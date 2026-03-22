#!/usr/bin/env python3
from __future__ import annotations

import argparse
from collections import Counter
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
from app.models import Opportunity, RecordStatus, User  # noqa: E402
from app.seeds.catalog import seed_all  # noqa: E402
from app.services.opportunities import list_opportunities  # noqa: E402


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


def build_report(force_reseed: bool = False) -> dict:
    ensure_seeded_db(force=force_reseed)
    with SessionLocal() as db:
        published = db.execute(
            select(Opportunity).where(Opportunity.record_status == RecordStatus.PUBLISHED.value)
        ).scalars().all()

        slug_counts = Counter(item.slug for item in published)
        duplicate_slugs = sorted(slug for slug, count in slug_counts.items() if count > 1)

        missing_required_fields: list[dict] = []
        missing_official_links: list[str] = []
        missing_current_version: list[str] = []

        for opportunity in published:
            current_version = opportunity.current_version
            if current_version is None:
                missing_current_version.append(opportunity.slug)
                continue

            required_pairs = {
                'title': opportunity.title,
                'slug': opportunity.slug,
                'category': opportunity.category,
                'last_checked_at': opportunity.last_checked_at,
            }
            missing_fields = sorted(key for key, value in required_pairs.items() if value in (None, '', []))
            if missing_fields:
                missing_required_fields.append({'slug': opportunity.slug, 'fields': missing_fields})

            if not current_version.official_links:
                missing_official_links.append(opportunity.slug)

        demo_user = db.execute(select(User).where(User.email == 'demo@example.com')).scalar_one_or_none()
        explanation_failures: list[str] = []
        if demo_user is not None:
            cards = list_opportunities(db, demo_user)
            for item in cards[:15]:
                if not all(key in item for key in ('why_now', 'blocking_question_keys', 'match_reasons', 'blocking_missing_labels')):
                    explanation_failures.append(item.get('slug', '<unknown>'))

        return {
            'published_count': len(published),
            'duplicate_slugs': duplicate_slugs,
            'missing_current_version': missing_current_version,
            'missing_required_fields': missing_required_fields,
            'missing_official_links': missing_official_links,
            'explanation_failures': explanation_failures,
        }


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument('--format', choices=['text', 'json'], default='text')
    parser.add_argument('--reseed', action='store_true')
    args = parser.parse_args()

    report = build_report(force_reseed=args.reseed)
    failures = (
        len(report['duplicate_slugs'])
        + len(report['missing_current_version'])
        + len(report['missing_required_fields'])
        + len(report['missing_official_links'])
        + len(report['explanation_failures'])
    )

    if args.format == 'json':
        print(json.dumps(report, indent=2))
    else:
        print('Data integrity report')
        print(f"published_count: {report['published_count']}")
        print(f"duplicate_slugs: {len(report['duplicate_slugs'])}")
        print(f"missing_current_version: {len(report['missing_current_version'])}")
        print(f"missing_required_fields: {len(report['missing_required_fields'])}")
        print(f"missing_official_links: {len(report['missing_official_links'])}")
        print(f"explanation_failures: {len(report['explanation_failures'])}")
        if failures:
            print(json.dumps(report, indent=2))

    return 1 if failures else 0


if __name__ == '__main__':
    raise SystemExit(main())
