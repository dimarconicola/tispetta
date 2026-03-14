from __future__ import annotations

from datetime import UTC, datetime
import logging
import time

from sqlalchemy import select

from app.db.session import SessionLocal
from app.models import MeasureFamily, SourceEndpoint
from worker.config import settings
from worker.jobs.pipeline import bootstrap_measure_family, ingest_source_endpoint, recompute_survey_weights

logging.basicConfig(level=logging.INFO, format='%(asctime)s %(levelname)s %(name)s %(message)s')
logger = logging.getLogger(__name__)


def _is_due(last_run: datetime | None, now: datetime, interval_seconds: int) -> bool:
    return last_run is None or (now - last_run).total_seconds() >= interval_seconds


def _prune_last_runs(last_runs: dict[str, datetime], active_ids: list[str]) -> dict[str, datetime]:
    active = set(active_ids)
    return {item_id: timestamp for item_id, timestamp in last_runs.items() if item_id in active}


def _dispatch_next_family(family_ids: list[str], last_runs: dict[str, datetime], now: datetime) -> bool:
    for family_id in family_ids:
        if not _is_due(last_runs.get(family_id), now, settings.worker_family_refresh_interval_seconds):
            continue
        bootstrap_measure_family.fn(family_id)
        last_runs[family_id] = now
        logger.info('Refreshed measure family bootstrap for %s', family_id)
        return True
    return False


def _dispatch_next_endpoint(endpoint_ids: list[str], last_runs: dict[str, datetime], now: datetime) -> bool:
    for endpoint_id in endpoint_ids:
        if not _is_due(last_runs.get(endpoint_id), now, settings.worker_endpoint_refresh_interval_seconds):
            continue
        ingest_source_endpoint.fn(endpoint_id)
        last_runs[endpoint_id] = now
        logger.info('Refreshed source endpoint ingestion for %s', endpoint_id)
        return True
    return False


def run() -> None:
    logger.info('Worker service online. Scheduling recurring refresh for curated sources and measure families.')
    endpoint_last_run: dict[str, datetime] = {}
    family_last_run: dict[str, datetime] = {}
    survey_last_run: datetime | None = None
    while True:
        now = datetime.now(UTC)
        with SessionLocal() as db:
            endpoint_ids = db.execute(select(SourceEndpoint.id)).scalars().all()
            family_ids = db.execute(select(MeasureFamily.id)).scalars().all()

        family_last_run = _prune_last_runs(family_last_run, family_ids)
        endpoint_last_run = _prune_last_runs(endpoint_last_run, endpoint_ids)

        dispatched = False
        if _dispatch_next_family(family_ids, family_last_run, now):
            dispatched = True
        if _dispatch_next_endpoint(endpoint_ids, endpoint_last_run, now):
            dispatched = True
        if _is_due(survey_last_run, now, settings.worker_survey_refresh_interval_seconds):
            recompute_survey_weights.fn('latest')
            survey_last_run = now
            dispatched = True
            logger.info('Recomputed survey coverage snapshot')

        if not dispatched:
            logger.debug('No recurring worker tasks due in this cycle')

        time.sleep(settings.worker_poll_interval_seconds)


if __name__ == '__main__':
    run()
