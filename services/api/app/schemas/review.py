from datetime import datetime

from pydantic import BaseModel

from app.schemas.common import ApiModel


class ReviewResolve(BaseModel):
    resolution_note: str


class ReviewItemRead(ApiModel):
    id: str
    item_type: str
    status: str
    related_entity_type: str
    related_entity_id: str
    title: str
    description: str | None = None
    payload: dict | None = None
    created_at: datetime
    resolved_at: datetime | None = None


class RuleTestResult(ApiModel):
    rule_id: str
    passed: bool
    results: list[dict]
