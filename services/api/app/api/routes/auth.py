from fastapi import APIRouter, Depends, HTTPException, Query, Response
from sqlalchemy.orm import Session

from app.api.deps import get_current_user
from app.core.config import get_settings
from app.db.session import get_db
from app.schemas.auth import (
    MagicLinkExchangeRequest,
    MagicLinkExchangeResponse,
    MagicLinkRequest,
    MagicLinkResponse,
    SessionUser,
)
from app.services.auth import consume_magic_link, create_session_for_user, request_magic_link

router = APIRouter(prefix='/v1/auth', tags=['auth'])
public_router = APIRouter(prefix='/v1', tags=['auth'])
settings = get_settings()


@router.post('/request-magic-link', response_model=MagicLinkResponse)
def request_magic_link_endpoint(payload: MagicLinkRequest, db: Session = Depends(get_db)) -> MagicLinkResponse:
    try:
        preview_url = request_magic_link(db, payload.email, payload.redirect_to)
    except RuntimeError as exc:
        raise HTTPException(status_code=503, detail='Unable to deliver magic link email') from exc
    return MagicLinkResponse(message='Magic link generated', preview_url=preview_url if settings.environment != 'production' else None)


@router.post('/exchange-magic-link', response_model=MagicLinkExchangeResponse)
def exchange_magic_link(payload: MagicLinkExchangeRequest, db: Session = Depends(get_db)) -> MagicLinkExchangeResponse:
    user, redirect_to = consume_magic_link(db, payload.token)
    if user is None:
        raise HTTPException(status_code=400, detail='Magic link invalid or expired')
    return MagicLinkExchangeResponse(
        redirect_to=redirect_to or '/onboarding',
        session_token=create_session_for_user(user),
    )


@router.get('/verify-magic-link')
def verify_magic_link(token: str = Query(...), db: Session = Depends(get_db)) -> Response:
    user, redirect_to = consume_magic_link(db, token)
    if user is None:
        raise HTTPException(status_code=400, detail='Magic link invalid or expired')
    session_token = create_session_for_user(user)
    response = Response(status_code=302)
    response.headers['Location'] = f'{settings.app_base_url}{redirect_to or "/onboarding"}'
    response.headers['Cache-Control'] = 'no-store'
    response.set_cookie(
        key=settings.session_cookie_name,
        value=session_token,
        max_age=settings.session_max_age_seconds,
        httponly=True,
        samesite=settings.session_cookie_same_site,
        secure=settings.cookie_secure(),
        domain=settings.cookie_domain(),
        path='/',
    )
    return response


@router.post('/sign-out')
def sign_out() -> Response:
    response = Response(content='signed out')
    response.headers['Cache-Control'] = 'no-store'
    response.delete_cookie(settings.session_cookie_name, path='/', domain=settings.cookie_domain())
    return response


@public_router.get('/me', response_model=SessionUser)
def me(user = Depends(get_current_user)) -> SessionUser:
    return SessionUser.model_validate(user)
