from app.matching.rules import compute_match
from app.services.profile import compute_profile_completeness


RULE = {
    'required': [
        {'in': {'field': 'user_type', 'value': ['startup', 'sme']}},
        {'eq': {'field': 'business_exists', 'value': True}},
        {'in': {'field': 'company_size_band', 'value': ['micro', 'small']}},
    ],
    'disqualifiers': [{'eq': {'field': 'user_type', 'value': 'advisor'}}],
    'boosters': [{'eq': {'field': 'innovation_intent', 'value': True}}],
    'tolerated_missing': [{'missing': {'field': 'company_size_band'}}],
}


def test_confirmed_match() -> None:
    result = compute_match(
        RULE,
        {
            'user_type': 'startup',
            'business_exists': True,
            'company_size_band': 'micro',
            'innovation_intent': True,
        },
    )
    assert result.status == 'confirmed'
    assert result.score > 0


def test_not_eligible_when_hard_requirement_fails() -> None:
    result = compute_match(
        RULE,
        {
            'user_type': 'freelancer',
            'business_exists': True,
            'company_size_band': 'micro',
            'innovation_intent': False,
        },
    )
    assert result.status == 'not_eligible'


def test_likely_when_tolerated_missing_fields_exist() -> None:
    result = compute_match(
        RULE,
        {
            'user_type': 'startup',
            'business_exists': True,
            'company_size_band': None,
        },
    )
    assert result.status == 'likely'
    assert 'company_size_band' in result.missing_fields


def test_profile_completeness_scores_progressively() -> None:
    sparse = compute_profile_completeness({'user_type': 'startup'})
    rich = compute_profile_completeness(
        {
            'user_type': 'startup',
            'region': 'Lombardia',
            'business_exists': True,
            'company_size_band': 'micro',
            'sector_code_or_category': 'digitale',
            'company_age_band': '1-3y',
            'hiring_intent': True,
            'innovation_intent': True,
        }
    )
    assert rich > sparse
