from __future__ import annotations

from dataclasses import asdict
from datetime import UTC, datetime
from typing import Any

from sqlalchemy import select
from sqlalchemy.orm import Session, joinedload

from app.matching.rules import compute_match
from app.models import Match, MatchEvaluation, Opportunity, OpportunityRule, OpportunityVersion, Profile, RecordStatus


def shortlist_candidates(profile: Profile, opportunities: list[Opportunity]) -> list[Opportunity]:
    shortlist: list[Opportunity] = []
    for opportunity in opportunities:
        version = opportunity.current_version
        if version is None or opportunity.record_status != RecordStatus.PUBLISHED.value:
            continue
        if version.country != 'IT':
            continue
        if version.target_entities and profile.user_type and profile.user_type not in version.target_entities:
            continue
        if version.company_size_constraints and profile.company_size_band and profile.company_size_band not in version.company_size_constraints:
            continue
        if version.target_sectors and profile.sector_code_or_category and profile.sector_code_or_category not in version.target_sectors:
            continue
        shortlist.append(opportunity)
    return shortlist


def build_explanation(opportunity: Opportunity, status: str, matched: list[dict[str, Any]], missing: list[str]) -> tuple[str, str]:
    version = opportunity.current_version
    title = version.title if version else opportunity.title
    reasons = [f"Compatibile con {item['label'].lower()}" for item in matched[:3]]
    if not reasons:
        reasons = [f'Regola disponibile per {title}']
    summary = '; '.join(reasons)
    if missing:
        summary = f"{summary}. Mancano dati su: {', '.join(missing)}."
    full = f"{title}: stato {status}. {summary}"
    return summary, full


def evaluate_profile_against_catalog(db: Session, profile: Profile) -> list[Match]:
    opportunities = db.execute(
        select(Opportunity)
        .options(joinedload(Opportunity.current_version).joinedload(OpportunityVersion.rules))
        .where(Opportunity.record_status == RecordStatus.PUBLISHED.value)
    ).unique().scalars().all()
    shortlisted = shortlist_candidates(profile, opportunities)
    results: list[Match] = []

    for opportunity in shortlisted:
        version = opportunity.current_version
        if version is None:
            continue
        active_rule = next((rule for rule in version.rules if rule.is_active), None)
        if active_rule is None:
            continue
        payload = {
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
            'hiring_intent': profile.hiring_intent,
            'innovation_intent': profile.innovation_intent,
            'sustainability_intent': profile.sustainability_intent,
            'export_intent': profile.export_intent,
            'startup_stage': profile.startup_stage,
            'incorporation_status': profile.incorporation_status,
        }
        computed = compute_match(active_rule.rule_json, payload)
        summary, full = build_explanation(opportunity, computed.status, computed.matched_conditions, computed.missing_fields)

        match = db.execute(
            select(Match).where(Match.user_id == profile.user_id, Match.opportunity_id == opportunity.id)
        ).scalar_one_or_none()
        if match is None:
            match = Match(
                user_id=profile.user_id,
                opportunity_id=opportunity.id,
                match_status=computed.status,
                match_score=computed.score,
                explanation_summary=summary,
                user_visible_reasoning=full,
                missing_fields=computed.missing_fields,
            )
            db.add(match)
            db.flush()
        else:
            match.match_status = computed.status
            match.match_score = computed.score
            match.explanation_summary = summary
            match.user_visible_reasoning = full
            match.missing_fields = computed.missing_fields
            match.last_evaluated_at = datetime.now(UTC)

        evaluation = MatchEvaluation(
            match_id=match.id,
            rule_id=active_rule.id,
            rule_evaluation_trace={
                'status': computed.status,
                'matched_conditions': computed.matched_conditions,
                'failed_conditions': computed.failed_conditions,
                'blockers': computed.blockers,
                'missing_fields': computed.missing_fields,
            },
            ranking_inputs={
                'score': computed.score,
                'matched_conditions_count': len(computed.matched_conditions),
                'boosters_count': len(computed.boosters),
            },
        )
        db.add(evaluation)
        results.append(match)
    db.commit()
    return results


def run_rule_tests(rule: OpportunityRule) -> list[dict[str, Any]]:
    results: list[dict[str, Any]] = []
    for case in rule.test_cases:
        computed = compute_match(rule.rule_json, case.profile_payload)
        results.append(
            {
                'case_id': case.id,
                'name': case.name,
                'scenario_type': case.scenario_type,
                'expected_status': case.expected_status,
                'actual_status': computed.status,
                'passed': computed.status == case.expected_status,
                'missing_fields': computed.missing_fields,
            }
        )
    return results
