from __future__ import annotations

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models import NotificationPreference, Profile, ProfileFactCatalog, ProfileFactValue, ProfileRevision, User
from app.schemas.profile import ProfilePayload
from app.services.corpus import CORE_FACT_KEYS, build_profile_questions, ensure_bootstrap_corpus

KNOWN_PROFILE_FIELDS = {
    'user_type',
    'region',
    'province',
    'age_range',
    'business_exists',
    'legal_entity_type',
    'company_age_band',
    'company_size_band',
    'revenue_band',
    'sector_code_or_category',
    'founder_attributes',
    'hiring_intent',
    'innovation_intent',
    'sustainability_intent',
    'export_intent',
    'incorporation_status',
    'startup_stage',
    'goals',
}

LEGACY_TO_FACT = {
    'user_type': 'profile_type',
    'region': 'main_operating_region',
    'legal_entity_type': 'legal_form_bucket',
    'company_age_band': 'company_age_or_formation_window',
    'company_size_band': 'size_band',
    'sector_code_or_category': 'sector_macro_category',
    'hiring_intent': 'hiring_interest',
    'export_intent': 'export_investment_intent',
}


def compute_profile_completeness(payload: dict) -> float:
    fact_values = payload.get('fact_values') or {}
    answered_core = sum(1 for key in CORE_FACT_KEYS if fact_values.get(key) not in (None, '', []))
    non_core_answered = sum(
        1
        for key, value in fact_values.items()
        if key not in CORE_FACT_KEYS and value not in (None, '', [])
    )
    if answered_core == 0:
        legacy_core = [
            payload.get('user_type'),
            payload.get('region'),
            payload.get('legal_entity_type'),
            payload.get('company_age_band'),
            payload.get('company_size_band'),
            payload.get('sector_code_or_category'),
        ]
        answered_core = len([value for value in legacy_core if value not in (None, '', [])])
    core_score = (answered_core / len(CORE_FACT_KEYS)) * 80 if CORE_FACT_KEYS else 0
    additional_score = min(non_core_answered * 2.5, 20)
    return round(min(core_score + additional_score, 100.0), 1)


def serialize_profile(profile: Profile) -> dict:
    return {
        'user_type': profile.user_type,
        'region': profile.region,
        'province': profile.province,
        'age_range': profile.age_range,
        'business_exists': profile.business_exists,
        'legal_entity_type': profile.legal_entity_type,
        'company_age_band': profile.company_age_band,
        'company_size_band': profile.company_size_band,
        'revenue_band': profile.revenue_band,
        'sector_code_or_category': profile.sector_code_or_category,
        'founder_attributes': profile.founder_attributes,
        'hiring_intent': profile.hiring_intent,
        'innovation_intent': profile.innovation_intent,
        'sustainability_intent': profile.sustainability_intent,
        'export_intent': profile.export_intent,
        'incorporation_status': profile.incorporation_status,
        'startup_stage': profile.startup_stage,
        'goals': profile.goals,
        'fact_values': get_profile_fact_values_for_profile_placeholder(profile),
        'profile_completeness_score': profile.profile_completeness_score,
    }


def get_profile_fact_values_for_profile_placeholder(profile: Profile) -> dict:
    return {
        item.fact.key: item.value_json.get('value')
        for item in profile.fact_values
        if item.fact is not None
    }


def profile_to_response(profile: Profile) -> dict:
    payload = serialize_profile(profile)
    return {
        'id': profile.id,
        'user_id': profile.user_id,
        'country': profile.country,
        'updated_at': profile.updated_at,
        **payload,
    }


def get_or_create_profile(db: Session, user: User) -> Profile:
    ensure_bootstrap_corpus(db)
    if user.profile is not None:
        return user.profile
    profile = Profile(user_id=user.id, country='IT', profile_completeness_score=0.0)
    db.add(profile)
    db.flush()
    if user.notification_preferences is None:
        db.add(NotificationPreference(user_id=user.id))
    return profile


def get_profile_questions(db: Session, user: User | None = None) -> list[dict]:
    ensure_bootstrap_corpus(db)
    profile = user.profile if user is not None and user.profile is not None else None
    return build_profile_questions(db, profile)


def update_profile(db: Session, user: User, payload: ProfilePayload) -> Profile:
    profile = get_or_create_profile(db, user)
    incoming = payload.model_dump(exclude_unset=True)
    fact_values = normalize_incoming_fact_values(incoming)
    for key, value in incoming.items():
        if key in KNOWN_PROFILE_FIELDS:
            setattr(profile, key, value)
    apply_fact_values_to_profile(db, profile, fact_values)
    materialize_legacy_fields_from_facts(profile, fact_values)
    serialized = serialize_profile(profile)
    profile.profile_completeness_score = compute_profile_completeness(serialized)
    revision_number = len(profile.revisions) + 1
    db.add(
        ProfileRevision(
            profile_id=profile.id,
            revision_number=revision_number,
            payload=serialized,
        )
    )
    db.commit()
    db.refresh(profile)
    return profile


def normalize_incoming_fact_values(incoming: dict) -> dict:
    values = dict(incoming.get('fact_values') or {})
    for legacy_key, fact_key in LEGACY_TO_FACT.items():
        if legacy_key in incoming and incoming.get(legacy_key) not in (None, ''):
            values[fact_key] = incoming[legacy_key]

    activity_stage = values.get('activity_stage')
    if activity_stage is None:
        business_exists = incoming.get('business_exists')
        incorporation_status = incoming.get('incorporation_status')
        legal_form = incoming.get('legal_entity_type')
        if business_exists is False:
            activity_stage = 'not_started'
        elif incorporation_status == 'partita_iva_only' or legal_form == 'individual_professional':
            activity_stage = 'partita_iva_only'
        elif business_exists is True:
            activity_stage = 'incorporated_business'
    if activity_stage is not None:
        values['activity_stage'] = activity_stage

    if 'innovation_intent' in incoming and incoming.get('innovation_intent') is True:
        values.setdefault('digital_transition_project', True)
    if 'sustainability_intent' in incoming and incoming.get('sustainability_intent') is True:
        values.setdefault('energy_transition_project', True)
    return values


def apply_fact_values_to_profile(db: Session, profile: Profile, fact_values: dict) -> None:
    if not fact_values:
        return
    catalog = {
        fact.key: fact
        for fact in db.execute(select(ProfileFactCatalog)).scalars().all()
    }
    existing = {
        item.fact.key: item
        for item in profile.fact_values
        if item.fact is not None
    }
    for key, value in fact_values.items():
        fact = catalog.get(key)
        if fact is None:
            continue
        record = existing.get(key)
        if record is None:
            db.add(ProfileFactValue(profile_id=profile.id, fact_catalog_id=fact.id, value_json={'value': value}))
        else:
            record.value_json = {'value': value}


def materialize_legacy_fields_from_facts(profile: Profile, fact_values: dict) -> None:
    if 'profile_type' in fact_values:
        profile.user_type = fact_values['profile_type']
    if 'main_operating_region' in fact_values:
        profile.region = fact_values['main_operating_region']
    if 'legal_form_bucket' in fact_values:
        profile.legal_entity_type = fact_values['legal_form_bucket']
    if 'company_age_or_formation_window' in fact_values:
        profile.company_age_band = fact_values['company_age_or_formation_window']
    if 'size_band' in fact_values:
        profile.company_size_band = fact_values['size_band']
    if 'sector_macro_category' in fact_values:
        profile.sector_code_or_category = fact_values['sector_macro_category']
    if 'hiring_interest' in fact_values:
        profile.hiring_intent = parse_boolish(fact_values['hiring_interest'])
    if 'export_investment_intent' in fact_values:
        profile.export_intent = parse_boolish(fact_values['export_investment_intent'])
    if 'digital_transition_project' in fact_values:
        profile.innovation_intent = parse_boolish(fact_values['digital_transition_project'])
    if 'energy_transition_project' in fact_values:
        profile.sustainability_intent = parse_boolish(fact_values['energy_transition_project'])

    activity_stage = fact_values.get('activity_stage')
    if activity_stage == 'not_started':
        profile.business_exists = False
        profile.incorporation_status = 'not_started'
    elif activity_stage == 'partita_iva_only':
        profile.business_exists = True
        profile.incorporation_status = 'partita_iva_only'
    elif activity_stage == 'incorporated_business':
        profile.business_exists = True
        profile.incorporation_status = 'incorporated_business'

    innovation_regime_status = fact_values.get('innovation_regime_status')
    founder_attributes = dict(profile.founder_attributes or {})
    if innovation_regime_status is not None:
        founder_attributes['innovation_regime_status'] = innovation_regime_status
    for gated_key in [
        'women_led_majority',
        'founder_age_band',
        'unemployment_status_at_start',
        'no_prior_permanent_employment',
        'target_hire_age_band',
        'target_hire_gender_priority',
        'target_hire_disadvantaged_status',
        'target_market_scope',
        'energy_reduction_goal',
        'filed_balance_sheets_count',
        'patent_ip_intent',
    ]:
        if gated_key in fact_values:
            founder_attributes[gated_key] = fact_values[gated_key]
    profile.founder_attributes = founder_attributes or None

    goals: list[str] = []
    if profile.hiring_intent:
        goals.append('hiring')
    if profile.export_intent:
        goals.append('export')
    if profile.innovation_intent:
        goals.append('innovazione')
    if profile.sustainability_intent:
        goals.append('sostenibilita')
    if goals:
        profile.goals = sorted(set(goals))


def parse_boolish(value) -> bool | None:
    if value in (None, ''):
        return None
    if isinstance(value, bool):
        return value
    if isinstance(value, str):
        return value.lower() == 'true'
    return bool(value)
