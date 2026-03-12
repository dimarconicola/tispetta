from fastapi import APIRouter, Depends, HTTPException, Query, Response
from sqlalchemy.orm import Session

from app.api.deps import get_current_user
from app.core.config import get_settings
from app.db.session import get_db
from app.schemas.auth import MagicLinkRequest, MagicLinkResponse, SessionUser
from app.services.auth import consume_magic_link, create_session_for_user, request_magic_link

router = APIRouter(prefix='/v1/auth', tags=['auth'])
public_router = APIRouter(prefix='/v1', tags=['auth'])
settings = get_settings()


@router.post('/request-magic-link', response_model=MagicLinkResponse)
def request_magic_link_endpoint(payload: MagicLinkRequest, db: Session = Depends(get_db)) -> MagicLinkResponse:
    preview_url = request_magic_link(db, payload.email)
    return MagicLinkResponse(message='Magic link generated', preview_url=preview_url if settings.environment != 'production' else None)


@router.get('/verify-magic-link')
def verify_magic_link(token: str = Query(...), db: Session = Depends(get_db)) -> Response:
    user = consume_magic_link(db, token)
    if user is None:
        raise HTTPException(status_code=400, detail='Magic link invalid or expired')
    session_token = create_session_for_user(user)
    response = Response(status_code=302)
    response.headers['Location'] = f'{settings.app_base_url}/onboarding'
    response.set_cookie(
        key=settings.session_cookie_name,
        value=session_token,
        max_age=settings.session_max_age_seconds,
        httponly=True,
        samesite='lax',
        secure=False,
        path='/',
    )
    return response


@router.post('/sign-out')
def sign_out() -> Response:
    response = Response(content='signed out')
    response.delete_cookie(settings.session_cookie_name, path='/')
    return response


@public_router.get('/me', response_model=SessionUser)
def me(user = Depends(get_current_user)) -> SessionUser:
    return SessionUser.model_validate(user)
