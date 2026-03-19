from __future__ import annotations

from datetime import UTC, datetime

from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.db.migrations import current_revision, head_revision
from app.matching.service import run_rule_tests
from app.models import (
    AuditEvent,
    IngestionRun,
    MeasureFamily,
    MeasureFamilyDocument,
    NormalizedDocument,
    NotificationEvent,
    Opportunity,
    OpportunityRule,
    OpportunityVersion,
    RecordStatus,
    ReviewItem,
    ReviewStatus,
    SavedOpportunity,
    Source,
    SourceEndpoint,
)
from app.services.corpus import ensure_bootstrap_corpus, get_survey_coverage_payload, list_family_documents, list_measure_families
from app.services.family_opportunities import sync_measure_family_opportunities
from app.services.notifications import emit_opportunity_change_events, list_notification_history


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


def get_ingestion_run_detail(db: Session, run_id: str) -> dict | None:
    run = db.execute(select(IngestionRun).where(IngestionRun.id == run_id)).scalar_one_or_none()
    if run is None:
        return None
    endpoint = db.execute(select(SourceEndpoint).where(SourceEndpoint.id == run.source_endpoint_id)).scalar_one_or_none()
    source = endpoint.source if endpoint is not None else None
    diagnostics = run.diagnostics or {}
    return {
        'id': run.id,
        'source_endpoint_id': run.source_endpoint_id,
        'stage': run.stage,
        'status': run.status,
        'started_at': run.started_at,
        'finished_at': run.finished_at,
        'diagnostics': diagnostics,
        'endpoint_name': endpoint.name if endpoint is not None else 'Unknown endpoint',
        'endpoint_url': endpoint.url if endpoint is not None else '',
        'source_name': source.source_name if source is not None else 'Unknown source',
        'review_item_id': diagnostics.get('review_item_id'),
        'normalized_document_id': diagnostics.get('normalized_document_id'),
    }


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
    emit_opportunity_change_events(db, opportunity)
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
        'record_status': version.record_status,
        'version_number': version.version_number,
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
            'record_status': previous_version.record_status,
            'version_number': previous_version.version_number,
        }
    active_rule = next((rule for rule in version.rules if rule.is_active), None)
    rule_results = run_rule_tests(active_rule) if active_rule is not None else []
    return {
        'opportunity_id': opportunity.id,
        'opportunity_title': opportunity.title,
        'record_status': opportunity.record_status,
        'measure_family_slug': (version.legal_constraints or {}).get('measure_family_slug'),
        'active_rule_id': active_rule.id if active_rule is not None else None,
        'rule_test_summary': {
            'passed': all(item['passed'] for item in rule_results) if rule_results else False,
            'total': len(rule_results),
            'failed': sum(1 for item in rule_results if not item['passed']),
        },
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


def list_measure_family_payloads(db: Session) -> list[dict]:
    return list_measure_families(db)


def list_document_payloads(
    db: Session,
    *,
    source_domain: str | None = None,
    role: str | None = None,
    lifecycle_status: str | None = None,
    family_slug: str | None = None,
    document_id: str | None = None,
) -> list[dict]:
    return list_family_documents(
        db,
        source_domain=source_domain,
        role=role,
        lifecycle_status=lifecycle_status,
        family_slug=family_slug,
        document_id=document_id,
    )


def review_document(db: Session, document_id: str, payload, actor_user_id: str) -> dict | None:
    document = db.execute(select(NormalizedDocument).where(NormalizedDocument.id == document_id)).scalar_one_or_none()
    if document is None:
        return None

    if payload.mark_irrelevant:
        document.document_role = 'irrelevant'
        links = db.execute(select(MeasureFamilyDocument).where(MeasureFamilyDocument.normalized_document_id == document_id)).scalars().all()
        for link in links:
            db.delete(link)
    else:
        if payload.document_role:
            document.document_role = payload.document_role
        if payload.lifecycle_status:
            document.lifecycle_status = payload.lifecycle_status
        if payload.family_slug:
            family = db.execute(select(MeasureFamily).where(MeasureFamily.slug == payload.family_slug)).scalar_one_or_none()
            if family is None:
                return None
            link = db.execute(
                select(MeasureFamilyDocument).where(
                    MeasureFamilyDocument.measure_family_id == family.id,
                    MeasureFamilyDocument.normalized_document_id == document.id,
                )
            ).scalar_one_or_none()
            if payload.unlink_family:
                if link is not None:
                    db.delete(link)
            else:
                if link is None:
                    link = MeasureFamilyDocument(measure_family_id=family.id, normalized_document_id=document.id)
                    db.add(link)
                    db.flush()
                if payload.relationship_type:
                    link.relationship_type = payload.relationship_type
                link.is_primary_legal_basis = payload.is_primary_legal_basis
                link.is_primary_operational_doc = payload.is_primary_operational_doc

    db.add(
        AuditEvent(
            actor_user_id=actor_user_id,
            action='document.review',
            entity_type='normalized_document',
            entity_id=document.id,
            payload=payload.model_dump(),
        )
    )
    db.commit()

    updated = list_document_payloads(db, document_id=document.id)
    if updated:
        return updated[0]
    return {
        'id': document.id,
        'family_slug': 'unlinked',
        'family_title': 'Documento non collegato',
        'source_domain': '',
        'document_title': document.title,
        'canonical_url': document.canonical_url,
        'document_role': document.document_role,
        'lifecycle_status': document.lifecycle_status,
        'relationship_type': 'unlinked',
        'is_primary_legal_basis': False,
        'is_primary_operational_doc': False,
        'created_at': document.created_at,
        'metadata_json': document.metadata_json,
    }


def get_survey_coverage(db: Session) -> dict:
    return get_survey_coverage_payload(db)


def run_bootstrap(db: Session) -> dict:
    result = ensure_bootstrap_corpus(db)
    sync = sync_measure_family_opportunities(db)
    return {
        **result,
        'review_message': f"Bootstrap corpus aggiornato con famiglie di misura, documenti e copertura survey. Sync opportunita: create {sync['created']}, aggiornate {sync['updated']}, nascoste {sync['unpublished']}.",
    }


def get_integrity_payload(db: Session) -> dict:
    checks = [
        _duplicate_check(
            db,
            name='source_names',
            stmt=select(Source.source_name, func.count(Source.id)).group_by(Source.source_name).having(func.count(Source.id) > 1),
        ),
        _duplicate_check(
            db,
            name='source_endpoint_urls',
            stmt=select(SourceEndpoint.url, func.count(SourceEndpoint.id)).group_by(SourceEndpoint.url).having(func.count(SourceEndpoint.id) > 1),
        ),
        _duplicate_check(
            db,
            name='measure_family_documents',
            stmt=select(
                MeasureFamilyDocument.measure_family_id,
                MeasureFamilyDocument.normalized_document_id,
                func.count(MeasureFamilyDocument.id),
            )
            .group_by(MeasureFamilyDocument.measure_family_id, MeasureFamilyDocument.normalized_document_id)
            .having(func.count(MeasureFamilyDocument.id) > 1),
        ),
        _duplicate_check(
            db,
            name='saved_opportunities',
            stmt=select(
                SavedOpportunity.user_id,
                SavedOpportunity.opportunity_id,
                func.count(SavedOpportunity.id),
            )
            .group_by(SavedOpportunity.user_id, SavedOpportunity.opportunity_id)
            .having(func.count(SavedOpportunity.id) > 1),
        ),
        _duplicate_check(
            db,
            name='notification_dedupe_keys',
            stmt=select(NotificationEvent.dedupe_key, func.count(NotificationEvent.id))
            .group_by(NotificationEvent.dedupe_key)
            .having(func.count(NotificationEvent.id) > 1),
        ),
    ]
    current = current_revision()
    head = head_revision()
    return {
        'current_revision': current,
        'head_revision': head,
        'schema_current': current == head,
        'checks': checks,
    }


def get_notification_history_payload(db: Session, *, limit: int = 100) -> list[dict]:
    return list_notification_history(db, limit=limit)


def _duplicate_check(db: Session, *, name: str, stmt) -> dict:
    rows = db.execute(stmt).all()
    sample_values = [str(tuple(row[:-1]) if len(row) > 2 else row[0]) for row in rows[:5]]
    duplicate_row_count = sum(int(row[-1]) for row in rows)
    return {
        'name': name,
        'duplicate_group_count': len(rows),
        'duplicate_row_count': duplicate_row_count,
        'sample_values': sample_values,
    }
