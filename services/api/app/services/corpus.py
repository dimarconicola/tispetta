from __future__ import annotations

from collections import defaultdict
from datetime import UTC, datetime
import hashlib
from urllib.parse import urlparse, urlsplit, urlunsplit

from sqlalchemy import select
from sqlalchemy.orm import Session, joinedload

from app.bootstrap_manifest import MEASURE_FAMILY_SPECS, PROFILE_FACT_SPECS, SOURCE_REGISTRY
from app.models import (
    DocumentRole,
    MeasureFamily,
    MeasureFamilyDocument,
    MeasureFamilyRequirement,
    MeasureFamilyVersion,
    MeasureLifecycleStatus,
    NormalizedDocument,
    Profile,
    ProfileFactCatalog,
    ProfileFactValue,
    RequirementMode,
    Source,
    SourceEndpoint,
    SourceSnapshot,
    SurveyCoverageSnapshot,
    SurveyModule,
)

CORE_FACT_KEYS = [
    'profile_type',
    'activity_stage',
    'legal_form_bucket',
    'main_operating_region',
    'company_age_or_formation_window',
    'size_band',
    'sector_macro_category',
    'innovation_regime_status',
]


def ensure_bootstrap_corpus(db: Session) -> dict[str, int]:
    from app.services.family_opportunities import sync_measure_family_opportunities

    facts_seeded = seed_profile_fact_catalog(db)
    ensure_source_registry(db)
    families_seeded, documents_seeded = seed_measure_families(db)
    coverage = recompute_survey_coverage(db)
    opportunity_sync = sync_measure_family_opportunities(db)
    return {
        'facts_seeded': facts_seeded,
        'measure_families_seeded': families_seeded,
        'documents_seeded': documents_seeded,
        'coverage_rows': len(coverage['rows']),
        'family_opportunities_created': opportunity_sync['created'],
        'family_opportunities_updated': opportunity_sync['updated'],
    }


def seed_profile_fact_catalog(db: Session) -> int:
    seeded = 0
    for spec in PROFILE_FACT_SPECS:
        fact = db.execute(select(ProfileFactCatalog).where(ProfileFactCatalog.key == spec['key'])).scalar_one_or_none()
        if fact is None:
            fact = ProfileFactCatalog(
                key=spec['key'],
                label=spec['label'],
                module=spec['module'],
                value_kind=spec['value_kind'],
                options=spec.get('options'),
                helper_text=spec.get('helper_text'),
                why_needed=spec.get('why_needed'),
                stable=spec.get('stable', True),
                sensitive=spec.get('sensitive', False),
                required_in_core=spec.get('required_in_core', False),
                depends_on=spec.get('depends_on'),
                sort_order=spec.get('sort_order', 0),
            )
            db.add(fact)
            seeded += 1
        else:
            fact.label = spec['label']
            fact.module = spec['module']
            fact.value_kind = spec['value_kind']
            fact.options = spec.get('options')
            fact.helper_text = spec.get('helper_text')
            fact.why_needed = spec.get('why_needed')
            fact.stable = spec.get('stable', True)
            fact.sensitive = spec.get('sensitive', False)
            fact.required_in_core = spec.get('required_in_core', False)
            fact.depends_on = spec.get('depends_on')
            fact.sort_order = spec.get('sort_order', 0)
    db.commit()
    return seeded


def ensure_source_registry(db: Session) -> None:
    for spec in SOURCE_REGISTRY:
        source = db.execute(select(Source).where(Source.source_name == spec['name'])).scalar_one_or_none()
        if source is None:
            source = Source(
                source_name=spec['name'],
                source_type=spec['source_type'],
                authority_level=spec['authority_level'],
                crawl_method=spec['crawl_method'],
                crawl_frequency=spec['crawl_frequency'],
                trust_level=spec['trust_level'],
                region=spec['region'],
                status='active',
            )
            db.add(source)
    db.commit()


def get_source_by_domain(db: Session, domain: str) -> Source:
    mapping = {item['domain']: item['name'] for item in SOURCE_REGISTRY}
    source_name = mapping.get(domain, domain)
    source = db.execute(select(Source).where(Source.source_name == source_name)).scalar_one_or_none()
    if source is None:
        source = Source(
            source_name=source_name,
            source_type='website',
            authority_level='tier_1',
            crawl_method='html',
            crawl_frequency='daily',
            trust_level='high',
            region='Italy',
            status='active',
        )
        db.add(source)
        db.commit()
        db.refresh(source)
    return source


def seed_measure_families(db: Session) -> tuple[int, int]:
    seeded_families = 0
    seeded_documents = 0
    facts_by_key = {
        item.key: item
        for item in db.execute(select(ProfileFactCatalog)).scalars().all()
    }

    for spec in MEASURE_FAMILY_SPECS:
        family = db.execute(select(MeasureFamily).where(MeasureFamily.slug == spec['slug'])).scalar_one_or_none()
        if family is None:
            family = MeasureFamily(
                slug=spec['slug'],
                title=spec['title'],
                operator_name=spec['operator_name'],
                source_domain=spec['source_domain'],
                is_regime_only=spec['is_regime_only'],
                is_actionable=spec['is_actionable'],
                current_lifecycle_status=spec['current_lifecycle_status'],
            )
            db.add(family)
            db.flush()
            seeded_families += 1
        else:
            family.title = spec['title']
            family.operator_name = spec['operator_name']
            family.source_domain = spec['source_domain']
            family.is_regime_only = spec['is_regime_only']
            family.is_actionable = spec['is_actionable']
            family.current_lifecycle_status = spec['current_lifecycle_status']

        version = db.execute(
            select(MeasureFamilyVersion)
            .where(MeasureFamilyVersion.measure_family_id == family.id)
            .order_by(MeasureFamilyVersion.version_number.desc())
        ).scalars().first()
        if version is None:
            version = MeasureFamilyVersion(
                measure_family_id=family.id,
                version_number=1,
                title=spec['title'],
                operator_name=spec['operator_name'],
                benefit_kind=spec['benefit_kind'],
                benefit_magnitude_model=spec['benefit_magnitude_model'],
                lifecycle_status=spec['current_lifecycle_status'],
                geography=spec['geography'],
                legal_basis_references=[
                    item['url']
                    for item in spec['documents']
                    if item['role'] in (DocumentRole.LEGAL_BASIS.value, DocumentRole.IMPLEMENTING_DECREE.value)
                ],
                beneficiary_entity_types=spec['beneficiary_entity_types'],
                size_constraints=spec['size_constraints'],
                sector_constraints=spec['sector_constraints'],
                legal_form_constraints=spec['legal_form_constraints'],
                regime_status_constraints=spec['regime_status_constraints'],
                age_or_time_constraints=spec['age_or_time_constraints'],
                person_specific_constraints=spec['person_specific_constraints'],
                project_specific_constraints=spec['project_specific_constraints'],
                application_mechanics=spec['application_mechanics'],
                required_documents=spec['required_documents'],
                evidence_snippets=spec['evidence_snippets'],
                entrypoint_urls=spec['entrypoint_urls'],
                allowed_path_keywords=spec['allowed_path_keywords'],
                changed_fields=['initial_bootstrap'],
            )
            db.add(version)
            db.flush()
        else:
            version.title = spec['title']
            version.operator_name = spec['operator_name']
            version.benefit_kind = spec['benefit_kind']
            version.benefit_magnitude_model = spec['benefit_magnitude_model']
            version.lifecycle_status = spec['current_lifecycle_status']
            version.geography = spec['geography']
            version.legal_basis_references = [
                item['url']
                for item in spec['documents']
                if item['role'] in (DocumentRole.LEGAL_BASIS.value, DocumentRole.IMPLEMENTING_DECREE.value)
            ]
            version.beneficiary_entity_types = spec['beneficiary_entity_types']
            version.size_constraints = spec['size_constraints']
            version.sector_constraints = spec['sector_constraints']
            version.legal_form_constraints = spec['legal_form_constraints']
            version.regime_status_constraints = spec['regime_status_constraints']
            version.age_or_time_constraints = spec['age_or_time_constraints']
            version.person_specific_constraints = spec['person_specific_constraints']
            version.project_specific_constraints = spec['project_specific_constraints']
            version.application_mechanics = spec['application_mechanics']
            version.required_documents = spec['required_documents']
            version.evidence_snippets = spec['evidence_snippets']
            version.entrypoint_urls = spec['entrypoint_urls']
            version.allowed_path_keywords = spec['allowed_path_keywords']
            version.verification_timestamp = datetime.now(UTC)

        family.current_version_id = version.id

        existing_requirements = {
            item.fact.key: item
            for item in db.execute(
                select(MeasureFamilyRequirement)
                .options(joinedload(MeasureFamilyRequirement.fact))
                .where(MeasureFamilyRequirement.measure_family_version_id == version.id)
            ).scalars().all()
        }
        for requirement_spec in spec['requirements']:
            fact = facts_by_key[requirement_spec['fact_key']]
            requirement = existing_requirements.get(requirement_spec['fact_key'])
            if requirement is None:
                requirement = MeasureFamilyRequirement(
                    measure_family_version_id=version.id,
                    fact_catalog_id=fact.id,
                    requirement_mode=requirement_spec['requirement_mode'],
                    expected_values=requirement_spec.get('expected_values'),
                    notes=requirement_spec.get('notes'),
                )
                db.add(requirement)
            else:
                requirement.requirement_mode = requirement_spec['requirement_mode']
                requirement.expected_values = requirement_spec.get('expected_values')
                requirement.notes = requirement_spec.get('notes')

        for doc_spec in spec['documents']:
            normalized_document = ensure_document_seed(db, doc_spec)
            link = db.execute(
                select(MeasureFamilyDocument).where(
                    MeasureFamilyDocument.measure_family_id == family.id,
                    MeasureFamilyDocument.normalized_document_id == normalized_document.id,
                )
            ).scalar_one_or_none()
            if link is None:
                link = MeasureFamilyDocument(
                    measure_family_id=family.id,
                    normalized_document_id=normalized_document.id,
                    relationship_type=doc_spec['relationship_type'],
                    is_primary_legal_basis=doc_spec['relationship_type'] == 'primary_legal_basis',
                    is_primary_operational_doc=doc_spec['relationship_type'] == 'primary_operational',
                )
                db.add(link)
                seeded_documents += 1
            else:
                link.relationship_type = doc_spec['relationship_type']
                link.is_primary_legal_basis = doc_spec['relationship_type'] == 'primary_legal_basis'
                link.is_primary_operational_doc = doc_spec['relationship_type'] == 'primary_operational'
    db.commit()
    return seeded_families, seeded_documents


def ensure_document_seed(db: Session, doc_spec: dict) -> NormalizedDocument:
    url = doc_spec['url']
    domain = urlparse(url).netloc.replace('www.', '')
    source = get_source_by_domain(db, domain)
    endpoint = db.execute(select(SourceEndpoint).where(SourceEndpoint.url == url)).scalars().first()
    if endpoint is None:
        endpoint = SourceEndpoint(
            source_id=source.id,
            name=doc_spec['title'],
            url=url,
            document_type=doc_spec['role'],
            status='active',
        )
        db.add(endpoint)
        db.flush()

    checksum = hashlib.sha256(f"{url}:{doc_spec['title']}".encode('utf-8')).hexdigest()
    snapshot = db.execute(
        select(SourceSnapshot).where(
            SourceSnapshot.source_endpoint_id == endpoint.id,
            SourceSnapshot.checksum == checksum,
        )
    ).scalar_one_or_none()
    if snapshot is None:
        snapshot = SourceSnapshot(
            source_endpoint_id=endpoint.id,
            checksum=checksum,
            http_status=200,
            headers={'seeded': True},
            storage_path=f"seed://{domain}/{checksum}",
            content_type='text/html',
            diagnostics={'seeded': True},
        )
        db.add(snapshot)
        db.flush()

    document = db.execute(
        select(NormalizedDocument).where(NormalizedDocument.source_snapshot_id == snapshot.id)
    ).scalar_one_or_none()
    if document is None:
        document = NormalizedDocument(
            source_snapshot_id=snapshot.id,
            title=doc_spec['title'],
            canonical_url=url,
            clean_text=doc_spec['summary'],
            metadata_json={'seeded': True, 'source_domain': domain},
            structural_sections=[{'heading': doc_spec['title'], 'text': doc_spec['summary']}],
            document_type='measure_family_document',
            document_role=doc_spec['role'],
            lifecycle_status=doc_spec['lifecycle_status'],
        )
        db.add(document)
    else:
        document.title = doc_spec['title']
        document.canonical_url = url
        document.clean_text = doc_spec['summary']
        document.metadata_json = {'seeded': True, 'source_domain': domain}
        document.structural_sections = [{'heading': doc_spec['title'], 'text': doc_spec['summary']}]
        document.document_type = 'measure_family_document'
        document.document_role = doc_spec['role']
        document.lifecycle_status = doc_spec['lifecycle_status']
    db.flush()
    return document


def profile_fact_map(profile: Profile | None) -> dict[str, str]:
    if profile is None:
        return {}
    values = {
        item.fact.key: normalize_fact_value(item.value_json.get('value'))
        for item in profile.fact_values
        if item.fact is not None
    }
    return {key: value for key, value in values.items() if value not in (None, '')}


def normalize_fact_value(value):
    if isinstance(value, bool):
        return 'true' if value else 'false'
    return value


def build_profile_questions(db: Session, profile: Profile | None) -> list[dict]:
    if db.execute(select(ProfileFactCatalog.id)).first() is None:
        ensure_bootstrap_corpus(db)

    fact_values = profile_fact_map(profile)
    active_audiences = active_question_audiences(fact_values)
    coverage = get_latest_coverage_snapshot(db)
    coverage_rows = {row['fact_key']: row for row in coverage.get('rows', [])}

    facts = db.execute(select(ProfileFactCatalog).order_by(ProfileFactCatalog.sort_order.asc())).scalars().all()
    questions: list[dict] = []
    for fact in facts:
        row = coverage_rows.get(fact.key, {})
        ask_when = row.get('ask_when_measure_families', [])
        if not should_ask_fact(fact, fact_values, ask_when):
            continue
        module = fact.module
        step = 1 if module == SurveyModule.CORE_ENTITY.value else 2 if module == SurveyModule.STRATEGIC_INTENT.value else 3
        audience = sorted(derive_audience_for_fact(db, fact.key))
        if module != SurveyModule.CORE_ENTITY.value and audience and set(audience).isdisjoint(active_audiences):
            continue
        questions.append(
            {
                'key': fact.key,
                'label': fact.label,
                'step': step,
                'kind': fact.value_kind,
                'required': fact.required_in_core,
                'options': fact.options,
                'helper_text': fact.helper_text,
                'audience': audience or None,
                'module': module,
                'sensitive': fact.sensitive,
                'depends_on': fact.depends_on,
                'ask_when_measure_families': ask_when,
                'why_needed': fact.why_needed,
                'coverage_weight': row.get('coverage_weight', 0.0),
                'ambiguity_reduction_score': row.get('ambiguity_reduction_score', 0.0),
            }
        )
    return questions


def active_question_audiences(fact_values: dict[str, str]) -> set[str]:
    audiences = {'persona_fisica'}
    profile_type = fact_values.get('profile_type')
    if profile_type and profile_type != 'persona_fisica':
        audiences.add(profile_type)
    return audiences


def should_ask_fact(fact: ProfileFactCatalog, fact_values: dict[str, str], ask_when_measure_families: list[str]) -> bool:
    if fact.module == SurveyModule.CORE_ENTITY.value:
        return True
    if fact.module == SurveyModule.STRATEGIC_INTENT.value:
        return True
    if fact.key in fact_values:
        return True
    if not ask_when_measure_families:
        return False
    depends_on = fact.depends_on or {}
    if not depends_on:
        return True
    for key, expected_values in depends_on.items():
        current = fact_values.get(key)
        if current in expected_values:
            return True
    return False


def derive_audience_for_fact(db: Session, fact_key: str) -> set[str]:
    if fact_key in {'main_operating_region', 'employment_type', 'isee_bracket', 'family_composition', 'figli_a_carico_count', 'persona_fisica_age_band'}:
        return {'persona_fisica'}
    items = db.execute(
        select(MeasureFamilyRequirement)
        .options(joinedload(MeasureFamilyRequirement.family_version))
        .join(MeasureFamilyRequirement.fact)
        .where(ProfileFactCatalog.key == fact_key)
    ).scalars().all()
    audience: set[str] = set()
    for item in items:
        version = item.family_version
        if version:
            audience.update(version.beneficiary_entity_types or [])
    return audience


def recompute_survey_coverage(db: Session) -> dict:
    facts = db.execute(select(ProfileFactCatalog).order_by(ProfileFactCatalog.sort_order.asc())).scalars().all()
    families = db.execute(
        select(MeasureFamily)
        .options(joinedload(MeasureFamily.current_version).joinedload(MeasureFamilyVersion.requirements).joinedload(MeasureFamilyRequirement.fact))
    ).unique().scalars().all()

    active_families = [
        family
        for family in families
        if family.current_version is not None
        and family.current_lifecycle_status not in (MeasureLifecycleStatus.CLOSED.value, MeasureLifecycleStatus.HISTORICAL_REFERENCE.value)
    ]
    rows = []
    for fact in facts:
        linked = []
        for family in active_families:
            version = family.current_version
            if version is None:
                continue
            requirement = next((item for item in version.requirements if item.fact and item.fact.key == fact.key), None)
            if requirement is not None:
                linked.append((family, requirement))

        hard_requirement_count = sum(
            1 for _, requirement in linked if requirement.requirement_mode == RequirementMode.ENTITY_HARD_REQUIREMENT.value
        )
        project_requirement_count = sum(
            1 for _, requirement in linked if requirement.requirement_mode == RequirementMode.PROJECT_HARD_REQUIREMENT.value
        )
        person_requirement_count = sum(
            1 for _, requirement in linked if requirement.requirement_mode == RequirementMode.PERSON_SPECIFIC_REQUIREMENT.value
        )
        ranking_requirement_count = sum(
            1 for _, requirement in linked if requirement.requirement_mode == RequirementMode.RANKING_OR_BOOSTER.value
        )
        active_count = len(linked)
        coverage_weight = round(
            hard_requirement_count * 1.0
            + project_requirement_count * 0.85
            + person_requirement_count * 0.95
            + ranking_requirement_count * 0.45,
            2,
        )
        ambiguity_reduction_score = round(
            coverage_weight * (1.1 if fact.stable else 0.8) * (0.9 if fact.sensitive else 1.0),
            2,
        )
        rows.append(
            {
                'fact_key': fact.key,
                'label': fact.label,
                'module': fact.module,
                'sensitive': fact.sensitive,
                'stable': fact.stable,
                'coverage_weight': coverage_weight,
                'ambiguity_reduction_score': ambiguity_reduction_score,
                'active_measure_family_count': active_count,
                'hard_requirement_count': hard_requirement_count,
                'project_requirement_count': project_requirement_count,
                'person_requirement_count': person_requirement_count,
                'ranking_requirement_count': ranking_requirement_count,
                'ask_when_measure_families': [family.slug for family, _ in linked],
                'depends_on': fact.depends_on,
            }
        )

    payload = {
        'total_measure_families': len(families),
        'total_active_measure_families': len(active_families),
        'rows': rows,
    }
    snapshot = SurveyCoverageSnapshot(snapshot_key='latest', payload=payload)
    db.add(snapshot)
    db.commit()
    return payload


def get_latest_coverage_snapshot(db: Session) -> dict:
    snapshot = db.execute(
        select(SurveyCoverageSnapshot).where(SurveyCoverageSnapshot.snapshot_key == 'latest').order_by(SurveyCoverageSnapshot.created_at.desc())
    ).scalars().first()
    if snapshot is None:
        payload = recompute_survey_coverage(db)
        return payload
    return snapshot.payload


def list_measure_families(db: Session) -> list[dict]:
    ensure_bootstrap_corpus(db)
    families = db.execute(
        select(MeasureFamily)
        .options(
            joinedload(MeasureFamily.current_version).joinedload(MeasureFamilyVersion.requirements),
            joinedload(MeasureFamily.documents),
        )
        .order_by(MeasureFamily.title.asc())
    ).unique().scalars().all()
    payloads = []
    for family in families:
        version = family.current_version
        if version is None:
            continue
        documents = preferred_family_document_links(family.documents)
        payloads.append(
            {
                'id': family.id,
                'slug': family.slug,
                'title': family.title,
                'operator_name': family.operator_name,
                'source_domain': family.source_domain,
                'is_regime_only': family.is_regime_only,
                'is_actionable': family.is_actionable,
                'current_lifecycle_status': family.current_lifecycle_status,
                'benefit_kind': version.benefit_kind,
                'benefit_magnitude_model': version.benefit_magnitude_model,
                'geography': version.geography,
                'legal_basis_references': version.legal_basis_references,
                'beneficiary_entity_types': version.beneficiary_entity_types,
                'requirements_count': len(version.requirements),
                'documents_count': len(documents),
                'primary_legal_basis_count': sum(1 for item in documents if item.is_primary_legal_basis),
                'primary_operational_count': sum(1 for item in documents if item.is_primary_operational_doc),
                'verification_timestamp': version.verification_timestamp,
            }
        )
    return payloads


def list_family_documents(
    db: Session,
    *,
    source_domain: str | None = None,
    role: str | None = None,
    lifecycle_status: str | None = None,
    family_slug: str | None = None,
    document_id: str | None = None,
) -> list[dict]:
    ensure_bootstrap_corpus(db)
    links = db.execute(
        select(MeasureFamilyDocument)
        .options(
            joinedload(MeasureFamilyDocument.family),
            joinedload(MeasureFamilyDocument.document),
        )
        .order_by(MeasureFamilyDocument.created_at.desc())
    ).scalars().all()

    payloads = []
    for link in preferred_family_document_links(links):
        family = link.family
        document = link.document
        if family is None or document is None:
            continue
        if source_domain and family.source_domain != source_domain:
            continue
        if role and document.document_role != role:
            continue
        if lifecycle_status and document.lifecycle_status != lifecycle_status:
            continue
        if family_slug and family.slug != family_slug:
            continue
        if document_id and document.id != document_id:
            continue
        payloads.append(
            {
                'id': document.id,
                'family_slug': family.slug,
                'family_title': family.title,
                'source_domain': family.source_domain,
                'document_title': document.title,
                'canonical_url': document.canonical_url,
                'document_role': document.document_role,
                'lifecycle_status': document.lifecycle_status,
                'relationship_type': link.relationship_type,
                'is_primary_legal_basis': link.is_primary_legal_basis,
                'is_primary_operational_doc': link.is_primary_operational_doc,
                'created_at': document.created_at,
                'metadata_json': document.metadata_json,
            }
        )
    return payloads


def get_survey_coverage_payload(db: Session) -> dict:
    ensure_bootstrap_corpus(db)
    snapshot = db.execute(
        select(SurveyCoverageSnapshot).where(SurveyCoverageSnapshot.snapshot_key == 'latest').order_by(SurveyCoverageSnapshot.created_at.desc())
    ).scalars().first()
    if snapshot is None:
        recompute_survey_coverage(db)
        snapshot = db.execute(
            select(SurveyCoverageSnapshot).where(SurveyCoverageSnapshot.snapshot_key == 'latest').order_by(SurveyCoverageSnapshot.created_at.desc())
        ).scalars().first()
    assert snapshot is not None
    payload = snapshot.payload
    return {
        'id': snapshot.id,
        'snapshot_key': snapshot.snapshot_key,
        'created_at': snapshot.created_at,
        'total_measure_families': payload.get('total_measure_families', 0),
        'total_active_measure_families': payload.get('total_active_measure_families', 0),
        'rows': payload.get('rows', []),
    }


def get_profile_fact_values_for_profile(db: Session, profile: Profile | None) -> dict[str, object]:
    if profile is None:
        return {}
    facts = db.execute(
        select(ProfileFactValue)
        .options(joinedload(ProfileFactValue.fact))
        .where(ProfileFactValue.profile_id == profile.id)
    ).scalars().all()
    return {item.fact.key: item.value_json.get('value') for item in facts if item.fact is not None}


def preferred_family_document_links(links: list[MeasureFamilyDocument]) -> list[MeasureFamilyDocument]:
    live_by_url: dict[tuple[str, str], MeasureFamilyDocument] = {}
    retained: list[MeasureFamilyDocument] = []

    for link in sorted(links, key=lambda item: item.created_at, reverse=True):
        family = link.family
        document = link.document
        if family is None or document is None:
            continue
        if is_seeded_document(document):
            continue
        canonical = canonicalize_url(document.canonical_url or '')
        key = (family.id, canonical)
        if key in live_by_url:
            continue
        live_by_url[key] = link
        retained.append(link)

    if retained:
        return sorted(retained, key=lambda item: item.created_at, reverse=True)

    return sorted(links, key=lambda item: item.created_at, reverse=True)


def is_seeded_document(document: NormalizedDocument) -> bool:
    return bool((document.metadata_json or {}).get('seeded'))


def canonicalize_url(url: str) -> str:
    if not url:
        return url
    parsed = urlsplit(url)
    return urlunsplit((parsed.scheme, parsed.netloc, parsed.path, parsed.query, ''))
