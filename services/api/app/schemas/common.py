from datetime import datetime
from typing import Any

from pydantic import BaseModel, ConfigDict


class ApiModel(BaseModel):
    model_config = ConfigDict(from_attributes=True)


class ApiMessage(ApiModel):
    message: str


class PaginatedResponse(ApiModel):
    items: list[Any]
    total: int
