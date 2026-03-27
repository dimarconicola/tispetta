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
    assert {
        'recommended_step',
        'progress_summary',
        'modules',
        'journey',
        'personal_core_questions',
        'business_context',
        'business_core_questions',
        'strategic_modules',
        'results_summary',
    } <= set(question_payload)
    all_questions = [question for module in question_payload['modules'] for question in module['questions']]
    assert len(all_questions) >= 8
    assert {'module', 'sensitive', 'coverage_weight', 'ambiguity_reduction_score', 'priority', 'impact_counts'} <= set(all_questions[0])
    assert sum(1 for question in all_questions if question['required']) <= 8
    assert {
        'activity_stage',
        'legal_form_bucket',
        'main_operating_region',
        'company_age_or_formation_window',
        'size_band',
        'sector_macro_category',
        'innovation_regime_status',
    } <= {question['key'] for question in all_questions}
    assert question_payload['journey']['current_step'] == 'personal_core'
    assert question_payload['journey']['steps'][0]['key'] == 'personal_core'
    assert {question['key'] for question in question_payload['personal_core_questions']} >= {
        'main_operating_region',
        'employment_type',
        'persona_fisica_age_band',
        'family_composition',
        'figli_a_carico_count',
    }
    assert question_payload['business_context']['answered'] is False

    opportunities = client.get('/v1/opportunities')
    assert opportunities.status_code == 200
    opportunity_payload = opportunities.json()
    assert len(opportunity_payload) >= 35
    assert any(item['slug'] == 'smart_start_italia' for item in opportunity_payload)
    assert {'why_now', 'blocking_question_keys', 'match_reasons', 'blocking_missing_labels', 'opportunity_scope'} <= set(opportunity_payload[0])

    limited_opportunities = client.get('/v1/opportunities?limit=3')
    assert limited_opportunities.status_code == 200
    assert len(limited_opportunities.json()) == 3

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


def test_authenticated_catalog_surfaces_match_explanations() -> None:
    request = client.post('/v1/auth/request-magic-link', json={'email': 'demo@example.com'})
    assert request.status_code == 200
    token = parse_qs(urlparse(request.json()['preview_url']).query)['token'][0]
    exchange = client.post('/v1/auth/exchange-magic-link', json={'token': token})
    session_token = exchange.json()['session_token']
    headers = {'X-Session-Token': session_token}

    profile = client.put(
        '/v1/profile',
        headers=headers,
        json={
            'fact_values': {
                'profile_type': 'startup',
                'main_operating_region': 'Lombardia',
                'employment_type': 'dipendente',
                'persona_fisica_age_band': 'under_35',
                'family_composition': 'single',
                'figli_a_carico_count': '0',
                'activity_stage': 'incorporated_business',
                'legal_form_bucket': 'srl',
                'company_age_or_formation_window': '1-3y',
                'size_band': 'micro',
                'sector_macro_category': 'digitale',
                'innovation_regime_status': 'startup_innovativa',
            }
        },
    )
    assert profile.status_code == 200

    opportunities = client.get('/v1/opportunities', headers=headers)
    assert opportunities.status_code == 200
    payload = opportunities.json()
    assert len(payload) >= 10
    first = payload[0]
    assert isinstance(first['blocking_question_keys'], list)
    assert isinstance(first['match_reasons'], list)
    assert isinstance(first['blocking_missing_labels'], list)
    assert first['why_now']
    assert any(item['opportunity_scope'] == 'personal' for item in payload)
    assert any(item['opportunity_scope'] == 'business' for item in payload)

    personalized = client.get('/v1/opportunities?personalized_only=true', headers=headers)
    assert personalized.status_code == 200
    personalized_payload = personalized.json()
    assert personalized_payload
    assert len(personalized_payload) <= len(payload)
    assert all(item['match_status'] in {'confirmed', 'likely', 'unclear'} for item in personalized_payload)
    assert all(item['match_status'] != 'not_eligible' for item in personalized_payload)
    assert all(
        item['profile_edit_target'] is None or item['profile_edit_target']['step'] in {'personal_core', 'business_context', 'business_core', 'strategic_modules'}
        for item in personalized_payload
    )

    personal_only = client.get('/v1/opportunities?scope=personal', headers=headers)
    assert personal_only.status_code == 200
    assert all(item['opportunity_scope'] in {'personal', 'hybrid'} for item in personal_only.json())

    business_only = client.get('/v1/opportunities?scope=business', headers=headers)
    assert business_only.status_code == 200
    assert all(item['opportunity_scope'] in {'business', 'hybrid'} for item in business_only.json())

    detail = client.get(f"/v1/opportunities/{first['slug']}", headers=headers)
    assert detail.status_code == 200
    detail_payload = detail.json()
    assert detail_payload['match_breakdown']['status'] == first['match_status']
    assert isinstance(detail_payload['match_breakdown']['next_best_questions'], list)
    assert detail_payload['opportunity_scope'] in {'personal', 'business', 'hybrid'}

    overview = client.get('/v1/profile/overview', headers=headers)
    assert overview.status_code == 200
    overview_payload = overview.json()
    assert {'summary', 'personal', 'business'} <= set(overview_payload)
    assert overview_payload['personal']['title'] == 'Profilo personale'
    assert overview_payload['business']['title'] == 'Attivita'
    assert overview_payload['personal']['answered_fields']
    assert overview_payload['personal']['edit_target']['step'] == 'personal_core'
    assert overview_payload['business']['edit_target']['step'] in {'business_context', 'business_core'}
    assert overview_payload['summary']['total_match_count'] == len(personalized_payload)
    if overview_payload['summary']['clarifiable_match_count'] > 0:
        assert 'chiar' in overview_payload['summary']['readiness_label'].lower()


def test_onboarding_questions_clamp_requested_step_and_unlock_business_path() -> None:
    request = client.post('/v1/auth/request-magic-link', json={'email': 'wizard@example.com'})
    token = parse_qs(urlparse(request.json()['preview_url']).query)['token'][0]
    exchange = client.post('/v1/auth/exchange-magic-link', json={'token': token})
    headers = {'X-Session-Token': exchange.json()['session_token']}

    clamped = client.get('/v1/profile/questions?step=strategic_modules&module=hiring', headers=headers)
    assert clamped.status_code == 200
    assert clamped.json()['journey']['current_step'] == 'personal_core'

    update = client.put(
        '/v1/profile',
        headers=headers,
        json={
            'fact_values': {
                'main_operating_region': 'Lombardia',
                'employment_type': 'dipendente',
                'persona_fisica_age_band': 'under_35',
                'family_composition': 'single',
                'figli_a_carico_count': '0',
            }
        },
    )
    assert update.status_code == 200

    business_context = client.get('/v1/profile/questions?step=business_context', headers=headers)
    assert business_context.status_code == 200
    assert business_context.json()['journey']['current_step'] == 'business_context'

    enable_business = client.put(
        '/v1/profile',
        headers=headers,
        json={
            'business_exists': True,
            'fact_values': {
                'profile_type': 'startup',
            },
        },
    )
    assert enable_business.status_code == 200

    business_core = client.get('/v1/profile/questions?step=business_core', headers=headers)
    assert business_core.status_code == 200
    assert business_core.json()['journey']['current_step'] == 'business_core'


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
