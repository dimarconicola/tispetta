from __future__ import annotations

from collections.abc import Iterable

from sqlalchemy import Select, func, or_, select
from sqlalchemy.orm import Session, joinedload

from app.models import Match, Opportunity, RecordStatus, SavedOpportunity, User


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
    if user is not None:
        saved_ids = set(
            db.execute(select(SavedOpportunity.opportunity_id).where(SavedOpportunity.user_id == user.id)).scalars().all()
        )
        user_matches = db.execute(select(Match).where(Match.user_id == user.id)).scalars().all()
        matches_by_opp = {match.opportunity_id: match for match in user_matches}

    payloads: list[dict] = []
    for opportunity in opportunities:
        match = matches_by_opp.get(opportunity.id)
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
            }
        )
    payloads.sort(
        key=lambda item: (
            status_rank(item['match_status']),
            item['deadline_date'].timestamp() if item['deadline_date'] else float('inf'),
            -(item['match_score'] or 0),
        )
    )
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
    if user is not None:
        match = db.execute(select(Match).where(Match.user_id == user.id, Match.opportunity_id == opportunity.id)).scalar_one_or_none()
        is_saved = db.execute(
            select(SavedOpportunity).where(SavedOpportunity.user_id == user.id, SavedOpportunity.opportunity_id == opportunity.id)
        ).scalar_one_or_none() is not None

    why = []
    missing = []
    if match is not None:
        why = [match.explanation_summary]
        missing = match.missing_fields

    return {
        'id': opportunity.id,
        'slug': opportunity.slug,
        'title': version.title,
        'short_description': version.short_description,
        'long_description': version.long_description,
        'category': version.category,
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
