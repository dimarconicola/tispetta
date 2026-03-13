from __future__ import annotations

from datetime import UTC, datetime
import logging

import dramatiq
from sqlalchemy import select

from app.db.session import SessionLocal
from app.models import IngestionRun, IngestionStage, MeasureFamily, NormalizedDocument, Notification, NotificationEvent, NotificationStatus, SourceEndpoint
from worker.services.bootstrap import (
    classify_document_role as classify_document_role_impl,
    extract_measure_requirements as extract_measure_requirements_impl,
    link_legal_basis as link_legal_basis_impl,
    refresh_family_bootstrap,
)
from worker.services.ingestion import extract_candidate, normalize_snapshot, route_candidate_for_review, upsert_snapshot

logger = logging.getLogger(__name__)


@dramatiq.actor
def ingest_source_endpoint(source_endpoint_id: str) -> None:
    with SessionLocal() as db:
        endpoint = db.execute(select(SourceEndpoint).where(SourceEndpoint.id == source_endpoint_id)).scalar_one_or_none()
        if endpoint is None:
            logger.warning('Source endpoint %s not found', source_endpoint_id)
            return
        run = IngestionRun(source_endpoint_id=source_endpoint_id, stage=IngestionStage.FETCH.value, status='started')
        db.add(run)
        db.commit()
        db.refresh(run)
        logger.info('Ingestion run created for %s', source_endpoint_id)
        try:
            snapshot = upsert_snapshot(db, endpoint, run)
            if snapshot is None:
                return
            document = normalize_snapshot(db, snapshot)
            run.stage = IngestionStage.EXTRACT.value
            db.commit()
            candidate = extract_candidate(endpoint, document)
            route_candidate_for_review(db, endpoint, candidate)
            run.stage = IngestionStage.COMPLETE.value
            run.status = 'success'
            run.finished_at = datetime.now(UTC)
            run.diagnostics = {
                'document_type': document.document_type,
                'confidence': candidate.confidence,
                'storage_path': snapshot.storage_path,
            }
            db.commit()
        except Exception as exc:  # pragma: no cover - defensive worker logging
            run.stage = IngestionStage.FAILED.value
            run.status = 'failed'
            run.finished_at = datetime.now(UTC)
            run.diagnostics = {'error': str(exc)}
            db.commit()
            logger.exception('Ingestion failed for endpoint %s', source_endpoint_id)


@dramatiq.actor
def recompute_profile_matches(user_id: str) -> None:
    logger.info('Requested profile recomputation for user %s', user_id)


@dramatiq.actor
def enqueue_notifications(event_id: str) -> None:
    with SessionLocal() as db:
        event = db.execute(select(NotificationEvent).where(NotificationEvent.id == event_id)).scalar_one_or_none()
        if event is None:
            return
        notification = Notification(
            notification_event_id=event.id,
            recipient=event.payload.get('email', 'unknown@example.com') if event.payload else 'unknown@example.com',
            subject=event.payload.get('subject', 'Aggiornamento opportunita') if event.payload else 'Aggiornamento opportunita',
            body=event.payload.get('body', '') if event.payload else '',
            status=NotificationStatus.PENDING.value,
        )
        db.add(notification)
        db.commit()
        logger.info('Notification enqueued for event %s', event_id)


@dramatiq.actor
def bootstrap_measure_family(measure_family_id: str) -> None:
    with SessionLocal() as db:
        family = db.execute(
            select(MeasureFamily).where(MeasureFamily.id == measure_family_id)
        ).scalar_one_or_none()
        if family is None:
            logger.warning('Measure family %s not found', measure_family_id)
            return
        result = refresh_family_bootstrap(db, family)
        logger.info('Bootstrap refresh completed for %s: %s', family.slug, result)


@dramatiq.actor
def crawl_curated_links(measure_family_id: str) -> None:
    bootstrap_measure_family.fn(measure_family_id)


@dramatiq.actor
def classify_document_role(normalized_document_id: str) -> None:
    with SessionLocal() as db:
        document = db.get(NormalizedDocument, normalized_document_id)
        if document is None:
            return
        document.document_role = classify_document_role_impl(document.canonical_url or '', document.title, document.clean_text)
        db.commit()


@dramatiq.actor
def extract_measure_requirements(measure_family_id: str) -> None:
    with SessionLocal() as db:
        family = db.execute(select(MeasureFamily).where(MeasureFamily.id == measure_family_id)).scalar_one_or_none()
        if family is None:
            return
        extract_measure_requirements_impl(db, family)
        logger.info('Requirements refreshed for family %s', family.slug)


@dramatiq.actor
def link_legal_basis(measure_family_id: str) -> None:
    with SessionLocal() as db:
        family = db.execute(select(MeasureFamily).where(MeasureFamily.id == measure_family_id)).scalar_one_or_none()
        if family is None:
            return
        count = link_legal_basis_impl(db, family)
        logger.info('Linked %s legal basis docs for %s', count, family.slug)


@dramatiq.actor
def recompute_survey_weights(_: str = 'latest') -> None:
    with SessionLocal() as db:
        from app.services.corpus import recompute_survey_coverage

        payload = recompute_survey_coverage(db)
        logger.info('Survey coverage recomputed with %s rows', len(payload.get('rows', [])))
