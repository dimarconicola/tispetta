from datetime import datetime

from app.schemas.common import ApiModel


class EvidenceSnippet(ApiModel):
    source: str
    quote: str
    field: str


class MatchQuestionHint(ApiModel):
    key: str
    label: str
    kind: str
    why_this_question_matters_now: str | None = None
    blocking_opportunity_count: int = 0
    upgrade_opportunity_count: int = 0


class MatchBreakdown(ApiModel):
    status: str | None = None
    matched_reasons: list[str] = []
    blocking_missing_facts: list[MatchQuestionHint] = []
    refinement_facts: list[MatchQuestionHint] = []
    next_best_questions: list[MatchQuestionHint] = []
    why_matched: list[str] = []
    what_blocks_confirmation: list[str] = []


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
    why_now: str | None = None
    blocking_question_keys: list[str] = []
    match_reasons: list[str] = []
    blocking_missing_labels: list[str] = []


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
    match_breakdown: MatchBreakdown = MatchBreakdown()
