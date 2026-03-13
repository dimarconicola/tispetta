from __future__ import annotations

import argparse
import json

from sqlalchemy import select

from app.db.init_db import init_db
from app.db.session import SessionLocal
from app.services.corpus import ensure_bootstrap_corpus
from app.services.family_opportunities import sync_measure_family_opportunities
from app.models import MeasureFamily
from worker.services.bootstrap import refresh_family_bootstrap


def main() -> None:
    parser = argparse.ArgumentParser(description='Run curated live bootstrap for measure families.')
    parser.add_argument('--slug', action='append', dest='slugs', help='Measure family slug to bootstrap. Can be repeated.')
    args = parser.parse_args()

    init_db()
    with SessionLocal() as db:
        ensure_bootstrap_corpus(db)
        stmt = select(MeasureFamily).order_by(MeasureFamily.title.asc())
        if args.slugs:
            stmt = stmt.where(MeasureFamily.slug.in_(args.slugs))
        families = db.execute(stmt).scalars().all()
        results = [refresh_family_bootstrap(db, family) for family in families]
        sync = sync_measure_family_opportunities(db)
        print(json.dumps({'results': results, 'opportunity_sync': sync}, ensure_ascii=False, default=str, indent=2))


if __name__ == '__main__':
    main()
