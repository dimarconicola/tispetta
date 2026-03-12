from fastapi.testclient import TestClient

from app.db.init_db import init_db
from app.db.session import SessionLocal
from app.main import app
from app.seeds.catalog import seed_all


client = TestClient(app)


def setup_module() -> None:
    init_db()
    with SessionLocal() as db:
        seed_all(db)


def test_health_endpoint() -> None:
    response = client.get('/health')
    assert response.status_code == 200
    assert response.json() == {'status': 'ok'}


def test_public_catalog_endpoints() -> None:
    questions = client.get('/v1/profile/questions')
    assert questions.status_code == 200
    assert len(questions.json()) >= 4

    opportunities = client.get('/v1/opportunities')
    assert opportunities.status_code == 200
    assert len(opportunities.json()) >= 20
