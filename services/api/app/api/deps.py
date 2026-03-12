from fastapi import Cookie, Depends, Header, HTTPException, status
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.core.config import get_settings
from app.core.security import parse_session_token
from app.db.session import get_db
from app.models import Role, User

settings = get_settings()


def _extract_session_token(
    cookie_token: str | None,
    header_token: str | None,
    authorization: str | None,
) -> str | None:
    if header_token:
        return header_token
    if cookie_token:
        return cookie_token
    if authorization and authorization.lower().startswith('bearer '):
        return authorization.split(' ', 1)[1].strip()
    return None


def get_optional_current_user(
    session_token_cookie: str | None = Cookie(default=None, alias=settings.session_cookie_name),
    x_session_token: str | None = Header(default=None, alias='X-Session-Token'),
    authorization: str | None = Header(default=None),
    db: Session = Depends(get_db),
) -> User | None:
    session_token = _extract_session_token(session_token_cookie, x_session_token, authorization)
    if not session_token:
        return None
    payload = parse_session_token(session_token)
    if payload is None:
        return None
    return db.execute(select(User).where(User.id == payload['sub'])).scalar_one_or_none()


def get_current_user(user: User | None = Depends(get_optional_current_user)) -> User:
    if user is None:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail='Authentication required')
    return user


def get_admin_user(user: User = Depends(get_current_user)) -> User:
    if user.role != Role.ADMIN.value:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail='Admin access required')
    return user
