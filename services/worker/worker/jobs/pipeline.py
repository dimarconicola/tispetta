from __future__ import annotations

from datetime import UTC, datetime
import logging

import dramatiq
from sqlalchemy import select

from app.db.session import SessionLocal
from app.matching.service import evaluate_profile_against_catalog
from app.models import (
    IngestionRun,
    IngestionStage,
    MeasureFamily,
    NormalizedDocument,
    NotificationEvent,
    Profile,
    SourceEndpoint,
)
from app.services.notifications import deliver_notification_event, run_deadline_reminders, run_weekly_digest
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
            review_item = route_candidate_for_review(db, endpoint, document, candidate)
            run.stage = IngestionStage.COMPLETE.value
            run.status = 'success'
            run.finished_at = datetime.now(UTC)
            run.diagnostics = {
                'document_type': document.document_type,
                'confidence': candidate.confidence,
                'storage_path': snapshot.storage_path,
                'snapshot_id': snapshot.id,
                'normalized_document_id': document.id,
                'review_item_id': review_item.id if review_item is not None else None,
                'candidate_title': candidate.title,
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
    with SessionLocal() as db:
        profile = db.execute(select(Profile).where(Profile.user_id == user_id)).scalar_one_or_none()
        if profile is None:
            logger.warning('Profile not found for user %s', user_id)
            return
        results = evaluate_profile_against_catalog(db, profile)
        logger.info('Recomputed %s matches for user %s', len(results), user_id)


@dramatiq.actor
def enqueue_notifications(event_id: str) -> None:
    with SessionLocal() as db:
        event = db.execute(select(NotificationEvent).where(NotificationEvent.id == event_id)).scalar_one_or_none()
        if event is None:
            return
        delivered = deliver_notification_event(db, event.id)
        logger.info('Notification dispatch for event %s delivered=%s', event_id, delivered)


@dramatiq.actor
def send_deadline_reminders(_: str = 'run') -> None:
    """Send deadline alerts for confirmed/likely matches expiring within 30 days."""
    with SessionLocal() as db:
        dispatched = run_deadline_reminders(db)
        logger.info('Deadline reminder job complete: %d emails sent', dispatched)


@dramatiq.actor
def send_weekly_digest(_: str = 'run') -> None:
    """Send weekly top-matches digest to users with weekly_profile_nudges enabled."""
    with SessionLocal() as db:
        dispatched = run_weekly_digest(db)
        logger.info('Weekly digest job complete: %d emails sent', dispatched)


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
