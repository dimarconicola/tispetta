#!/usr/bin/env python3
from __future__ import annotations

import os
from pathlib import Path
import sys

import uvicorn

ROOT = Path(__file__).resolve().parents[2]
API_DIR = ROOT / 'services' / 'api'
DB_PATH = API_DIR / 'benefits_engine.db'

sys.path.insert(0, str(API_DIR))

os.environ.setdefault('DATABASE_URL', f'sqlite:///{DB_PATH}')
os.environ.setdefault('APP_BASE_URL', os.environ.get('PLAYWRIGHT_APP_BASE_URL', 'http://localhost:3100'))
os.environ.setdefault('CORS_ALLOWED_ORIGINS', os.environ.get('PLAYWRIGHT_APP_BASE_URL', 'http://localhost:3100'))
os.environ.setdefault('ENVIRONMENT', 'development')
os.environ.setdefault('SESSION_COOKIE_SECURE', 'false')

from app.db.init_db import reset_db  # noqa: E402
from app.db.session import SessionLocal  # noqa: E402
from app.seeds.catalog import seed_all  # noqa: E402


def main() -> None:
    reset_db()
    with SessionLocal() as db:
        seed_all(db)
    uvicorn.run(
        'app.main:app',
        host='0.0.0.0',
        port=int(os.environ.get('PLAYWRIGHT_API_PORT', '8100')),
        reload=False,
        log_level='warning',
    )


if __name__ == '__main__':
    main()
