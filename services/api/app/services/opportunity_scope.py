from __future__ import annotations

PERSONAL_PROFILE_TYPE = 'persona_fisica'
PERSONAL_SCOPE = 'personal'
BUSINESS_SCOPE = 'business'
HYBRID_SCOPE = 'hybrid'


def active_profile_types(profile_type: str | None) -> list[str]:
    active = [PERSONAL_PROFILE_TYPE]
    if profile_type and profile_type != PERSONAL_PROFILE_TYPE:
        active.append(profile_type)
    return active


def derive_opportunity_scope(target_entities: list[str] | None) -> str:
    entities = set(target_entities or [])
    if not entities:
        return HYBRID_SCOPE
    if entities == {PERSONAL_PROFILE_TYPE}:
        return PERSONAL_SCOPE
    if PERSONAL_PROFILE_TYPE in entities:
        return HYBRID_SCOPE
    return BUSINESS_SCOPE


def matches_scope_filter(opportunity_scope: str, scope_filter: str | None) -> bool:
    if not scope_filter:
        return True
    if scope_filter == PERSONAL_SCOPE:
        return opportunity_scope in {PERSONAL_SCOPE, HYBRID_SCOPE}
    if scope_filter == BUSINESS_SCOPE:
        return opportunity_scope in {BUSINESS_SCOPE, HYBRID_SCOPE}
    if scope_filter == HYBRID_SCOPE:
        return opportunity_scope == HYBRID_SCOPE
    return True


def resolve_effective_profile_type(
    *,
    target_entities: list[str] | None,
    stored_profile_type: str | None,
) -> str:
    entities = set(target_entities or [])
    active_types = active_profile_types(stored_profile_type)
    business_types = [item for item in active_types if item != PERSONAL_PROFILE_TYPE]

    if not entities:
        return business_types[0] if business_types else PERSONAL_PROFILE_TYPE
    if PERSONAL_PROFILE_TYPE in entities and not business_types:
        return PERSONAL_PROFILE_TYPE
    for business_type in business_types:
        if business_type in entities:
            return business_type
    if PERSONAL_PROFILE_TYPE in entities:
        return PERSONAL_PROFILE_TYPE
    return business_types[0] if business_types else PERSONAL_PROFILE_TYPE
