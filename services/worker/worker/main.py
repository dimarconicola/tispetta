from __future__ import annotations

import logging
import time

from sqlalchemy import select

from app.db.session import SessionLocal
from app.models import SourceEndpoint
from worker.jobs.pipeline import ingest_source_endpoint

logging.basicConfig(level=logging.INFO, format='%(asctime)s %(levelname)s %(name)s %(message)s')
logger = logging.getLogger(__name__)


def run() -> None:
    logger.info('Worker service online. Polling seeded source endpoints for stub ingestion dispatch.')
    dispatched: set[str] = set()
    while True:
        with SessionLocal() as db:
            endpoint_ids = db.execute(select(SourceEndpoint.id)).scalars().all()
        for endpoint_id in endpoint_ids:
            if endpoint_id in dispatched:
                continue
            ingest_source_endpoint.fn(endpoint_id)
            dispatched.add(endpoint_id)
            logger.info('Dispatched ingestion actor for endpoint %s', endpoint_id)
        time.sleep(30)


if __name__ == '__main__':
    run()
