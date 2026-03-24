from __future__ import annotations

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models import Match, MatchStatus, NotificationPreference, Profile, ProfileFactCatalog, ProfileFactValue, ProfileRevision, User
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

MODULE_META = {
    'core_entity': {
        'title': 'Base profile',
        'description': 'Le domande stabili che definiscono il perimetro iniziale del profilo.',
    },
    'strategic_intent': {
        'title': 'Strategic intent',
        'description': 'Le intenzioni progettuali che migliorano ranking, coverage e rilevanza.',
    },
    'conditional_accuracy': {
        'title': 'Conditional accuracy',
        'description': 'Domande che appaiono solo quando chiariscono davvero opportunita vive.',
    },
}

PERSONAL_CORE_KEYS = [
    'main_operating_region',
    'employment_type',
    'persona_fisica_age_band',
    'family_composition',
    'figli_a_carico_count',
    'isee_bracket',
]

BUSINESS_CORE_KEYS = [
    'activity_stage',
    'legal_form_bucket',
    'company_age_or_formation_window',
    'size_band',
    'sector_macro_category',
    'innovation_regime_status',
]

STEP_LABELS = {
    'personal_core': 'Profilo personale',
    'business_context': 'Attivita',
    'business_core': 'Dati attivita',
    'results_checkpoint': 'Prime misure',
    'strategic_modules': 'Approfondimenti',
    'final_next_actions': 'Passaggio completato',
}

STRATEGIC_MODULE_META = {
    'hiring': {
        'title': 'Assunzioni',
        'description': 'Risposte utili solo se stai valutando incentivi per nuove assunzioni.',
        'why': 'Puoi chiarire incentivi occupazionali e bonus legati al profilo del lavoratore target.',
    },
    'export': {
        'title': 'Export',
        'description': 'Apri solo le domande che contano se stai lavorando su mercati esteri o fiere.',
        'why': 'Serve a capire se le misure SIMEST e le linee export sono davvero pertinenti.',
    },
    'digital_energy': {
        'title': 'Investimenti',
        'description': 'Qui rientrano transizione digitale, energia, brevetti e investimenti progettuali.',
        'why': 'Sblocca chiarezza su Transizione 4.0 / 5.0 e altre misure progettuali.',
    },
    'personal_family': {
        'title': 'Benefici personali',
        'description': 'Affina le misure personali, familiari e fiscali quando serve davvero.',
        'why': 'Puoi chiarire importi e condizioni di bonus personali e familiari.',
    },
    'general': {
        'title': 'Dettagli finali',
        'description': 'Ultime informazioni utili per togliere ambiguita residue.',
        'why': 'Serve a chiudere gli ultimi dubbi sui match che restano aperti.',
    },
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


def get_profile_questions(db: Session, user: User | None = None, requested_step: str | None = None, requested_module: str | None = None) -> dict:
    ensure_bootstrap_corpus(db)
    profile = user.profile if user is not None and user.profile is not None else None
    fact_values = dict((profile_to_response(profile)['fact_values'] if profile is not None else {}) or {})
    grouped_modules, question_map = build_grouped_questions(db, profile)
    personal_core_questions = build_fixed_question_set(db, profile, question_map, PERSONAL_CORE_KEYS)
    business_core_questions = build_fixed_question_set(db, profile, question_map, BUSINESS_CORE_KEYS)
    strategic_modules = build_strategic_modules(grouped_modules, fact_values)
    business_context = build_business_context(profile, fact_values)
    progress_summary = build_progress_summary(
        grouped_modules,
        fact_values,
        profile,
        personal_core_questions=personal_core_questions,
        business_core_questions=business_core_questions,
        strategic_modules=strategic_modules,
        business_context=business_context,
    )
    results_summary = build_results_summary(
        db,
        user,
        grouped_modules=grouped_modules,
        progress_summary=progress_summary,
        strategic_modules=strategic_modules,
        business_context=business_context,
    )
    journey = build_onboarding_journey(
        fact_values=fact_values,
        personal_core_questions=personal_core_questions,
        business_core_questions=business_core_questions,
        strategic_modules=strategic_modules,
        business_context=business_context,
        requested_step=requested_step,
        requested_module=requested_module,
    )
    return {
        'recommended_step': journey['current_step'],
        'progress_summary': progress_summary,
        'modules': grouped_modules,
        'journey': journey,
        'personal_core_questions': personal_core_questions,
        'business_context': business_context,
        'business_core_questions': business_core_questions,
        'strategic_modules': strategic_modules,
        'results_summary': results_summary,
    }


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


def build_grouped_questions(db: Session, profile: Profile | None) -> tuple[list[dict], dict[str, dict]]:
    questions = [question for question in build_profile_questions(db, profile) if question['key'] != 'profile_type']
    question_keys = {question['key'] for question in questions}
    fact_values = dict((profile_to_response(profile)['fact_values'] if profile is not None else {}) or {})
    impacts = compute_question_impacts(db, profile, question_keys)

    modules = {'core_entity': [], 'strategic_intent': [], 'conditional_accuracy': []}
    for question in questions:
        question_impact = impacts.get(
            question['key'],
            {
                'clarification_opportunity_count': 0,
                'blocking_opportunity_count': 0,
                'upgrade_opportunity_count': 0,
            },
        )
        enriched = {
            **question,
            'impact_counts': question_impact,
            'blocking_opportunity_count': question_impact['blocking_opportunity_count'],
            'upgrade_opportunity_count': question_impact['upgrade_opportunity_count'],
        }
        unanswered = fact_values.get(question['key']) in (None, '', [])
        enriched['priority'] = compute_question_priority(enriched, unanswered=unanswered)
        modules.setdefault(question['module'] or 'core_entity', []).append(enriched)

    grouped_modules = []
    for module_key in ('core_entity', 'strategic_intent', 'conditional_accuracy'):
        module_questions = sorted(
            modules.get(module_key, []),
            key=lambda item: (
                0 if item.get('required') else 1,
                -(item.get('priority') or 0),
                -(item.get('ambiguity_reduction_score') or 0),
                item.get('sensitive', False),
                item.get('step', 0),
            ),
        )
        grouped_modules.append(
            {
                'key': module_key,
                'title': MODULE_META[module_key]['title'],
                'description': MODULE_META[module_key]['description'],
                'questions': module_questions,
            }
        )

    question_map: dict[str, dict] = {}
    for module in grouped_modules:
        for question in module['questions']:
            question_map[question['key']] = question
    return grouped_modules, question_map


def build_fixed_question_set(db: Session, profile: Profile | None, question_map: dict[str, dict], keys: list[str]) -> list[dict]:
    impacts = compute_question_impacts(db, profile, set(keys))
    facts = {
        fact.key: fact
        for fact in db.execute(select(ProfileFactCatalog).where(ProfileFactCatalog.key.in_(keys))).scalars().all()
    }
    items: list[dict] = []
    for key in keys:
        question = question_map.get(key)
        if question is None:
            fact = facts.get(key)
            if fact is None:
                continue
            impact = impacts.get(
                key,
                {
                    'clarification_opportunity_count': 0,
                    'blocking_opportunity_count': 0,
                    'upgrade_opportunity_count': 0,
                },
            )
            question = {
                'key': fact.key,
                'label': fact.label,
                'step': 1,
                'kind': fact.value_kind,
                'required': fact.required_in_core,
                'options': fact.options,
                'helper_text': fact.helper_text,
                'audience': ['persona_fisica'] if key in PERSONAL_CORE_KEYS else None,
                'module': 'core_entity',
                'sensitive': fact.sensitive,
                'depends_on': fact.depends_on,
                'ask_when_measure_families': [],
                'why_needed': fact.why_needed,
                'coverage_weight': 0,
                'ambiguity_reduction_score': 0,
                'priority': compute_question_priority({'required': fact.required_in_core, 'impact_counts': impact, 'ambiguity_reduction_score': 0, 'sensitive': fact.sensitive}, unanswered=True),
                'impact_counts': impact,
                'blocking_opportunity_count': impact['blocking_opportunity_count'],
                'upgrade_opportunity_count': impact['upgrade_opportunity_count'],
            }
        items.append(prepare_special_question(question))
    return sorted(items, key=lambda question: keys.index(question['key']))


def prepare_special_question(question: dict) -> dict:
    if question['key'] == 'main_operating_region':
        return {
            **question,
            'label': 'Qual e la tua regione principale?',
            'helper_text': 'Usiamo una regione di riferimento per partire da dove vivi o operi davvero.',
            'why_needed': 'Molte opportunita cambiano in base alla regione e alle priorita territoriali.',
            'required': True,
            'module': 'core_entity',
        }
    if question['key'] in {'employment_type', 'persona_fisica_age_band', 'family_composition', 'figli_a_carico_count'}:
        return {**question, 'required': True, 'module': 'core_entity'}
    if question['key'] in BUSINESS_CORE_KEYS:
        return {**question, 'required': True, 'module': 'core_entity'}
    return question


def build_business_context(profile: Profile | None, fact_values: dict) -> dict:
    profile_type = fact_values.get('profile_type')
    enabled = bool(profile_type and profile_type != 'persona_fisica')
    answered = profile is not None and profile.business_exists is not None and (not profile.business_exists or enabled)
    return {
        'answered': answered,
        'enabled': enabled,
        'profile_type': profile_type if enabled else None,
    }


def build_strategic_modules(grouped_modules: list[dict], fact_values: dict) -> list[dict]:
    buckets: dict[str, list[dict]] = {key: [] for key in STRATEGIC_MODULE_META}
    for module in grouped_modules:
        if module['key'] == 'core_entity':
            continue
        for question in module['questions']:
            if question['key'] in PERSONAL_CORE_KEYS or question['key'] in BUSINESS_CORE_KEYS:
                continue
            if fact_values.get(question['key']) not in (None, '', []):
                continue
            group_key = question_group_key(question['key'])
            buckets.setdefault(group_key, []).append(question)

    strategic_modules = []
    for group_key in ('hiring', 'export', 'digital_energy', 'personal_family', 'general'):
        questions = sorted(
            buckets.get(group_key, []),
            key=lambda item: (
                -(item.get('upgrade_opportunity_count') or 0),
                -(item.get('blocking_opportunity_count') or 0),
                -(item.get('priority') or 0),
                item['label'],
            ),
        )
        if not questions:
            continue
        meta = STRATEGIC_MODULE_META[group_key]
        strategic_modules.append(
            {
                'key': group_key,
                'title': meta['title'],
                'description': meta['description'],
                'why_this_module_matters': meta['why'],
                'questions': questions,
                'clarification_count': sum(question.get('blocking_opportunity_count', 0) for question in questions),
                'upgrade_count': sum(question.get('upgrade_opportunity_count', 0) for question in questions),
            }
        )
    return strategic_modules


def build_results_summary(
    db: Session,
    user: User | None,
    *,
    grouped_modules: list[dict],
    progress_summary: dict,
    strategic_modules: list[dict],
    business_context: dict,
) -> dict:
    ready = user is not None and progress_summary['personal_total'] > 0 and progress_summary['personal_answered'] > 0
    if user is None or not ready:
        return {
            'ready': False,
            'total_matches': 0,
            'blocked_count': 0,
            'profile_state': profile_state_label(progress_summary, business_context, total_matches=0, blocked_count=0),
            'top_matches': [],
            'why_now': [],
            'next_focus_labels': [module['title'] for module in strategic_modules[:2]],
        }

    from app.services.opportunities import list_opportunities

    opportunity_payload = {'modules': grouped_modules}
    all_matches = list_opportunities(db, user, question_payload=opportunity_payload)
    top_matches = all_matches[:4]
    blocked_count = sum(1 for item in all_matches if item['blocking_question_keys'])
    why_now = [item['why_now'] for item in top_matches if item.get('why_now')]
    return {
        'ready': True,
        'total_matches': len(all_matches),
        'blocked_count': blocked_count,
        'profile_state': profile_state_label(progress_summary, business_context, total_matches=len(all_matches), blocked_count=blocked_count),
        'top_matches': top_matches,
        'why_now': why_now[:3],
        'next_focus_labels': [module['title'] for module in strategic_modules[:2]],
    }


def build_onboarding_journey(
    *,
    fact_values: dict,
    personal_core_questions: list[dict],
    business_core_questions: list[dict],
    strategic_modules: list[dict],
    business_context: dict,
    requested_step: str | None,
    requested_module: str | None,
) -> dict:
    personal_complete = all_required_answered(personal_core_questions, fact_values)
    has_business_context = business_context['enabled']
    business_context_complete = business_context['answered']
    business_core_complete = not has_business_context or all_required_answered(business_core_questions, fact_values)
    results_unlocked = personal_complete and business_context_complete and business_core_complete
    final_unlocked = results_unlocked
    strategic_unlocked = results_unlocked and len(strategic_modules) > 0

    allowed_steps = ['personal_core']
    if personal_complete:
        allowed_steps.append('business_context')
    if business_context_complete and has_business_context:
        allowed_steps.append('business_core')
    if results_unlocked:
        allowed_steps.append('results_checkpoint')
    if strategic_unlocked:
        allowed_steps.append('strategic_modules')
    if final_unlocked:
        allowed_steps.append('final_next_actions')

    requested = requested_step or default_requested_step(
        personal_complete,
        business_context_complete,
        has_business_context,
        business_core_complete,
        strategic_modules,
    )
    current_step = requested if requested in allowed_steps else allowed_steps[-1]

    active_module_key = None
    if strategic_unlocked:
        module_keys = [module['key'] for module in strategic_modules]
        active_module_key = requested_module if requested_module in module_keys else module_keys[0]

    completed_steps = set()
    if current_step != 'personal_core' and personal_complete:
        completed_steps.add('personal_core')
    if current_step not in {'personal_core', 'business_context'} and business_context_complete:
        completed_steps.add('business_context')
    if has_business_context and current_step not in {'personal_core', 'business_context', 'business_core'} and business_core_complete:
        completed_steps.add('business_core')
    if current_step not in {'personal_core', 'business_context', 'business_core', 'results_checkpoint'} and results_unlocked:
        completed_steps.add('results_checkpoint')
    if current_step == 'final_next_actions' and strategic_unlocked:
        completed_steps.add('strategic_modules')

    ordered_steps = [
        'personal_core',
        'business_context',
        'business_core' if has_business_context else None,
        'results_checkpoint',
        'strategic_modules' if strategic_unlocked else None,
        'final_next_actions',
    ]
    steps = []
    for step_key in [item for item in ordered_steps if item]:
        status = 'locked'
        if step_key == current_step or step_key in allowed_steps:
            status = 'available'
        if step_key in completed_steps:
            status = 'completed'
        steps.append({'key': step_key, 'label': STEP_LABELS[step_key], 'status': status})

    return {
        'steps': steps,
        'current_step': current_step,
        'next_step': determine_next_step(current_step, has_business_context=has_business_context, strategic_modules=strategic_modules),
        'has_business_context': has_business_context,
        'active_module_key': active_module_key,
    }


def default_requested_step(
    personal_complete: bool,
    business_context_complete: bool,
    has_business_context: bool,
    business_core_complete: bool,
    strategic_modules: list[dict],
) -> str:
    if not personal_complete:
        return 'personal_core'
    if not business_context_complete:
        return 'business_context'
    if has_business_context and not business_core_complete:
        return 'business_core'
    if strategic_modules:
        return 'results_checkpoint'
    return 'results_checkpoint'


def determine_next_step(current_step: str, *, has_business_context: bool, strategic_modules: list[dict]) -> str | None:
    if current_step == 'personal_core':
        return 'business_context'
    if current_step == 'business_context':
        return 'business_core' if has_business_context else 'results_checkpoint'
    if current_step == 'business_core':
        return 'results_checkpoint'
    if current_step == 'results_checkpoint':
        return 'strategic_modules' if strategic_modules else 'final_next_actions'
    if current_step == 'strategic_modules':
        return 'final_next_actions'
    return None


def all_required_answered(questions: list[dict], fact_values: dict) -> bool:
    required_questions = [question for question in questions if question.get('required')]
    if not required_questions:
        return True
    return all(fact_values.get(question['key']) not in (None, '', []) for question in required_questions)


def question_group_key(key: str) -> str:
    if key.startswith('target_hire_') or key == 'hiring_interest':
        return 'hiring'
    if 'export' in key or 'market' in key:
        return 'export'
    if 'digital' in key or 'energy' in key or 'patent' in key or 'balance' in key:
        return 'digital_energy'
    if 'family' in key or 'isee' in key or 'figli' in key or 'persona_fisica' in key or 'employment' in key:
        return 'personal_family'
    return 'general'


def profile_state_label(progress_summary: dict, business_context: dict, *, total_matches: int, blocked_count: int) -> str:
    if progress_summary['personal_answered'] < progress_summary['personal_total']:
        return 'Profilo personale in completamento'
    if business_context['enabled'] and progress_summary['business_answered'] < progress_summary['business_total']:
        return 'Attivita da completare'
    if total_matches == 0:
        return 'Profilo pronto, risultati in aggiornamento'
    if blocked_count > 0:
        return 'Profilo pronto, alcuni match sono da chiarire'
    return 'Profilo pronto'


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
        profile_type = values.get('profile_type') or incoming.get('user_type')
        if business_exists is False and profile_type and profile_type != 'persona_fisica':
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


def compute_question_impacts(db: Session, profile: Profile | None, question_keys: set[str]) -> dict[str, dict[str, int]]:
    impacts = {
        key: {
            'clarification_opportunity_count': 0,
            'blocking_opportunity_count': 0,
            'upgrade_opportunity_count': 0,
        }
        for key in question_keys
    }
    if profile is None:
        return impacts

    matches = db.execute(select(Match).where(Match.user_id == profile.user_id)).scalars().all()
    for match in matches:
        if not match.missing_fields:
            continue
        for field in match.missing_fields:
            if field not in impacts:
                continue
            impacts[field]['clarification_opportunity_count'] += 1
            if match.match_status in {MatchStatus.UNCLEAR.value, MatchStatus.LIKELY.value}:
                impacts[field]['blocking_opportunity_count'] += 1
                impacts[field]['upgrade_opportunity_count'] += 1
    return impacts


def compute_question_priority(question: dict, *, unanswered: bool) -> int:
    if question.get('required'):
        return 10_000
    impact = question.get('impact_counts') or {}
    priority = 0
    if unanswered:
        priority += int(impact.get('upgrade_opportunity_count', 0)) * 100
        priority += int(impact.get('clarification_opportunity_count', 0)) * 10
        priority += int(round(float(question.get('ambiguity_reduction_score') or 0) * 10))
        if question.get('sensitive'):
            priority -= 5
    else:
        priority = 1
    return priority


def build_progress_summary(
    grouped_modules: list[dict],
    fact_values: dict,
    profile: Profile | None,
    *,
    personal_core_questions: list[dict],
    business_core_questions: list[dict],
    strategic_modules: list[dict],
    business_context: dict,
) -> dict:
    counts = {
        'personal_answered': 0,
        'personal_total': 0,
        'business_answered': 0,
        'business_total': 0,
        'core_answered': 0,
        'core_total': 0,
        'strategic_answered': 0,
        'strategic_total': 0,
        'conditional_answered': 0,
        'conditional_total': 0,
        'completeness_score': float(profile.profile_completeness_score if profile is not None else 0),
        'blocked_opportunity_count': 0,
        'upgradable_opportunity_count': 0,
    }
    counts['personal_total'] = len([question for question in personal_core_questions if question.get('required')])
    counts['personal_answered'] = sum(
        1 for question in personal_core_questions if question.get('required') and fact_values.get(question['key']) not in (None, '', [])
    )
    counts['business_total'] = len([question for question in business_core_questions if question.get('required')]) if business_context['enabled'] else 0
    counts['business_answered'] = sum(
        1 for question in business_core_questions if question.get('required') and fact_values.get(question['key']) not in (None, '', [])
    ) if business_context['enabled'] else 0
    counts['core_total'] = counts['personal_total'] + counts['business_total']
    counts['core_answered'] = counts['personal_answered'] + counts['business_answered']

    for module in grouped_modules:
        if module['key'] == 'strategic_intent':
            counts['strategic_total'] = len(module['questions'])
            counts['strategic_answered'] = sum(
                1 for question in module['questions'] if fact_values.get(question['key']) not in (None, '', [])
            )
        elif module['key'] == 'conditional_accuracy':
            counts['conditional_total'] = len(module['questions'])
            counts['conditional_answered'] = sum(
                1 for question in module['questions'] if fact_values.get(question['key']) not in (None, '', [])
            )
        counts['blocked_opportunity_count'] += sum(question.get('blocking_opportunity_count', 0) for question in module['questions'])
        counts['upgradable_opportunity_count'] += sum(question.get('upgrade_opportunity_count', 0) for question in module['questions'])
    if strategic_modules:
        counts['blocked_opportunity_count'] = sum(module.get('clarification_count', 0) for module in strategic_modules)
        counts['upgradable_opportunity_count'] = sum(module.get('upgrade_count', 0) for module in strategic_modules)
    return counts


def recommended_step(grouped_modules: list[dict], fact_values: dict) -> str:
    for module in grouped_modules:
        if module['key'] == 'core_entity':
            if any(fact_values.get(question['key']) in (None, '', []) for question in module['questions']):
                return 'core_entity'
        else:
            if any(
                fact_values.get(question['key']) in (None, '', []) and (question.get('priority') or 0) > 0
                for question in module['questions']
            ):
                return module['key']
    return 'results'
