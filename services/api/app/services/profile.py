from __future__ import annotations

from sqlalchemy.orm import Session

from app.models import NotificationPreference, Profile, ProfileRevision, User
from app.schemas.profile import ProfilePayload

CORE_FIELDS = [
    'user_type',
    'region',
    'business_exists',
    'company_size_band',
    'sector_code_or_category',
    'company_age_band',
]

OPTIONAL_FIELDS = [
    'province',
    'legal_entity_type',
    'revenue_band',
    'hiring_intent',
    'innovation_intent',
    'sustainability_intent',
    'export_intent',
    'goals',
]


PROFILE_QUESTIONS = [
    {
        'key': 'user_type',
        'label': 'Quale profilo ti descrive meglio?',
        'step': 1,
        'kind': 'select',
        'required': True,
        'options': ['freelancer', 'startup', 'sme', 'advisor'],
        'helper_text': 'L\'esperienza si adatta al tuo profilo.',
        'audience': ['freelancer', 'startup', 'sme', 'advisor'],
    },
    {
        'key': 'region',
        'label': 'In quale regione operi?',
        'step': 2,
        'kind': 'select',
        'required': True,
        'options': ['Lombardia', 'Lazio', 'Campania', 'Puglia', 'Sicilia', 'Veneto', 'Emilia-Romagna', 'Toscana'],
        'helper_text': 'Serve per filtrare opportunita geografiche.',
        'audience': ['freelancer', 'startup', 'sme'],
    },
    {
        'key': 'business_exists',
        'label': 'Hai gia un\'attivita costituita?',
        'step': 2,
        'kind': 'select',
        'required': True,
        'options': ['true', 'false'],
        'helper_text': 'Molti incentivi distinguono tra impresa costituita e progetto in avvio.',
        'audience': ['freelancer', 'startup', 'sme'],
    },
    {
        'key': 'company_size_band',
        'label': 'Quanto e grande l\'attivita?',
        'step': 2,
        'kind': 'select',
        'required': False,
        'options': ['solo', 'micro', 'small', 'medium'],
        'helper_text': 'Serve per incentivi dedicati a startup, microimprese e PMI.',
        'audience': ['freelancer', 'startup', 'sme'],
    },
    {
        'key': 'company_age_band',
        'label': 'Da quanto tempo esiste l\'attivita?',
        'step': 2,
        'kind': 'select',
        'required': False,
        'options': ['idea', '0-12m', '1-3y', '3-5y', '5y+'],
        'helper_text': 'Molte misure sono limitate alle imprese giovani.',
        'audience': ['startup', 'sme'],
    },
    {
        'key': 'sector_code_or_category',
        'label': 'Qual e il tuo settore principale?',
        'step': 2,
        'kind': 'select',
        'required': True,
        'options': ['digitale', 'manifattura', 'servizi', 'turismo', 'retail', 'energia', 'agritech'],
        'helper_text': 'Aiuta a far emergere bandi verticali.',
        'audience': ['freelancer', 'startup', 'sme'],
    },
    {
        'key': 'hiring_intent',
        'label': 'Hai intenzione di assumere nei prossimi 12 mesi?',
        'step': 4,
        'kind': 'select',
        'required': False,
        'options': ['true', 'false'],
        'audience': ['startup', 'sme', 'freelancer'],
    },
    {
        'key': 'innovation_intent',
        'label': 'Cerchi incentivi per innovazione o R&D?',
        'step': 4,
        'kind': 'select',
        'required': False,
        'options': ['true', 'false'],
        'audience': ['startup', 'sme'],
    },
    {
        'key': 'sustainability_intent',
        'label': 'Hai progetti legati a sostenibilita o efficienza energetica?',
        'step': 4,
        'kind': 'select',
        'required': False,
        'options': ['true', 'false'],
        'audience': ['startup', 'sme'],
    },
    {
        'key': 'export_intent',
        'label': 'Vuoi espanderti all\'estero?',
        'step': 4,
        'kind': 'select',
        'required': False,
        'options': ['true', 'false'],
        'audience': ['startup', 'sme'],
    },
]


def compute_profile_completeness(payload: dict) -> float:
    score = 0.0
    for field in CORE_FIELDS:
        if payload.get(field) not in (None, '', []):
            score += 12
    for field in OPTIONAL_FIELDS:
        if payload.get(field) not in (None, '', []):
            score += 3.5
    return min(round(score, 1), 100.0)


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
        'profile_completeness_score': profile.profile_completeness_score,
    }


def get_or_create_profile(db: Session, user: User) -> Profile:
    if user.profile is not None:
        return user.profile
    profile = Profile(user_id=user.id, country='IT', profile_completeness_score=0.0)
    db.add(profile)
    db.flush()
    if user.notification_preferences is None:
        db.add(NotificationPreference(user_id=user.id))
    return profile


def update_profile(db: Session, user: User, payload: ProfilePayload) -> Profile:
    profile = get_or_create_profile(db, user)
    incoming = payload.model_dump(exclude_unset=True)
    for key, value in incoming.items():
        setattr(profile, key, value)
    profile.profile_completeness_score = compute_profile_completeness({**serialize_profile(profile), **incoming})
    revision_number = len(profile.revisions) + 1
    db.add(
        ProfileRevision(
            profile_id=profile.id,
            revision_number=revision_number,
            payload=serialize_profile(profile),
        )
    )
    db.commit()
    db.refresh(profile)
    return profile
