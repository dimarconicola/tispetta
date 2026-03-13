from __future__ import annotations

from datetime import UTC, datetime
from typing import Any
from urllib.parse import urlsplit, urlunsplit

from sqlalchemy import select
from sqlalchemy.orm import Session, joinedload

from app.models import (
    FactValueKind,
    MeasureFamily,
    MeasureFamilyRequirement,
    Opportunity,
    OpportunityRule,
    OpportunityType,
    OpportunityVersion,
    ProfileFactCatalog,
    RecordStatus,
    RuleTestCase,
    VerificationStatus,
)


def sync_measure_family_opportunities(db: Session) -> dict[str, int]:
    families = db.execute(
        select(MeasureFamily)
        .options(
            joinedload(MeasureFamily.current_version).joinedload(MeasureFamilyVersion.requirements).joinedload(MeasureFamilyRequirement.fact),
            joinedload(MeasureFamily.documents).joinedload(MeasureFamilyDocument.document),
        )
        .order_by(MeasureFamily.title.asc())
    ).unique().scalars().all()
    fact_catalog = {
        fact.key: fact
        for fact in db.execute(select(ProfileFactCatalog)).scalars().all()
    }

    created = 0
    updated = 0
    unpublished = 0
    for family in families:
        result = sync_measure_family_opportunity(db, family, fact_catalog)
        if result == 'created':
            created += 1
        elif result == 'updated':
            updated += 1
        elif result == 'unpublished':
            unpublished += 1
    db.commit()
    return {'created': created, 'updated': updated, 'unpublished': unpublished}


def sync_measure_family_opportunity(
    db: Session,
    family: MeasureFamily,
    fact_catalog: dict[str, ProfileFactCatalog],
) -> str | None:
    version = family.current_version
    if version is None:
        return None

    opportunity = db.execute(select(Opportunity).where(Opportunity.slug == family.slug)).scalar_one_or_none()
    if family.is_regime_only or not family.is_actionable:
        if opportunity is not None and opportunity.record_status != RecordStatus.UNPUBLISHED.value:
            opportunity.record_status = RecordStatus.UNPUBLISHED.value
            return 'unpublished'
        return None

    payload = build_opportunity_payload(family)
    opportunity_record_status = payload['opportunity']['record_status']
    if opportunity is None:
        opportunity = Opportunity(
            slug=family.slug,
            title=payload['opportunity']['title'],
            short_description=payload['opportunity']['short_description'],
            category=payload['opportunity']['category'],
            geography_scope=payload['opportunity']['geography_scope'],
            benefit_type=payload['opportunity']['benefit_type'],
            deadline_date=payload['opportunity']['deadline_date'],
            estimated_value_max=payload['opportunity']['estimated_value_max'],
            record_status=opportunity_record_status,
            verification_status=payload['opportunity']['verification_status'],
        )
        db.add(opportunity)
        db.flush()
        create_opportunity_version_bundle(db, opportunity, family, payload, fact_catalog)
        return 'created'

    changed = apply_top_level_changes(opportunity, payload['opportunity'])
    current_version = opportunity.current_version
    new_version_payload = payload['version']
    current_version_payload = version_payload_from_model(current_version) if current_version is not None else None
    if current_version is None or current_version_payload != new_version_payload:
        create_opportunity_version_bundle(db, opportunity, family, payload, fact_catalog)
        changed = True

    if opportunity.record_status != opportunity_record_status:
        opportunity.record_status = opportunity_record_status
        changed = True
    if changed:
        return 'updated'
    return None


def create_opportunity_version_bundle(
    db: Session,
    opportunity: Opportunity,
    family: MeasureFamily,
    payload: dict[str, Any],
    fact_catalog: dict[str, ProfileFactCatalog],
) -> None:
    current_version = opportunity.current_version
    version_number = (current_version.version_number + 1) if current_version is not None else 1
    new_version = OpportunityVersion(
        opportunity_id=opportunity.id,
        version_number=version_number,
        **payload['version'],
    )
    db.add(new_version)
    db.flush()
    opportunity.current_version_id = new_version.id

    rule_json = build_rule_from_family(family)
    rule = OpportunityRule(
        opportunity_version_id=new_version.id,
        version_number=version_number,
        note=f'Generated from measure family {family.slug}',
        rule_json=rule_json,
        evidence_references=payload['version']['official_links'],
        is_active=True,
    )
    db.add(rule)
    db.flush()

    positive = build_fixture_payload(family, fact_catalog, scenario='positive')
    negative = build_fixture_payload(family, fact_catalog, scenario='negative')
    incomplete = build_fixture_payload(family, fact_catalog, scenario='incomplete')
    db.add_all(
        [
            RuleTestCase(rule_id=rule.id, name=f'{family.title} - positive', scenario_type='positive', profile_payload=positive, expected_status='confirmed'),
            RuleTestCase(rule_id=rule.id, name=f'{family.title} - negative', scenario_type='negative', profile_payload=negative, expected_status='not_eligible'),
            RuleTestCase(rule_id=rule.id, name=f'{family.title} - incomplete', scenario_type='incomplete', profile_payload=incomplete, expected_status='unclear'),
        ]
    )


def build_opportunity_payload(family: MeasureFamily) -> dict[str, dict[str, Any]]:
    version = family.current_version
    assert version is not None
    links = preferred_document_links(family)
    official_links = dedupe([link.document.canonical_url for link in links if link.document and link.document.canonical_url])
    source_documents = official_links.copy()
    live_links = [link for link in links if link.document and not is_seeded_document(link.document)]
    primary_document = next(
        (
            link.document
            for link in links
            if link.document is not None and link.relationship_type in {'primary_operational', 'primary_legal_basis'}
        ),
        None,
    )
    source_snapshot_id = primary_document.source_snapshot_id if primary_document is not None else None
    long_description = None
    if primary_document and primary_document.clean_text:
        long_description = primary_document.clean_text[:2500]
    if not long_description:
        long_description = ' '.join(item.get('quote', '') for item in version.evidence_snippets[:3]).strip() or None
    short_description = (
        next((item.get('quote') for item in version.evidence_snippets if item.get('quote')), None)
        or (primary_document.clean_text[:240] if primary_document and primary_document.clean_text else family.title)
    )
    category, opportunity_type = categorize_family(family)
    record_status = (
        RecordStatus.PUBLISHED.value
        if family.current_lifecycle_status in {'open_application', 'scheduled', 'evergreen_regime'}
        else RecordStatus.UNPUBLISHED.value
    )
    verification_status = VerificationStatus.AUTO_VERIFIED.value if live_links else VerificationStatus.REVIEWED.value
    evidence = dedupe_evidence(normalize_version_evidence(version.evidence_snippets or [], official_links, family.slug) + build_document_evidence(links))
    application_mode = version.application_mechanics.get('channel') if version.application_mechanics else None
    deadline_type = 'rolling' if application_mode else None
    benefit_type = humanize_benefit_kind(version.benefit_kind)
    now = datetime.now(UTC)

    top_level = {
        'title': family.title,
        'short_description': short_description,
        'category': category,
        'geography_scope': version.geography,
        'benefit_type': benefit_type,
        'deadline_date': None,
        'estimated_value_max': None,
        'last_checked_at': now,
        'record_status': record_status,
        'verification_status': verification_status,
    }
    version_payload = {
        'source_snapshot_id': source_snapshot_id,
        'title': family.title,
        'normalized_title': family.slug,
        'short_description': short_description,
        'long_description': long_description,
        'opportunity_type': opportunity_type,
        'category': category,
        'subcategory': None,
        'issuer_name': family.operator_name,
        'issuer_type': 'public_agency',
        'country': 'IT',
        'region': None,
        'geography_scope': version.geography,
        'target_entities': version.beneficiary_entity_types,
        'target_sectors': version.sector_constraints,
        'company_stage': version.age_or_time_constraints,
        'company_size_constraints': version.size_constraints,
        'demographic_constraints': {'person_specific_constraints': version.person_specific_constraints} if version.person_specific_constraints else None,
        'legal_constraints': {
            'legal_form_constraints': version.legal_form_constraints,
            'regime_status_constraints': version.regime_status_constraints,
            'measure_family_slug': family.slug,
            'lifecycle_status': family.current_lifecycle_status,
            'provenance': 'measure_family',
        },
        'eligibility_inputs_required': [item.fact.key for item in version.requirements if item.fact is not None],
        'exclusions': ['advisor'],
        'benefit_type': benefit_type,
        'benefit_value_type': version.benefit_magnitude_model,
        'estimated_value_min': None,
        'estimated_value_max': None,
        'funding_rate': None,
        'deadline_type': deadline_type,
        'deadline_date': None,
        'application_window_start': None,
        'application_window_end': None,
        'application_mode': application_mode,
        'required_documents': version.required_documents,
        'official_links': official_links,
        'source_documents': source_documents,
        'evidence_snippets': evidence,
        'extraction_confidence': 0.94 if live_links else 0.76,
        'verification_status': verification_status,
        'record_status': record_status,
        'changed_fields': ['measure_family_sync'],
        'last_checked_at': now,
    }
    return {'opportunity': top_level, 'version': version_payload}


def preferred_document_links(family: MeasureFamily) -> list[MeasureFamilyDocument]:
    links = sorted(family.documents, key=lambda item: item.created_at, reverse=True)
    live_by_url: dict[str, MeasureFamilyDocument] = {}
    retained: list[MeasureFamilyDocument] = []
    for link in links:
        document = link.document
        if document is None or is_seeded_document(document):
            continue
        canonical = canonicalize_url(document.canonical_url or '')
        if canonical and canonical in live_by_url:
            continue
        live_by_url[canonical] = link
        retained.append(link)
    if retained:
        return retained
    return links


def build_rule_from_family(family: MeasureFamily) -> dict[str, Any]:
    version = family.current_version
    assert version is not None
    required: list[dict[str, Any]] = []
    boosters: list[dict[str, Any]] = []
    disqualifiers: list[dict[str, Any]] = [{'eq': {'field': 'profile_type', 'value': 'advisor'}}]
    for requirement in version.requirements:
        if requirement.fact is None:
            continue
        condition = build_condition(requirement.fact, requirement.expected_values)
        if condition is None:
            continue
        if requirement.requirement_mode == 'ranking_or_booster':
            boosters.append(condition)
        else:
            required.append(condition)
    return {
        'required': required,
        'disqualifiers': disqualifiers,
        'boosters': boosters,
        'tolerated_missing': [],
    }


def build_condition(fact: ProfileFactCatalog, expected_values: list[str] | None) -> dict[str, Any] | None:
    if fact.value_kind == FactValueKind.BOOLEAN.value:
        strict = [value for value in normalize_expected_values(fact, expected_values or []) if value is not None]
    else:
        strict = [value for value in (expected_values or []) if value not in {'not_sure', 'mixed'}]
    if expected_values and not strict:
        return {'exists': {'field': fact.key}}
    if not expected_values:
        return {'exists': {'field': fact.key}}
    if len(strict) == 1:
        return {'eq': {'field': fact.key, 'value': strict[0]}}
    return {'in': {'field': fact.key, 'value': strict}}


def build_fixture_payload(
    family: MeasureFamily,
    fact_catalog: dict[str, ProfileFactCatalog],
    *,
    scenario: str,
) -> dict[str, Any]:
    version = family.current_version
    assert version is not None
    payload: dict[str, Any] = {}
    ordered_requirements = sorted(
        [item for item in version.requirements if item.fact is not None],
        key=lambda item: 0 if item.requirement_mode == 'entity_hard_requirement' else 1,
    )
    first_required_key: str | None = None
    for requirement in ordered_requirements:
        fact = requirement.fact
        assert fact is not None
        first_required_key = first_required_key or fact.key
        payload[fact.key] = choose_positive_value(fact, requirement.expected_values)

    for key, fact in fact_catalog.items():
        if key in payload:
            continue
        default = fallback_value_for_fact(fact)
        if default is not None:
            payload[key] = default

    if scenario == 'negative' and first_required_key is not None:
        payload[first_required_key] = choose_negative_value(fact_catalog[first_required_key], payload[first_required_key])
    if scenario == 'incomplete' and first_required_key is not None:
        payload[first_required_key] = None
    return payload


def choose_positive_value(fact: ProfileFactCatalog, expected_values: list[str] | None) -> Any:
    if fact.value_kind == FactValueKind.BOOLEAN.value:
        normalized = normalize_expected_values(fact, expected_values or [])
        strict = [value for value in normalized if value is not None]
        return strict[0] if strict else True
    if expected_values:
        for value in expected_values:
            if value not in {'not_sure', 'mixed'}:
                return value
        return expected_values[0]
    if fact.options:
        return fact.options[0]
    return fallback_value_for_fact(fact)


def choose_negative_value(fact: ProfileFactCatalog, current_value: Any) -> Any:
    if fact.value_kind == FactValueKind.BOOLEAN.value:
        return not bool(current_value)
    for option in fact.options or []:
        if option != current_value and option not in {'not_sure', 'mixed'}:
            return option
    if fact.key == 'profile_type':
        return 'advisor'
    if fact.key == 'main_operating_region':
        return 'Lombardia' if current_value != 'Lombardia' else 'Sicilia'
    return '__mismatch__'


def fallback_value_for_fact(fact: ProfileFactCatalog) -> Any:
    if fact.value_kind == FactValueKind.BOOLEAN.value:
        return False
    if fact.options:
        for option in fact.options:
            if option not in {'not_sure', 'mixed'}:
                return option
        return fact.options[0]
    return None


def normalize_expected_values(fact: ProfileFactCatalog, expected_values: list[str]) -> list[Any]:
    if fact.value_kind != FactValueKind.BOOLEAN.value:
        return expected_values
    normalized: list[Any] = []
    for value in expected_values:
        if value == 'true':
            normalized.append(True)
        elif value == 'false':
            normalized.append(False)
        elif value in {'not_sure', 'mixed'}:
            normalized.append(None)
        else:
            normalized.append(value)
    return normalized


def apply_top_level_changes(opportunity: Opportunity, payload: dict[str, Any]) -> bool:
    changed = False
    for key, value in payload.items():
        if getattr(opportunity, key) != value:
            setattr(opportunity, key, value)
            changed = True
    return changed


def version_payload_from_model(version: OpportunityVersion | None) -> dict[str, Any] | None:
    if version is None:
        return None
    return {
        'source_snapshot_id': version.source_snapshot_id,
        'title': version.title,
        'normalized_title': version.normalized_title,
        'short_description': version.short_description,
        'long_description': version.long_description,
        'opportunity_type': version.opportunity_type,
        'category': version.category,
        'subcategory': version.subcategory,
        'issuer_name': version.issuer_name,
        'issuer_type': version.issuer_type,
        'country': version.country,
        'region': version.region,
        'geography_scope': version.geography_scope,
        'target_entities': version.target_entities,
        'target_sectors': version.target_sectors,
        'company_stage': version.company_stage,
        'company_size_constraints': version.company_size_constraints,
        'demographic_constraints': version.demographic_constraints,
        'legal_constraints': version.legal_constraints,
        'eligibility_inputs_required': version.eligibility_inputs_required,
        'exclusions': version.exclusions,
        'benefit_type': version.benefit_type,
        'benefit_value_type': version.benefit_value_type,
        'estimated_value_min': version.estimated_value_min,
        'estimated_value_max': version.estimated_value_max,
        'funding_rate': version.funding_rate,
        'deadline_type': version.deadline_type,
        'deadline_date': version.deadline_date,
        'application_window_start': version.application_window_start,
        'application_window_end': version.application_window_end,
        'application_mode': version.application_mode,
        'required_documents': version.required_documents,
        'official_links': version.official_links,
        'source_documents': version.source_documents,
        'evidence_snippets': version.evidence_snippets,
        'extraction_confidence': version.extraction_confidence,
        'verification_status': version.verification_status,
        'record_status': version.record_status,
        'changed_fields': version.changed_fields,
        'last_checked_at': version.last_checked_at,
    }


def categorize_family(family: MeasureFamily) -> tuple[str, str]:
    version = family.current_version
    assert version is not None
    if version.benefit_kind == 'hiring_incentive':
        return 'hiring_incentive', OpportunityType.HIRING_INCENTIVE.value
    if version.benefit_kind == 'tax_credit':
        return 'tax_incentive', OpportunityType.TAX_INCENTIVE.value
    if family.slug.startswith('simest_'):
        return 'export_incentive', OpportunityType.EXPORT.value
    if version.benefit_kind in {'voucher'}:
        return 'grants', OpportunityType.GRANT.value
    if family.slug.startswith('transizione_'):
        return 'digitization_incentive', OpportunityType.DIGITIZATION.value
    if version.benefit_kind == 'mutuo_agevolato':
        return 'subsidized_loan', OpportunityType.SUBSIDIZED_LOAN.value
    if version.benefit_kind in {'finanziamento_agevolato', 'self_employment_support', 'direct_bonus'}:
        return 'grants', OpportunityType.GRANT.value
    return 'grants', OpportunityType.GRANT.value


def humanize_benefit_kind(value: str | None) -> str:
    if not value:
        return 'agevolazione'
    return value.replace('_', ' ')


def build_document_evidence(links: list[MeasureFamilyDocument]) -> list[dict[str, str]]:
    evidence: list[dict[str, str]] = []
    for link in links:
        document = link.document
        if document is None or not document.canonical_url or not document.clean_text:
            continue
        evidence.append(
            {
                'source': document.canonical_url,
                'field': document.document_role,
                'quote': document.clean_text[:240],
            }
        )
    return evidence[:6]


def dedupe(items: list[str]) -> list[str]:
    deduped: list[str] = []
    for item in items:
        if item and item not in deduped:
            deduped.append(item)
    return deduped


def dedupe_evidence(items: list[dict[str, str]]) -> list[dict[str, str]]:
    deduped: list[dict[str, str]] = []
    seen: set[tuple[str, str, str]] = set()
    for item in items:
        key = (item.get('source', ''), item.get('field', ''), item.get('quote', ''))
        if key in seen:
            continue
        seen.add(key)
        deduped.append(item)
    return deduped[:8]


def normalize_version_evidence(items: list[dict[str, str]], official_links: list[str], family_slug: str) -> list[dict[str, str]]:
    source = official_links[0] if official_links else f'measure-family://{family_slug}'
    normalized: list[dict[str, str]] = []
    for item in items:
        normalized.append(
            {
                'source': item.get('source') or source,
                'field': item.get('field') or 'summary',
                'quote': item.get('quote') or '',
            }
        )
    return normalized


def is_seeded_document(document) -> bool:
    return bool((document.metadata_json or {}).get('seeded'))


def canonicalize_url(url: str) -> str:
    if not url:
        return url
    parsed = urlsplit(url)
    return urlunsplit((parsed.scheme, parsed.netloc, parsed.path, parsed.query, ''))


# Late imports to avoid circular reference strings becoming hard to follow.
from app.models import MeasureFamilyDocument, MeasureFamilyVersion  # noqa: E402
