#!/usr/bin/env python3
from __future__ import annotations

import argparse
from datetime import UTC, datetime, timedelta
import json
import os
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[2]
API_DIR = ROOT / 'services' / 'api'
DB_PATH = API_DIR / 'benefits_engine.db'

sys.path.insert(0, str(API_DIR))
os.environ.setdefault('DATABASE_URL', f'sqlite:///{DB_PATH}')

from sqlalchemy import select  # noqa: E402

from app.db.init_db import reset_db  # noqa: E402
from app.db.session import SessionLocal  # noqa: E402
from app.models import Opportunity, RecordStatus  # noqa: E402
from app.seeds.catalog import seed_all  # noqa: E402


SOFT_THRESHOLD_DAYS = 14
HARD_THRESHOLD_DAYS = 30
SOFT_THRESHOLD_RATIO = 0.10


def ensure_seeded_db(force: bool = False) -> None:
    if force:
        reset_db()
        with SessionLocal() as db:
            seed_all(db)
        return

    try:
        with SessionLocal() as db:
            count = db.execute(select(Opportunity.id)).first()
            if count is not None:
                return
    except Exception:
        pass

    reset_db()
    with SessionLocal() as db:
        seed_all(db)


def ensure_utc(value: datetime) -> datetime:
    if value.tzinfo is None:
        return value.replace(tzinfo=UTC)
    return value.astimezone(UTC)


def build_report(force_reseed: bool = False) -> dict:
    ensure_seeded_db(force=force_reseed)
    now = datetime.now(UTC)
    with SessionLocal() as db:
        published = db.execute(
            select(Opportunity).where(Opportunity.record_status == RecordStatus.PUBLISHED.value)
        ).scalars().all()

    total = len(published)
    if total == 0:
        return {
            'published_count': 0,
            'stale_over_14d': 0,
            'stale_over_30d': 0,
            'stale_ratio_over_14d': 0.0,
            'hard_threshold_breached': False,
            'soft_threshold_breached': False,
        }

    stale_14 = [
        item.slug
        for item in published
        if item.last_checked_at and ensure_utc(item.last_checked_at) < now - timedelta(days=SOFT_THRESHOLD_DAYS)
    ]
    stale_30 = [
        item.slug
        for item in published
        if item.last_checked_at and ensure_utc(item.last_checked_at) < now - timedelta(days=HARD_THRESHOLD_DAYS)
    ]
    ratio = len(stale_14) / total

    return {
        'published_count': total,
        'stale_over_14d': len(stale_14),
        'stale_over_30d': len(stale_30),
        'stale_ratio_over_14d': ratio,
        'stale_slugs_over_14d': stale_14,
        'stale_slugs_over_30d': stale_30,
        'hard_threshold_breached': len(stale_30) > 0,
        'soft_threshold_breached': ratio > SOFT_THRESHOLD_RATIO,
    }


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument('--format', choices=['text', 'json'], default='text')
    parser.add_argument('--reseed', action='store_true')
    args = parser.parse_args()

    report = build_report(force_reseed=args.reseed)
    failed = report['hard_threshold_breached'] or report['soft_threshold_breached']

    if args.format == 'json':
        print(json.dumps(report, indent=2))
    else:
        print('Data freshness report')
        print(f"published_count: {report['published_count']}")
        print(f"stale_over_14d: {report['stale_over_14d']}")
        print(f"stale_over_30d: {report['stale_over_30d']}")
        print(f"stale_ratio_over_14d: {report['stale_ratio_over_14d']:.2%}")
        if failed:
            print(json.dumps(report, indent=2))

    return 1 if failed else 0


if __name__ == '__main__':
    raise SystemExit(main())
