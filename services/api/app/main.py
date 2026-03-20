from contextlib import asynccontextmanager
from datetime import UTC, datetime

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.api.router import api_router
from app.core.config import get_settings
from app.db.init_db import init_db
from app.db.session import SessionLocal
from app.seeds.catalog import seed_all

settings = get_settings()
STARTED_AT = datetime.now(UTC)


@asynccontextmanager
async def lifespan(_: FastAPI):
    if settings.auto_create_schema:
        init_db()
    if settings.auto_seed_on_startup:
        with SessionLocal() as db:
            seed_all(db)
    yield


app = FastAPI(
    title='Benefits Opportunity Engine API',
    version='0.1.0',
    lifespan=lifespan,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins(),
    allow_credentials=True,
    allow_methods=['*'],
    allow_headers=['*'],
)


@app.get('/health')
def health() -> dict[str, str | None]:
    return {
        'status': 'ok',
        'version': settings.version_label(),
        'updated_at': settings.build_updated_at or STARTED_AT.isoformat(),
        'deployment_id': settings.deployment_label(),
    }


app.include_router(api_router)
