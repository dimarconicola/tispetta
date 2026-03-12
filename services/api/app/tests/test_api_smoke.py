from fastapi.testclient import TestClient
from urllib.parse import parse_qs, urlparse

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


def test_magic_link_exchange_creates_authenticated_session() -> None:
    request = client.post('/v1/auth/request-magic-link', json={'email': 'demo@example.com'})
    assert request.status_code == 200
    preview_url = request.json()['preview_url']
    assert preview_url

    token = parse_qs(urlparse(preview_url).query)['token'][0]
    exchange = client.post('/v1/auth/exchange-magic-link', json={'token': token})
    assert exchange.status_code == 200

    session_token = exchange.json()['session_token']
    me = client.get('/v1/me', headers={'X-Session-Token': session_token})
    assert me.status_code == 200
    assert me.json()['email'] == 'demo@example.com'
