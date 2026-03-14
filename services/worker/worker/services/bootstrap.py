from __future__ import annotations

from collections.abc import Iterable
from datetime import UTC, datetime
from urllib.parse import urljoin, urlparse, urlsplit, urlunsplit

from bs4 import BeautifulSoup
from sqlalchemy import select
from sqlalchemy.orm import Session, joinedload

from app.models import (
    DocumentRole,
    MeasureFamily,
    MeasureFamilyDocument,
    MeasureFamilyVersion,
    MeasureLifecycleStatus,
    NormalizedDocument,
    SourceEndpoint,
    SourceSnapshot,
)
from app.services.corpus import recompute_survey_coverage
from worker.clients.storage import read_snapshot
from worker.services.ingestion import normalize_snapshot, upsert_snapshot


def classify_document_role(url: str, title: str | None, clean_text: str) -> str:
    lowered_url = url.lower()
    blob = f'{title or ""}\n{clean_text[:3000]}'.lower()
    if 'normattiva.it' in lowered_url:
        return DocumentRole.LEGAL_BASIS.value
    if 'gazzettaufficiale.it' in lowered_url:
        return DocumentRole.NEWS_OR_STATUS_UPDATE.value
    if 'assistenza.clienti.gse.it' in lowered_url or 'transizione-5-0' in lowered_url:
        return DocumentRole.FAQ_OR_OPERATIONAL_GUIDE.value
    if any(keyword in lowered_url for keyword in ['faq', 'domande', 'guide', 'guida']):
        return DocumentRole.FAQ_OR_OPERATIONAL_GUIDE.value
    if any(keyword in lowered_url for keyword in ['portale', 'portal', 'login', 'area-riservata', 'servizi-per-te']):
        return DocumentRole.APPLICATION_PORTAL.value
    if any(keyword in lowered_url for keyword in ['circolare', 'decreto', 'provvedimento']):
        return DocumentRole.MINISTERIAL_CIRCULAR.value
    if any(keyword in blob for keyword in ['allegato', 'modulo', 'template', 'fac-simile']):
        return DocumentRole.FORMS_AND_TEMPLATES.value
    if any(keyword in blob for keyword in ['bonus', 'incentivo', 'credito', 'finanziamento', 'voucher', 'startup', 'innovative', 'assunzion', 'transizione']):
        return DocumentRole.OPERATOR_MEASURE_PAGE.value
    return DocumentRole.IRRELEVANT.value


def infer_lifecycle_status(url: str, clean_text: str) -> str:
    lowered = f'{url}\n{clean_text[:2000]}'.lower()
    if any(keyword in lowered for keyword in ['regime', 'sezione speciale', 'status', 'startup innovativa', 'pmi innovativa']):
        return MeasureLifecycleStatus.EVERGREEN_REGIME.value
    if any(keyword in lowered for keyword in ['sportello aperto', 'domande aperte', 'presentare la domanda', 'operativo']):
        return MeasureLifecycleStatus.OPEN_APPLICATION.value
    if any(keyword in lowered for keyword in ['in arrivo', 'di prossima apertura', 'sarà operativo', 'sara operativo']):
        return MeasureLifecycleStatus.SCHEDULED.value
    if any(keyword in lowered for keyword in ['sospeso', 'temporaneamente sospeso']):
        return MeasureLifecycleStatus.PAUSED.value
    if any(keyword in lowered for keyword in ['esaurite', 'fondi esauriti']):
        return MeasureLifecycleStatus.EXHAUSTED.value
    if any(keyword in lowered for keyword in ['chiuso', 'terminato']):
        return MeasureLifecycleStatus.CLOSED.value
    return MeasureLifecycleStatus.HISTORICAL_REFERENCE.value


def link_document_to_family(
    db: Session,
    family: MeasureFamily,
    document: NormalizedDocument,
    *,
    relationship_type: str,
) -> None:
    existing_links = db.execute(
        select(MeasureFamilyDocument).where(
            MeasureFamilyDocument.measure_family_id == family.id,
            MeasureFamilyDocument.normalized_document_id == document.id,
        )
    ).scalars().all()
    existing = existing_links[0] if existing_links else None
    for duplicate in existing_links[1:]:
        db.delete(duplicate)
    if existing is None:
        existing = MeasureFamilyDocument(
            measure_family_id=family.id,
            normalized_document_id=document.id,
            relationship_type=relationship_type,
            is_primary_legal_basis=relationship_type == 'primary_legal_basis',
            is_primary_operational_doc=relationship_type == 'primary_operational',
        )
        db.add(existing)
    else:
        existing.relationship_type = relationship_type
        existing.is_primary_legal_basis = relationship_type == 'primary_legal_basis'
        existing.is_primary_operational_doc = relationship_type == 'primary_operational'
    if not is_seeded_document(document):
        remove_seeded_placeholders(db, family, document)


def is_seeded_document(document: NormalizedDocument) -> bool:
    return bool((document.metadata_json or {}).get('seeded'))


def remove_seeded_placeholders(db: Session, family: MeasureFamily, document: NormalizedDocument) -> None:
    linked = db.execute(
        select(MeasureFamilyDocument)
        .options(joinedload(MeasureFamilyDocument.document))
        .where(MeasureFamilyDocument.measure_family_id == family.id)
    ).scalars().all()
    for item in linked:
        linked_document = item.document
        if linked_document is None or linked_document.id == document.id:
            continue
        if not is_seeded_document(linked_document):
            duplicate_live = (
                canonicalize_url(linked_document.canonical_url or '') == canonicalize_url(document.canonical_url or '')
                and item.relationship_type in {'primary_legal_basis', 'primary_operational'}
            )
            if duplicate_live:
                db.delete(item)
            continue
        same_url = bool(
            document.canonical_url
            and canonicalize_url(linked_document.canonical_url or '') == canonicalize_url(document.canonical_url)
        )
        same_primary_role = (
            item.relationship_type in {'primary_legal_basis', 'primary_operational'}
            and item.relationship_type
            == ('primary_legal_basis' if document.document_role == DocumentRole.LEGAL_BASIS.value else 'primary_operational')
        )
        if same_url or same_primary_role:
            db.delete(item)


def discover_same_domain_links(url: str, html_text: str, allowed_keywords: Iterable[str]) -> list[str]:
    parsed = urlparse(url)
    domain = parsed.netloc
    soup = BeautifulSoup(html_text, 'html.parser')
    discovered: list[str] = []
    for link in soup.find_all('a', href=True):
        candidate = canonicalize_url(urljoin(url, link['href']))
        parsed_candidate = urlparse(candidate)
        if parsed_candidate.netloc != domain:
            continue
        lowered = candidate.lower()
        if not any(keyword.lower() in lowered for keyword in allowed_keywords):
            continue
        if candidate not in discovered:
            discovered.append(candidate)
    return discovered[:6]


def ensure_endpoint(db: Session, family: MeasureFamily, url: str, title: str | None = None) -> SourceEndpoint:
    url = canonicalize_url(url)
    endpoint = db.execute(select(SourceEndpoint).where(SourceEndpoint.url == url)).scalar_one_or_none()
    if endpoint is not None:
        return endpoint
    from app.services.corpus import get_source_by_domain

    resolved_source = get_source_by_domain(db, urlparse(url).netloc.replace('www.', ''))
    endpoint = SourceEndpoint(
        source_id=resolved_source.id,
        name=title or family.title,
        url=url,
        document_type='measure_family_document',
        status='active',
    )
    db.add(endpoint)
    db.commit()
    db.refresh(endpoint)
    return endpoint


def crawl_curated_links(db: Session, family: MeasureFamily) -> list[NormalizedDocument]:
    version = family.current_version
    if version is None:
        return []
    documents: list[NormalizedDocument] = []
    for url in version.entrypoint_urls:
        endpoint = ensure_endpoint(db, family, url, family.title)
        try:
            snapshot = upsert_snapshot(db, endpoint, _ephemeral_run(db, endpoint.id))
        except Exception:
            continue
        if snapshot is None:
            latest = db.execute(
                select(NormalizedDocument)
                .join(SourceSnapshot, NormalizedDocument.source_snapshot_id == SourceSnapshot.id)
                .join(SourceEndpoint, SourceSnapshot.source_endpoint_id == SourceEndpoint.id)
                .where(SourceEndpoint.url == endpoint.url)
                .order_by(NormalizedDocument.created_at.desc())
            ).scalars().first()
            if latest is not None:
                documents.append(latest)
            continue
        document = normalize_snapshot(db, snapshot)
        document.canonical_url = canonicalize_url(endpoint.url)
        document.document_role = classify_document_role(endpoint.url, document.title, document.clean_text)
        document.lifecycle_status = infer_lifecycle_status(endpoint.url, document.clean_text)
        relationship_type = choose_relationship_type(db, family, document.document_role)
        link_document_to_family(db, family, document, relationship_type=relationship_type)
        documents.append(document)

        raw_html = read_snapshot(snapshot.storage_path).decode('utf-8', errors='ignore') if snapshot.storage_path else ''
        discovered = discover_same_domain_links(endpoint.url, raw_html, version.allowed_path_keywords or [])
        for discovered_url in discovered:
            discovered_endpoint = ensure_endpoint(db, family, discovered_url, family.title)
            try:
                discovered_snapshot = upsert_snapshot(db, discovered_endpoint, _ephemeral_run(db, discovered_endpoint.id))
            except Exception:
                continue
            if discovered_snapshot is None:
                continue
            discovered_document = normalize_snapshot(db, discovered_snapshot)
            discovered_document.canonical_url = canonicalize_url(discovered_endpoint.url)
            discovered_document.document_role = classify_document_role(discovered_endpoint.url, discovered_document.title, discovered_document.clean_text)
            discovered_document.lifecycle_status = infer_lifecycle_status(discovered_endpoint.url, discovered_document.clean_text)
            has_primary_operational = db.execute(
                select(MeasureFamilyDocument).where(
                    MeasureFamilyDocument.measure_family_id == family.id,
                    MeasureFamilyDocument.relationship_type == 'primary_operational',
                )
            ).scalars().first() is not None
            discovered_relationship = choose_relationship_type(
                db,
                family,
                discovered_document.document_role,
                has_primary_operational=has_primary_operational,
            )
            link_document_to_family(db, family, discovered_document, relationship_type=discovered_relationship)
            documents.append(discovered_document)
    db.commit()
    return documents


def link_legal_basis(db: Session, family: MeasureFamily) -> int:
    linked = 0
    version = family.current_version
    if version is None:
        return linked
    for url in version.legal_basis_references:
        endpoint = ensure_endpoint(db, family, url, family.title)
        try:
            snapshot = upsert_snapshot(db, endpoint, _ephemeral_run(db, endpoint.id))
        except Exception:
            continue
        if snapshot is None:
            continue
        document = normalize_snapshot(db, snapshot)
        document.canonical_url = canonicalize_url(endpoint.url)
        document.document_role = DocumentRole.LEGAL_BASIS.value if 'normattiva' in endpoint.url else DocumentRole.NEWS_OR_STATUS_UPDATE.value
        document.lifecycle_status = MeasureLifecycleStatus.EVERGREEN_REGIME.value
        link_document_to_family(db, family, document, relationship_type='primary_legal_basis')
        linked += 1
    db.commit()
    return linked


def extract_measure_requirements(db: Session, family: MeasureFamily) -> dict:
    version = family.current_version
    if version is None:
        return {'documents': 0, 'legal_basis_references': 0}
    docs = db.execute(
        select(MeasureFamilyDocument)
        .options(joinedload(MeasureFamilyDocument.document))
        .where(MeasureFamilyDocument.measure_family_id == family.id)
    ).scalars().all()
    legal_basis_urls = []
    evidence_snippets = list(version.evidence_snippets or [])
    for link in docs:
        document = link.document
        if document is None:
            continue
        if document.document_role == DocumentRole.LEGAL_BASIS.value and document.canonical_url:
            legal_basis_urls.append(document.canonical_url)
        if document.canonical_url and document.clean_text:
            evidence_snippets.append(
                {
                    'field': document.document_role,
                    'quote': document.clean_text[:240],
                    'source': document.canonical_url,
                }
            )
    version.legal_basis_references = sorted(set(legal_basis_urls)) or version.legal_basis_references
    version.evidence_snippets = evidence_snippets[:8]
    version.verification_timestamp = datetime.now(UTC)
    version.changed_fields = sorted(set((version.changed_fields or []) + ['bootstrap_refresh']))
    db.commit()
    return {'documents': len(docs), 'legal_basis_references': len(version.legal_basis_references or [])}


def refresh_family_bootstrap(db: Session, family: MeasureFamily) -> dict:
    crawled = crawl_curated_links(db, family)
    linked_legal_basis = link_legal_basis(db, family)
    extracted = extract_measure_requirements(db, family)
    recompute_survey_coverage(db)
    return {
        'family': family.slug,
        'documents_crawled': len(crawled),
        'legal_basis_linked': linked_legal_basis,
        'requirements_refreshed': extracted,
    }


def _ephemeral_run(db: Session, endpoint_id: str):
    from app.models import IngestionRun, IngestionStage

    run = IngestionRun(
        source_endpoint_id=endpoint_id,
        stage=IngestionStage.FETCH.value,
        status='started',
        diagnostics={'bootstrap': True},
    )
    db.add(run)
    db.commit()
    db.refresh(run)
    return run


def canonicalize_url(url: str) -> str:
    if not url:
        return url
    parsed = urlsplit(url)
    return urlunsplit((parsed.scheme, parsed.netloc, parsed.path, parsed.query, ''))


def choose_relationship_type(
    db: Session,
    family: MeasureFamily,
    document_role: str,
    *,
    has_primary_operational: bool | None = None,
) -> str:
    if document_role == DocumentRole.LEGAL_BASIS.value:
        return 'primary_legal_basis'
    if document_role not in {
        DocumentRole.OPERATOR_MEASURE_PAGE.value,
        DocumentRole.FAQ_OR_OPERATIONAL_GUIDE.value,
        DocumentRole.APPLICATION_PORTAL.value,
        DocumentRole.FORMS_AND_TEMPLATES.value,
    }:
        return 'supporting_document'
    if has_primary_operational is None:
        has_primary_operational = db.execute(
            select(MeasureFamilyDocument).where(
                MeasureFamilyDocument.measure_family_id == family.id,
                MeasureFamilyDocument.relationship_type == 'primary_operational',
            )
        ).scalars().first() is not None
    return 'supporting_document' if has_primary_operational else 'primary_operational'
