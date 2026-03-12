from datetime import datetime

from app.schemas.common import ApiModel


class EvidenceSnippet(ApiModel):
    source: str
    quote: str
    field: str


class OpportunityCard(ApiModel):
    id: str
    slug: str
    title: str
    short_description: str
    category: str
    geography_scope: str
    benefit_type: str
    match_status: str | None = None
    match_score: float | None = None
    user_visible_reasoning: str | None = None
    missing_fields: list[str] = []
    deadline_date: datetime | None = None
    estimated_value_max: float | None = None
    last_checked_at: datetime
    is_saved: bool = False


class OpportunityDetail(OpportunityCard):
    long_description: str | None = None
    issuer_name: str
    official_links: list[str]
    source_documents: list[str]
    evidence_snippets: list[EvidenceSnippet]
    required_documents: list[str] | None = None
    next_steps: list[str]
    why_this_matches: list[str]
    what_is_missing: list[str]
    verification_status: str
