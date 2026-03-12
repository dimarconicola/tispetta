from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from app.models import MatchStatus


@dataclass
class ClauseResult:
    ok: bool
    missing_fields: list[str]
    matched_conditions: list[dict[str, Any]]
    failed_conditions: list[dict[str, Any]]


@dataclass
class MatchComputation:
    status: str
    score: float
    missing_fields: list[str]
    matched_conditions: list[dict[str, Any]]
    failed_conditions: list[dict[str, Any]]
    blockers: list[dict[str, Any]]
    boosters: list[dict[str, Any]]


PROFILE_FIELD_LABELS: dict[str, str] = {
    'user_type': 'Tipo utente',
    'region': 'Regione',
    'province': 'Provincia',
    'business_exists': 'Esistenza attivita',
    'legal_entity_type': 'Forma giuridica',
    'company_age_band': 'Anzianita impresa',
    'company_size_band': 'Dimensione impresa',
    'revenue_band': 'Fascia di ricavi',
    'sector_code_or_category': 'Settore',
    'hiring_intent': 'Intenzione di assumere',
    'innovation_intent': 'Intenzione di innovazione',
    'sustainability_intent': 'Intenzione di sostenibilita',
    'export_intent': 'Intenzione di export',
    'startup_stage': 'Fase startup',
    'incorporation_status': 'Stato costituzione',
}


def get_value(payload: dict[str, Any], key: str) -> Any:
    return payload.get(key)


def normalize_list(value: Any) -> list[Any]:
    if value is None:
        return []
    if isinstance(value, list):
        return value
    return [value]


OPERATORS = {'all', 'any', 'not', 'eq', 'neq', 'in', 'not_in', 'gte', 'lte', 'exists', 'missing', 'between'}


def eval_condition(condition: dict[str, Any], payload: dict[str, Any]) -> ClauseResult:
    operator = next((key for key in condition if key in OPERATORS), None)
    if operator is None:
        raise ValueError(f'Unsupported condition: {condition}')

    if operator == 'all':
        return combine(condition['all'], payload, mode='all')
    if operator == 'any':
        return combine(condition['any'], payload, mode='any')
    if operator == 'not':
        inner = eval_condition(condition['not'], payload)
        ok = not inner.ok
        return ClauseResult(ok=ok, missing_fields=inner.missing_fields, matched_conditions=[] if ok else inner.matched_conditions, failed_conditions=inner.failed_conditions if ok else inner.matched_conditions)

    field = condition[operator]['field']
    expected = condition[operator].get('value')
    value = get_value(payload, field)
    label = PROFILE_FIELD_LABELS.get(field, field)

    if operator == 'exists':
        ok = value not in (None, '', [])
    elif operator == 'missing':
        ok = value in (None, '', [])
        if ok:
            return ClauseResult(
                ok=True,
                missing_fields=[field],
                matched_conditions=[{'field': field, 'label': label, 'operator': operator, 'expected': expected, 'actual': value}],
                failed_conditions=[],
            )
        return ClauseResult(
            ok=False,
            missing_fields=[],
            matched_conditions=[],
            failed_conditions=[{'field': field, 'label': label, 'operator': operator, 'expected': expected, 'actual': value}],
        )
    else:
        if value in (None, '', []):
            return ClauseResult(ok=False, missing_fields=[field], matched_conditions=[], failed_conditions=[{'field': field, 'label': label, 'operator': operator, 'expected': expected, 'actual': value}])
        if operator == 'eq':
            ok = value == expected
        elif operator == 'neq':
            ok = value != expected
        elif operator == 'in':
            ok = value in normalize_list(expected)
        elif operator == 'not_in':
            ok = value not in normalize_list(expected)
        elif operator == 'gte':
            ok = value >= expected
        elif operator == 'lte':
            ok = value <= expected
        elif operator == 'between':
            lower = condition[operator].get('min')
            upper = condition[operator].get('max')
            ok = lower <= value <= upper
        else:
            raise ValueError(f'Unsupported operator: {operator}')

    descriptor = {'field': field, 'label': label, 'operator': operator, 'expected': expected, 'actual': value}
    if operator == 'between':
        descriptor['expected'] = {'min': condition[operator].get('min'), 'max': condition[operator].get('max')}
    return ClauseResult(ok=ok, missing_fields=[], matched_conditions=[descriptor] if ok else [], failed_conditions=[] if ok else [descriptor])


def combine(conditions: list[dict[str, Any]], payload: dict[str, Any], mode: str) -> ClauseResult:
    results = [eval_condition(item, payload) for item in conditions]
    missing_fields = sorted({field for result in results for field in result.missing_fields})
    matched_conditions = [item for result in results for item in result.matched_conditions]
    failed_conditions = [item for result in results for item in result.failed_conditions]
    ok = all(result.ok for result in results) if mode == 'all' else any(result.ok for result in results)
    return ClauseResult(ok=ok, missing_fields=missing_fields, matched_conditions=matched_conditions, failed_conditions=failed_conditions)


def compute_match(rule_json: dict[str, Any], payload: dict[str, Any]) -> MatchComputation:
    required = [eval_condition(condition, payload) for condition in rule_json.get('required', [])]
    disqualifiers = [eval_condition(condition, payload) for condition in rule_json.get('disqualifiers', [])]
    boosters = [eval_condition(condition, payload) for condition in rule_json.get('boosters', [])]
    tolerated_missing = [eval_condition(condition, payload) for condition in rule_json.get('tolerated_missing', [])]

    matched_required = [item for result in required for item in result.matched_conditions]
    failed_required = [item for result in required for item in result.failed_conditions]
    missing_fields = sorted({field for result in required for field in result.missing_fields})
    triggered_disqualifiers = [item for result in disqualifiers if result.ok for item in result.matched_conditions]
    matched_boosters = [item for result in boosters if result.ok for item in result.matched_conditions]
    tolerated_missing_fields = {field for result in tolerated_missing for field in result.missing_fields}

    if triggered_disqualifiers:
        return MatchComputation(
            status=MatchStatus.NOT_ELIGIBLE.value,
            score=0.0,
            missing_fields=missing_fields,
            matched_conditions=matched_required,
            failed_conditions=failed_required,
            blockers=triggered_disqualifiers,
            boosters=matched_boosters,
        )

    hard_failures = [
        result
        for result in required
        if not result.ok and (not result.missing_fields or not set(result.missing_fields).issubset(tolerated_missing_fields))
    ]
    all_required_ok = all(result.ok for result in required)

    if all_required_ok and not missing_fields:
        base_status = MatchStatus.CONFIRMED.value
    elif hard_failures:
        has_missing = any(result.missing_fields for result in hard_failures)
        base_status = MatchStatus.UNCLEAR.value if has_missing else MatchStatus.NOT_ELIGIBLE.value
    else:
        base_status = MatchStatus.LIKELY.value

    score = 40.0
    score += len(matched_required) * 10
    score += len(matched_boosters) * 4
    score -= len(failed_required) * 8
    score -= len(missing_fields) * 6
    if base_status == MatchStatus.CONFIRMED.value:
        score += 20
    elif base_status == MatchStatus.LIKELY.value:
        score += 8
    elif base_status == MatchStatus.NOT_ELIGIBLE.value:
        score = min(score, 10)

    return MatchComputation(
        status=base_status,
        score=max(score, 0),
        missing_fields=missing_fields,
        matched_conditions=matched_required,
        failed_conditions=failed_required,
        blockers=triggered_disqualifiers,
        boosters=matched_boosters,
    )
