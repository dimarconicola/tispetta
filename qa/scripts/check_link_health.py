#!/usr/bin/env python3
from __future__ import annotations

import argparse
from collections import OrderedDict
from concurrent.futures import ThreadPoolExecutor
import json
import os
from pathlib import Path
import sys

import httpx
from sqlalchemy import select
from sqlalchemy.orm import selectinload

ROOT = Path(__file__).resolve().parents[2]
API_DIR = ROOT / 'services' / 'api'
DB_PATH = API_DIR / 'benefits_engine.db'

sys.path.insert(0, str(API_DIR))
os.environ.setdefault('DATABASE_URL', f'sqlite:///{DB_PATH}')

from app.db.session import SessionLocal  # noqa: E402
from app.models import Opportunity, RecordStatus  # noqa: E402
from app.db.init_db import reset_db  # noqa: E402
from app.seeds.catalog import seed_all  # noqa: E402


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


def collect_links(sample_size: int, force_reseed: bool = False) -> list[str]:
    ensure_seeded_db(force=force_reseed)
    with SessionLocal() as db:
        published = db.execute(
            select(Opportunity)
            .options(selectinload(Opportunity.current_version))
            .where(Opportunity.record_status == RecordStatus.PUBLISHED.value)
            .order_by(Opportunity.updated_at.desc())
        ).scalars().all()

    seen: OrderedDict[str, None] = OrderedDict()
    for opportunity in published:
        current_version = opportunity.current_version
        if current_version is None:
            continue
        for link in current_version.official_links:
            seen.setdefault(link, None)
            if len(seen) >= sample_size:
                return list(seen.keys())
    return list(seen.keys())


def probe_link(url: str) -> tuple[int | None, str | None]:
    try:
        response = httpx.get(
            url,
            follow_redirects=True,
            timeout=6.0,
            headers={'User-Agent': 'tispetta-link-health/1.0'},
        )
        return response.status_code, None
    except httpx.HTTPError as exc:
        return None, str(exc)


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument('--sample-size', type=int, default=25)
    parser.add_argument('--format', choices=['text', 'json'], default='text')
    parser.add_argument('--reseed', action='store_true')
    args = parser.parse_args()

    links = collect_links(args.sample_size, force_reseed=args.reseed)
    with ThreadPoolExecutor(max_workers=min(8, max(1, len(links)))) as executor:
        probes = list(executor.map(probe_link, links))
    results = [
        {'url': link, 'status_code': status, 'error': error}
        for link, (status, error) in zip(links, probes, strict=True)
    ]

    successful = sum(1 for item in results if item['status_code'] and 200 <= item['status_code'] < 400)
    success_rate = successful / len(results) if results else 1.0
    report = {
        'checked_links': len(results),
        'successful_links': successful,
        'success_rate': success_rate,
        'failures': [item for item in results if not item['status_code'] or item['status_code'] >= 400],
    }

    if args.format == 'json':
        print(json.dumps(report, indent=2))
    else:
        print('Link health report')
        print(f"checked_links: {report['checked_links']}")
        print(f"successful_links: {report['successful_links']}")
        print(f"success_rate: {report['success_rate']:.2%}")
        if report['failures']:
            print(json.dumps(report['failures'], indent=2))

    return 1 if success_rate < 0.95 else 0


if __name__ == '__main__':
    raise SystemExit(main())
