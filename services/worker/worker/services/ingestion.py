from __future__ import annotations

from dataclasses import dataclass
from datetime import UTC, datetime
import hashlib
import re

from bs4 import BeautifulSoup
import httpx
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models import (
    IngestionRun,
    IngestionStage,
    NormalizedDocument,
    ReviewItem,
    ReviewItemType,
    SourceEndpoint,
    SourceSnapshot,
)
from worker.clients.storage import persist_snapshot, read_snapshot


@dataclass
class ExtractionCandidate:
    title: str | None
    short_description: str | None
    official_links: list[str]
    evidence_snippets: list[dict]
    confidence: float
    document_type: str


DEADLINE_RE = re.compile(r'(\d{1,2}[/-]\d{1,2}[/-]\d{2,4})')


def fetch_endpoint(endpoint: SourceEndpoint) -> tuple[bytes, str, str]:
    response = httpx.get(endpoint.url, timeout=15.0, follow_redirects=True)
    response.raise_for_status()
    content = response.content
    checksum = hashlib.sha256(content).hexdigest()
    content_type = response.headers.get('content-type', 'text/html')
    return content, checksum, content_type


def upsert_snapshot(db: Session, endpoint: SourceEndpoint, run: IngestionRun) -> SourceSnapshot | None:
    content, checksum, content_type = fetch_endpoint(endpoint)
    existing = db.execute(
        select(SourceSnapshot)
        .where(SourceSnapshot.source_endpoint_id == endpoint.id, SourceSnapshot.checksum == checksum)
        .order_by(SourceSnapshot.fetched_at.desc())
    ).scalar_one_or_none()
    if existing is not None:
        run.status = 'skipped'
        run.stage = IngestionStage.COMPLETE.value
        run.finished_at = datetime.now(UTC)
        run.diagnostics = {'reason': 'checksum_unchanged'}
        db.commit()
        return None

    suffix = f"{datetime.now(UTC).strftime('%Y%m%d%H%M%S')}.{'pdf' if 'pdf' in content_type else 'html'}"
    storage_path = persist_snapshot(endpoint.id, suffix, content, content_type=content_type)
    snapshot = SourceSnapshot(
        source_endpoint_id=endpoint.id,
        checksum=checksum,
        http_status=200,
        headers={'content_type': content_type},
        storage_path=storage_path,
        content_type=content_type,
        diagnostics={'size_bytes': len(content)},
    )
    db.add(snapshot)
    db.flush()
    run.stage = IngestionStage.NORMALIZE.value
    db.commit()
    return snapshot


def normalize_snapshot(db: Session, snapshot: SourceSnapshot) -> NormalizedDocument:
    raw = read_snapshot(snapshot.storage_path) if snapshot.storage_path else b''
    content_type = snapshot.content_type or 'text/html'
    if 'pdf' in content_type:
        clean_text = raw.decode('utf-8', errors='ignore')
        title = snapshot.storage_path.rsplit('/', 1)[-1] if snapshot.storage_path else 'document.pdf'
        sections = [{'heading': 'PDF import', 'text': clean_text[:2000]}]
    else:
        html = raw.decode('utf-8', errors='ignore')
        soup = BeautifulSoup(html, 'html.parser')
        title_tag = soup.find('title') or soup.find('h1')
        paragraphs = [element.get_text(' ', strip=True) for element in soup.find_all(['p', 'li'])]
        clean_text = '\n'.join(paragraphs)
        sections = [
            {'heading': heading.get_text(' ', strip=True), 'text': heading.find_next('p').get_text(' ', strip=True) if heading.find_next('p') else ''}
            for heading in soup.find_all(['h1', 'h2'])[:8]
        ]
        title = title_tag.get_text(' ', strip=True) if title_tag else None
    document_type = classify_document(title or '', clean_text)
    document = NormalizedDocument(
        source_snapshot_id=snapshot.id,
        title=title,
        clean_text=clean_text,
        metadata_json={'content_type': content_type},
        structural_sections=sections,
        document_type=document_type,
    )
    db.add(document)
    db.commit()
    db.refresh(document)
    return document


def classify_document(title: str, clean_text: str) -> str:
    blob = f'{title}\n{clean_text[:2000]}'.lower()
    if any(keyword in blob for keyword in ['bando', 'incentivo', 'voucher', 'finanziamento', 'credito d', 'contributo']):
        return 'opportunity_page'
    if any(keyword in blob for keyword in ['faq', 'domande frequenti']):
        return 'faq'
    if any(keyword in blob for keyword in ['guida', 'manuale', 'policy']):
        return 'policy_page'
    return 'irrelevant'


def extract_candidate(endpoint: SourceEndpoint, document: NormalizedDocument) -> ExtractionCandidate:
    text = document.clean_text
    title = document.title
    short_description = next((line for line in text.splitlines() if len(line) > 80), text[:220] if text else None)
    official_links = [endpoint.url]
    evidence_snippets = []
    if short_description:
        evidence_snippets.append({'source': endpoint.url, 'field': 'summary', 'quote': short_description[:240]})
    deadline_match = DEADLINE_RE.search(text)
    if deadline_match:
        evidence_snippets.append({'source': endpoint.url, 'field': 'deadline', 'quote': deadline_match.group(1)})
    confidence = 0.35
    if title:
        confidence += 0.2
    if short_description:
        confidence += 0.2
    if document.document_type == 'opportunity_page':
        confidence += 0.2
    if deadline_match:
        confidence += 0.05
    return ExtractionCandidate(
        title=title,
        short_description=short_description,
        official_links=official_links,
        evidence_snippets=evidence_snippets,
        confidence=min(confidence, 0.95),
        document_type=document.document_type,
    )


def route_candidate_for_review(db: Session, endpoint: SourceEndpoint, candidate: ExtractionCandidate) -> ReviewItem | None:
    if candidate.document_type == 'irrelevant':
        return None
    item_type = ReviewItemType.PUBLISH_PENDING.value if candidate.confidence >= 0.9 else ReviewItemType.LOW_CONFIDENCE.value
    review_item = ReviewItem(
        item_type=item_type,
        related_entity_type='source_endpoint',
        related_entity_id=endpoint.id,
        title=candidate.title or f'Nuovo documento da {endpoint.name}',
        description='Candidate opportunity estratta dal worker e pronta per revisione.',
        payload={
            'short_description': candidate.short_description,
            'official_links': candidate.official_links,
            'evidence_snippets': candidate.evidence_snippets,
            'confidence': candidate.confidence,
            'document_type': candidate.document_type,
        },
    )
    db.add(review_item)
    db.commit()
    db.refresh(review_item)
    return review_item
