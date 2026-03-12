from __future__ import annotations

from datetime import UTC, datetime
import logging

import dramatiq
from sqlalchemy import select

from app.db.session import SessionLocal
from app.models import IngestionRun, IngestionStage, Notification, NotificationEvent, NotificationStatus, SourceEndpoint
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
