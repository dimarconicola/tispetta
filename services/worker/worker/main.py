from __future__ import annotations

import logging
import time

from sqlalchemy import select

from app.db.session import SessionLocal
from app.models import MeasureFamily, SourceEndpoint
from worker.jobs.pipeline import bootstrap_measure_family, ingest_source_endpoint

logging.basicConfig(level=logging.INFO, format='%(asctime)s %(levelname)s %(name)s %(message)s')
logger = logging.getLogger(__name__)


def run() -> None:
    logger.info('Worker service online. Polling curated source endpoints and measure families.')
    dispatched_endpoints: set[str] = set()
    dispatched_families: set[str] = set()
    while True:
        with SessionLocal() as db:
            endpoint_ids = db.execute(select(SourceEndpoint.id)).scalars().all()
            family_ids = db.execute(select(MeasureFamily.id)).scalars().all()
        for family_id in family_ids:
            if family_id in dispatched_families:
                continue
            bootstrap_measure_family.fn(family_id)
            dispatched_families.add(family_id)
            logger.info('Dispatched bootstrap actor for family %s', family_id)
        for endpoint_id in endpoint_ids:
            if endpoint_id in dispatched_endpoints:
                continue
            ingest_source_endpoint.fn(endpoint_id)
            dispatched_endpoints.add(endpoint_id)
            logger.info('Dispatched ingestion actor for endpoint %s', endpoint_id)
        time.sleep(30)


if __name__ == '__main__':
    run()
