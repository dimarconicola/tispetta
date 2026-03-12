from pydantic import BaseModel, EmailStr

from app.schemas.common import ApiModel


class MagicLinkRequest(BaseModel):
    email: EmailStr


class MagicLinkResponse(ApiModel):
    message: str
    preview_url: str | None = None


class SessionUser(ApiModel):
    id: str
    email: str
    role: str
    locale: str
