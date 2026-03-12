from __future__ import annotations

from datetime import UTC, datetime

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.matching.service import run_rule_tests
from app.models import (
    AuditEvent,
    IngestionRun,
    Opportunity,
    OpportunityRule,
    OpportunityVersion,
    RecordStatus,
    ReviewItem,
    ReviewStatus,
    Source,
)


def create_source(db: Session, payload) -> Source:
    source = Source(**payload.model_dump())
    db.add(source)
    db.commit()
    db.refresh(source)
    return source


def trigger_ingestion_run(db: Session, source_id: str) -> IngestionRun | None:
    source = db.execute(select(Source).where(Source.id == source_id)).scalar_one_or_none()
    if source is None or not source.endpoints:
        return None
    run = IngestionRun(source_endpoint_id=source.endpoints[0].id, stage='fetch', status='queued', diagnostics={'manual': True})
    db.add(run)
    db.commit()
    db.refresh(run)
    return run


def resolve_review_item(db: Session, review_item_id: str, resolution_note: str, actor_user_id: str) -> ReviewItem | None:
    item = db.execute(select(ReviewItem).where(ReviewItem.id == review_item_id)).scalar_one_or_none()
    if item is None:
        return None
    item.status = ReviewStatus.RESOLVED.value
    item.resolved_at = datetime.now(UTC)
    payload = item.payload or {}
    payload['resolution_note'] = resolution_note
    item.payload = payload
    db.add(AuditEvent(actor_user_id=actor_user_id, action='review.resolve', entity_type='review_item', entity_id=item.id, payload={'note': resolution_note}))
    db.commit()
    db.refresh(item)
    return item


def publish_opportunity(db: Session, opportunity_id: str, actor_user_id: str) -> Opportunity | None:
    opportunity = db.execute(select(Opportunity).where(Opportunity.id == opportunity_id)).scalar_one_or_none()
    if opportunity is None:
        return None
    opportunity.record_status = RecordStatus.PUBLISHED.value
    if opportunity.current_version is not None:
        opportunity.current_version.record_status = RecordStatus.PUBLISHED.value
    db.add(AuditEvent(actor_user_id=actor_user_id, action='opportunity.publish', entity_type='opportunity', entity_id=opportunity.id))
    db.commit()
    db.refresh(opportunity)
    return opportunity


def unpublish_opportunity(db: Session, opportunity_id: str, actor_user_id: str) -> Opportunity | None:
    opportunity = db.execute(select(Opportunity).where(Opportunity.id == opportunity_id)).scalar_one_or_none()
    if opportunity is None:
        return None
    opportunity.record_status = RecordStatus.UNPUBLISHED.value
    db.add(AuditEvent(actor_user_id=actor_user_id, action='opportunity.unpublish', entity_type='opportunity', entity_id=opportunity.id))
    db.commit()
    db.refresh(opportunity)
    return opportunity


def diff_opportunity(db: Session, opportunity_id: str) -> dict | None:
    opportunity = db.execute(select(Opportunity).where(Opportunity.id == opportunity_id)).scalar_one_or_none()
    if opportunity is None or opportunity.current_version is None:
        return None
    version = opportunity.current_version
    previous_version = db.execute(
        select(OpportunityVersion)
        .where(OpportunityVersion.opportunity_id == opportunity.id, OpportunityVersion.version_number < version.version_number)
        .order_by(OpportunityVersion.version_number.desc())
    ).scalars().first()
    current_payload = {
        'title': version.title,
        'short_description': version.short_description,
        'category': version.category,
        'benefit_type': version.benefit_type,
        'deadline_date': version.deadline_date.isoformat() if version.deadline_date else None,
        'official_links': version.official_links,
    }
    previous_payload = None
    changed_fields = version.changed_fields or []
    if previous_version is not None:
        previous_payload = {
            'title': previous_version.title,
            'short_description': previous_version.short_description,
            'category': previous_version.category,
            'benefit_type': previous_version.benefit_type,
            'deadline_date': previous_version.deadline_date.isoformat() if previous_version.deadline_date else None,
            'official_links': previous_version.official_links,
        }
    return {
        'opportunity_id': opportunity.id,
        'current': current_payload,
        'previous': previous_payload,
        'changed_fields': changed_fields,
    }


def test_rule(db: Session, rule_id: str) -> dict | None:
    rule = db.execute(select(OpportunityRule).where(OpportunityRule.id == rule_id)).scalar_one_or_none()
    if rule is None:
        return None
    results = run_rule_tests(rule)
    return {'rule_id': rule.id, 'passed': all(item['passed'] for item in results), 'results': results}


def list_rules(db: Session) -> list[dict]:
    rules = db.execute(select(OpportunityRule).order_by(OpportunityRule.created_at.desc())).scalars().all()
    payloads: list[dict] = []
    for rule in rules:
        version = rule.opportunity_version
        payloads.append(
            {
                'id': rule.id,
                'note': rule.note,
                'is_active': rule.is_active,
                'version_number': rule.version_number,
                'opportunity_title': version.title if version else 'Unknown opportunity',
                'fixture_count': len(rule.test_cases),
            }
        )
    return payloads
