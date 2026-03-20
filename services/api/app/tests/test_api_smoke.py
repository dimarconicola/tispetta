from fastapi.testclient import TestClient
from urllib.parse import parse_qs, urlparse

from app.db.init_db import reset_db
from app.db.session import SessionLocal
from app.main import app
from app.seeds.catalog import seed_all


client = TestClient(app)


def setup_module() -> None:
    reset_db()
    with SessionLocal() as db:
        seed_all(db)


def test_health_endpoint() -> None:
    response = client.get('/health')
    assert response.status_code == 200
    payload = response.json()
    assert payload['status'] == 'ok'
    assert payload['version']
    assert payload['updated_at']


def test_public_catalog_endpoints() -> None:
    questions = client.get('/v1/profile/questions')
    assert questions.status_code == 200
    question_payload = questions.json()
    assert {'recommended_step', 'progress_summary', 'modules'} <= set(question_payload)
    all_questions = [question for module in question_payload['modules'] for question in module['questions']]
    assert len(all_questions) >= 8
    assert {'module', 'sensitive', 'coverage_weight', 'ambiguity_reduction_score', 'priority', 'impact_counts'} <= set(all_questions[0])
    assert sum(1 for question in all_questions if question['required']) <= 8
    assert {
        'profile_type',
        'activity_stage',
        'legal_form_bucket',
        'main_operating_region',
        'company_age_or_formation_window',
        'size_band',
        'sector_macro_category',
        'innovation_regime_status',
    } <= {question['key'] for question in all_questions}

    opportunities = client.get('/v1/opportunities')
    assert opportunities.status_code == 200
    opportunity_payload = opportunities.json()
    assert len(opportunity_payload) >= 35
    assert any(item['slug'] == 'smart_start_italia' for item in opportunity_payload)
    assert {'why_now', 'blocking_question_keys', 'match_reasons', 'blocking_missing_labels'} <= set(opportunity_payload[0])

    detail = client.get('/v1/opportunities/smart_start_italia')
    assert detail.status_code == 200
    detail_payload = detail.json()
    assert detail_payload['issuer_name'] == 'Invitalia'
    assert {'status', 'matched_reasons', 'blocking_missing_facts', 'next_best_questions'} <= set(detail_payload['match_breakdown'])


def test_magic_link_exchange_creates_authenticated_session() -> None:
    request = client.post(
        '/v1/auth/request-magic-link',
        json={'email': 'demo@example.com', 'redirect_to': '/onboarding?entry=apex'},
    )
    assert request.status_code == 200
    preview_url = request.json()['preview_url']
    assert preview_url

    token = parse_qs(urlparse(preview_url).query)['token'][0]
    exchange = client.post('/v1/auth/exchange-magic-link', json={'token': token})
    assert exchange.status_code == 200
    assert exchange.json()['redirect_to'] == '/onboarding?entry=apex'

    session_token = exchange.json()['session_token']
    me = client.get('/v1/me', headers={'X-Session-Token': session_token})
    assert me.status_code == 200
    assert me.json()['email'] == 'demo@example.com'

    history = client.get('/v1/notifications/history', headers={'X-Session-Token': session_token})
    assert history.status_code == 200
    assert isinstance(history.json(), list)


def test_admin_bootstrap_endpoints() -> None:
    request = client.post('/v1/auth/request-magic-link', json={'email': 'admin@example.com'})
    assert request.status_code == 200
    preview_url = request.json()['preview_url']
    token = parse_qs(urlparse(preview_url).query)['token'][0]
    exchange = client.post('/v1/auth/exchange-magic-link', json={'token': token})
    assert exchange.status_code == 200
    session_token = exchange.json()['session_token']
    headers = {'X-Session-Token': session_token}

    families = client.get('/v1/admin/measure-families', headers=headers)
    assert families.status_code == 200
    assert len(families.json()) >= 18

    sources = client.get('/v1/admin/sources', headers=headers)
    assert sources.status_code == 200
    source_payload = sources.json()
    assert len(source_payload) >= 1

    trigger_run = client.post(f"/v1/admin/sources/{source_payload[0]['id']}/run", headers=headers)
    assert trigger_run.status_code == 200
    run_payload = trigger_run.json()

    run_detail = client.get(f"/v1/admin/ingestion-runs/{run_payload['id']}", headers=headers)
    assert run_detail.status_code == 200
    assert run_detail.json()['endpoint_url']

    documents = client.get('/v1/admin/documents', headers=headers)
    assert documents.status_code == 200
    assert len(documents.json()) >= 36
    first_document = documents.json()[0]

    review_document = client.post(
        f"/v1/admin/documents/{first_document['id']}/review",
        headers=headers,
        json={'document_role': first_document['document_role'], 'lifecycle_status': first_document['lifecycle_status']},
    )
    assert review_document.status_code == 200

    coverage = client.get('/v1/admin/survey/coverage', headers=headers)
    assert coverage.status_code == 200
    payload = coverage.json()
    assert payload['total_measure_families'] >= 18
    assert len(payload['rows']) >= 8

    integrity = client.get('/v1/admin/integrity', headers=headers)
    assert integrity.status_code == 200
    integrity_payload = integrity.json()
    assert integrity_payload['head_revision'] == '20260312_0001'
    assert isinstance(integrity_payload['checks'], list)

    notification_history = client.get('/v1/admin/notifications/history', headers=headers)
    assert notification_history.status_code == 200
    assert isinstance(notification_history.json(), list)

    bootstrap = client.post('/v1/admin/bootstrap/run', headers=headers)
    assert bootstrap.status_code == 200
    assert bootstrap.json()['coverage_rows'] >= 8
