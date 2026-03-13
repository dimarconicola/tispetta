from datetime import datetime

from pydantic import BaseModel

from app.schemas.common import ApiModel


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
