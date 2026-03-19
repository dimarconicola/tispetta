from datetime import datetime

from pydantic import BaseModel

from app.schemas.common import ApiModel


class SourceCreate(BaseModel):
    source_name: str
    source_type: str
    authority_level: str
    crawl_method: str
    crawl_frequency: str
    trust_level: str
    region: str
    status: str = 'active'


class SourceRead(ApiModel):
    id: str
    source_name: str
    source_type: str
    authority_level: str
    crawl_method: str
    crawl_frequency: str
    trust_level: str
    region: str
    status: str
    created_at: datetime


class IngestionRunRead(ApiModel):
    id: str
    source_endpoint_id: str
    stage: str
    status: str
    started_at: datetime
    finished_at: datetime | None = None
    diagnostics: dict | None = None


class IngestionRunDetailRead(IngestionRunRead):
    endpoint_name: str
    endpoint_url: str
    source_name: str
    review_item_id: str | None = None
    normalized_document_id: str | None = None
