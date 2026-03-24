from __future__ import annotations

from collections.abc import Iterable
from datetime import UTC, datetime

from sqlalchemy import Select, func, or_, select
from sqlalchemy.orm import Session, joinedload

from app.matching.rules import PROFILE_FIELD_LABELS
from app.models import Match, MatchEvaluation, Opportunity, RecordStatus, SavedOpportunity, User
from app.services.opportunity_scope import derive_opportunity_scope, matches_scope_filter
from app.services.profile import get_profile_questions


def _search_clause(query: str):
    pattern = f"%{query.lower()}%"
    return or_(
        func.lower(Opportunity.title).like(pattern),
        func.lower(Opportunity.short_description).like(pattern),
        func.lower(Opportunity.category).like(pattern),
    )


def list_opportunities(
    db: Session,
    user: User | None,
    *,
    query: str | None = None,
    category: str | None = None,
    matched_status: str | None = None,
    saved_only: bool = False,
    scope: str | None = None,
    limit: int | None = None,
    question_payload: dict | None = None,
) -> list[dict]:
    stmt: Select[tuple[Opportunity]] = (
        select(Opportunity)
        .options(joinedload(Opportunity.current_version))
        .where(Opportunity.record_status == RecordStatus.PUBLISHED.value)
        .order_by(Opportunity.deadline_date.is_(None), Opportunity.deadline_date.asc(), Opportunity.updated_at.desc())
    )
    if query:
        stmt = stmt.where(_search_clause(query))
    if category:
        stmt = stmt.where(Opportunity.category == category)

    opportunities = db.execute(stmt).scalars().all()
    saved_ids: set[str] = set()
    matches_by_opp: dict[str, Match] = {}
    latest_evaluations_by_match_id: dict[str, MatchEvaluation] = {}
    question_lookup: dict[str, dict] = {}
    if user is not None:
        saved_ids = set(
            db.execute(select(SavedOpportunity.opportunity_id).where(SavedOpportunity.user_id == user.id)).scalars().all()
        )
        user_matches = db.execute(select(Match).where(Match.user_id == user.id)).scalars().all()
        matches_by_opp = {match.opportunity_id: match for match in user_matches}
        if user_matches:
            evaluations = (
                db.execute(
                    select(MatchEvaluation)
                    .where(MatchEvaluation.match_id.in_([match.id for match in user_matches]))
                    .order_by(MatchEvaluation.created_at.desc())
                )
                .scalars()
                .all()
            )
            for evaluation in evaluations:
                latest_evaluations_by_match_id.setdefault(evaluation.match_id, evaluation)
        question_lookup = flatten_question_lookup(question_payload or get_profile_questions(db, user))

    payloads: list[dict] = []
    for opportunity in opportunities:
        opportunity_scope = derive_opportunity_scope(opportunity.current_version.target_entities if opportunity.current_version else None)
        if not matches_scope_filter(opportunity_scope, scope):
            continue
        match = matches_by_opp.get(opportunity.id)
        evaluation = latest_evaluations_by_match_id.get(match.id) if match else None
        match_meta = build_match_metadata(match, evaluation, question_lookup)
        if matched_status and (match is None or match.match_status != matched_status):
            continue
        if saved_only and opportunity.id not in saved_ids:
            continue
        payloads.append(
            {
                'id': opportunity.id,
                'slug': opportunity.slug,
                'title': opportunity.title,
                'short_description': opportunity.short_description,
                'category': opportunity.category,
                'opportunity_scope': opportunity_scope,
                'geography_scope': opportunity.geography_scope,
                'benefit_type': opportunity.benefit_type,
                'match_status': match.match_status if match else None,
                'match_score': match.match_score if match else None,
                'user_visible_reasoning': match.explanation_summary if match else None,
                'missing_fields': match.missing_fields if match else [],
                'deadline_date': opportunity.deadline_date,
                'estimated_value_max': opportunity.estimated_value_max,
                'last_checked_at': opportunity.last_checked_at,
                'is_saved': opportunity.id in saved_ids,
                'why_now': build_why_now(match, match_meta),
                'blocking_question_keys': match_meta['blocking_keys'],
                'match_reasons': match_meta['matched_reasons'],
                'blocking_missing_labels': match_meta['blocking_labels'],
            }
        )
    payloads.sort(
        key=lambda item: (
            status_rank(item['match_status']),
            len(item['blocking_question_keys']),
            deadline_urgency_bucket(item['deadline_date']),
            -len(item['match_reasons']),
            -(item['match_score'] or 0),
            -float(item['estimated_value_max'] or 0),
            freshness_bucket(item['last_checked_at']),
        )
    )
    if limit is not None:
        return payloads[:limit]
    return payloads


def status_rank(status: str | None) -> int:
    order = {'confirmed': 0, 'likely': 1, 'unclear': 2, 'not_eligible': 3}
    return order.get(status or 'unclear', 2)


def get_opportunity_detail(db: Session, opportunity_key: str, user: User | None) -> dict | None:
    opportunity = db.execute(
        select(Opportunity)
        .options(joinedload(Opportunity.current_version))
        .where(or_(Opportunity.slug == opportunity_key, Opportunity.id == opportunity_key))
    ).scalar_one_or_none()
    if opportunity is None or opportunity.current_version is None:
        return None
    version = opportunity.current_version
    match = None
    is_saved = False
    evaluation = None
    question_lookup: dict[str, dict] = {}
    if user is not None:
        match = db.execute(select(Match).where(Match.user_id == user.id, Match.opportunity_id == opportunity.id)).scalar_one_or_none()
        is_saved = db.execute(
            select(SavedOpportunity).where(SavedOpportunity.user_id == user.id, SavedOpportunity.opportunity_id == opportunity.id)
        ).scalar_one_or_none() is not None
        question_lookup = flatten_question_lookup(get_profile_questions(db, user))
        if match is not None:
            evaluation = db.execute(
                select(MatchEvaluation)
                .where(MatchEvaluation.match_id == match.id)
                .order_by(MatchEvaluation.created_at.desc())
            ).scalars().first()

    match_meta = build_match_metadata(match, evaluation, question_lookup)
    why = match_meta['matched_reasons'] or ([match.explanation_summary] if match is not None else [])
    missing = match_meta['blocking_labels'] or ([PROFILE_FIELD_LABELS.get(item, item) for item in match.missing_fields] if match is not None else [])
    opportunity_scope = derive_opportunity_scope(version.target_entities)

    return {
        'id': opportunity.id,
        'slug': opportunity.slug,
        'title': version.title,
        'short_description': version.short_description,
        'long_description': version.long_description,
        'category': version.category,
        'opportunity_scope': opportunity_scope,
        'geography_scope': version.geography_scope,
        'benefit_type': version.benefit_type,
        'match_status': match.match_status if match else None,
        'match_score': match.match_score if match else None,
        'user_visible_reasoning': match.user_visible_reasoning if match else None,
        'missing_fields': missing,
        'deadline_date': version.deadline_date,
        'estimated_value_max': version.estimated_value_max,
        'last_checked_at': version.last_checked_at,
        'issuer_name': version.issuer_name,
        'official_links': version.official_links,
        'source_documents': version.source_documents,
        'evidence_snippets': version.evidence_snippets,
        'required_documents': version.required_documents,
        'next_steps': build_next_steps(version),
        'why_this_matches': why,
        'what_is_missing': missing,
        'verification_status': version.verification_status,
        'is_saved': is_saved,
        'why_now': build_why_now(match, match_meta),
        'blocking_question_keys': match_meta['blocking_keys'],
        'match_reasons': match_meta['matched_reasons'],
        'blocking_missing_labels': match_meta['blocking_labels'],
        'match_breakdown': {
            'status': match.match_status if match else None,
            'matched_reasons': match_meta['matched_reasons'],
            'blocking_missing_facts': match_meta['blocking_facts'],
            'refinement_facts': match_meta['refinement_facts'],
            'next_best_questions': match_meta['next_best_questions'],
            'why_matched': why,
            'what_blocks_confirmation': [
                f"Manca {label.lower()}" for label in match_meta['blocking_labels']
            ],
        },
    }


def build_next_steps(version) -> list[str]:
    steps = ['Verifica il testo ufficiale e i documenti richiesti.']
    if version.application_window_end:
        steps.append('Controlla la finestra di apertura e chiusura della domanda.')
    if version.required_documents:
        steps.append('Prepara la documentazione essenziale prima dell\'invio.')
    return steps


def save_opportunity(db: Session, user: User, opportunity_id: str) -> None:
    existing = db.execute(
        select(SavedOpportunity).where(SavedOpportunity.user_id == user.id, SavedOpportunity.opportunity_id == opportunity_id)
    ).scalar_one_or_none()
    if existing is None:
        db.add(SavedOpportunity(user_id=user.id, opportunity_id=opportunity_id))
        db.commit()


def unsave_opportunity(db: Session, user: User, opportunity_id: str) -> None:
    existing = db.execute(
        select(SavedOpportunity).where(SavedOpportunity.user_id == user.id, SavedOpportunity.opportunity_id == opportunity_id)
    ).scalar_one_or_none()
    if existing is not None:
        db.delete(existing)
        db.commit()


def interpret_query(query: str) -> dict:
    lowered = query.lower()
    category = None
    if 'assun' in lowered or 'personale' in lowered:
        category = 'hiring_incentive'
    elif 'digit' in lowered or 'software' in lowered:
        category = 'digitization_incentive'
    elif 'export' in lowered or 'estero' in lowered:
        category = 'export_incentive'
    elif 'energia' in lowered or 'sostenibil' in lowered:
        category = 'sustainability_incentive'
    return {'query': query, 'category': category}


def flatten_question_lookup(question_payload: dict | None) -> dict[str, dict]:
    lookup: dict[str, dict] = {}
    if not question_payload:
        return lookup
    for module in question_payload.get('modules', []):
        for question in module.get('questions', []):
            lookup[question['key']] = question
    return lookup


def build_match_metadata(
    match: Match | None,
    evaluation: MatchEvaluation | None,
    question_lookup: dict[str, dict],
) -> dict[str, list | dict]:
    trace = evaluation.rule_evaluation_trace if evaluation is not None else {}
    matched_reasons = unique_preserving_order(
        [item.get('label') for item in trace.get('matched_conditions', []) if item.get('label')]
    )[:3]
    blocking_keys = trace.get('blocking_missing_fields') or []
    refinement_keys = trace.get('refinement_missing_fields') or []
    blocking_facts = [build_question_hint(key, question_lookup) for key in blocking_keys]
    refinement_facts = [build_question_hint(key, question_lookup) for key in refinement_keys]
    next_best_questions = sorted(
        blocking_facts + refinement_facts,
        key=lambda item: (-(item['upgrade_opportunity_count']), -(item['blocking_opportunity_count']), item['label']),
    )[:3]
    return {
        'matched_reasons': matched_reasons or ([match.explanation_summary] if match is not None and match.explanation_summary else []),
        'blocking_keys': blocking_keys,
        'blocking_labels': [item['label'] for item in blocking_facts],
        'blocking_facts': blocking_facts,
        'refinement_facts': refinement_facts,
        'next_best_questions': next_best_questions,
    }


def build_question_hint(key: str, question_lookup: dict[str, dict]) -> dict:
    question = question_lookup.get(key)
    if question is None:
        return {
            'key': key,
            'label': PROFILE_FIELD_LABELS.get(key, key.replace('_', ' ')),
            'kind': 'unknown',
            'why_this_question_matters_now': None,
            'blocking_opportunity_count': 0,
            'upgrade_opportunity_count': 0,
        }
    return {
        'key': key,
        'label': question['label'],
        'kind': question['kind'],
        'why_this_question_matters_now': question.get('why_needed'),
        'blocking_opportunity_count': question.get('blocking_opportunity_count', 0),
        'upgrade_opportunity_count': question.get('upgrade_opportunity_count', 0),
    }


def build_why_now(match: Match | None, meta: dict[str, list | dict]) -> str | None:
    if match is None:
        return 'Completa il profilo per ottenere un primo match spiegabile.'
    if meta['blocking_labels']:
        labels = ', '.join(meta['blocking_labels'][:2])
        return f"Puoi confermarla rispondendo prima su {labels}."
    if meta['matched_reasons']:
        return f"Sta emergendo ora per {meta['matched_reasons'][0].lower()}."
    return match.explanation_summary


def deadline_urgency_bucket(deadline_date) -> int:
    if deadline_date is None:
        return 4
    normalized = ensure_utc(deadline_date)
    days = (normalized - datetime.now(UTC)).days
    if days <= 7:
        return 0
    if days <= 30:
        return 1
    return 2


def freshness_bucket(last_checked_at) -> float:
    if last_checked_at is None:
        return float('inf')
    return (datetime.now(UTC) - ensure_utc(last_checked_at)).total_seconds()


def unique_preserving_order(values: Iterable[str | None]) -> list[str]:
    seen: set[str] = set()
    ordered: list[str] = []
    for value in values:
        if not value or value in seen:
            continue
        seen.add(value)
        ordered.append(value)
    return ordered


def ensure_utc(value: datetime) -> datetime:
    if value.tzinfo is None:
        return value.replace(tzinfo=UTC)
    return value.astimezone(UTC)
