from datetime import datetime

from pydantic import BaseModel

from app.schemas.common import ApiModel
from app.schemas.opportunity import OpportunityCard


class ProfileQuestionImpactCounts(ApiModel):
    clarification_opportunity_count: int = 0
    blocking_opportunity_count: int = 0
    upgrade_opportunity_count: int = 0


class ProfileQuestion(ApiModel):
    key: str
    label: str
    step: int
    kind: str
    required: bool
    options: list[str] | None = None
    helper_text: str | None = None
    audience: list[str] | None = None
    module: str | None = None
    sensitive: bool = False
    depends_on: dict | None = None
    ask_when_measure_families: list[str] | None = None
    why_needed: str | None = None
    coverage_weight: float = 0
    ambiguity_reduction_score: float = 0
    priority: int = 0
    impact_counts: ProfileQuestionImpactCounts = ProfileQuestionImpactCounts()
    blocking_opportunity_count: int = 0
    upgrade_opportunity_count: int = 0


class ProfileQuestionModule(ApiModel):
    key: str
    title: str
    description: str
    questions: list[ProfileQuestion]


class ProfileQuestionProgress(ApiModel):
    personal_answered: int = 0
    personal_total: int = 0
    business_answered: int = 0
    business_total: int = 0
    core_answered: int = 0
    core_total: int = 0
    strategic_answered: int = 0
    strategic_total: int = 0
    conditional_answered: int = 0
    conditional_total: int = 0
    completeness_score: float = 0
    blocked_opportunity_count: int = 0
    upgradable_opportunity_count: int = 0


class OnboardingStep(ApiModel):
    key: str
    label: str
    status: str


class OnboardingJourney(ApiModel):
    steps: list[OnboardingStep]
    current_step: str
    next_step: str | None = None
    has_business_context: bool = False
    active_module_key: str | None = None


class ProfileBusinessContext(ApiModel):
    answered: bool = False
    enabled: bool = False
    profile_type: str | None = None


class StrategicModule(ApiModel):
    key: str
    title: str
    description: str
    why_this_module_matters: str | None = None
    questions: list[ProfileQuestion]
    clarification_count: int = 0
    upgrade_count: int = 0


class ProfileResultsSummary(ApiModel):
    ready: bool = False
    total_matches: int = 0
    blocked_count: int = 0
    profile_state: str
    top_matches: list[OpportunityCard] = []
    why_now: list[str] = []
    next_focus_labels: list[str] = []


class ProfileQuestionResponse(ApiModel):
    recommended_step: str
    progress_summary: ProfileQuestionProgress
    modules: list[ProfileQuestionModule]
    journey: OnboardingJourney
    personal_core_questions: list[ProfileQuestion]
    business_context: ProfileBusinessContext
    business_core_questions: list[ProfileQuestion]
    strategic_modules: list[StrategicModule]
    results_summary: ProfileResultsSummary


class ProfilePayload(BaseModel):
    user_type: str | None = None
    region: str | None = None
    province: str | None = None
    age_range: str | None = None
    business_exists: bool | None = None
    legal_entity_type: str | None = None
    company_age_band: str | None = None
    company_size_band: str | None = None
    revenue_band: str | None = None
    sector_code_or_category: str | None = None
    founder_attributes: dict | None = None
    hiring_intent: bool | None = None
    innovation_intent: bool | None = None
    sustainability_intent: bool | None = None
    export_intent: bool | None = None
    incorporation_status: str | None = None
    startup_stage: str | None = None
    goals: list[str] | None = None
    fact_values: dict | None = None


class ProfileResponse(ProfilePayload, ApiModel):
    id: str
    user_id: str
    country: str
    profile_completeness_score: float
    updated_at: datetime
