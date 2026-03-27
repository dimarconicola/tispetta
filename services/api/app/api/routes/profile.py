from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session

from app.api.deps import get_current_user, get_optional_current_user
from app.db.session import get_db
from app.matching.service import evaluate_profile_against_catalog
from app.schemas.profile import ProfileOverviewResponse, ProfilePayload, ProfileQuestionResponse, ProfileResponse
from app.services.profile import (
    get_or_create_profile,
    get_profile_overview,
    get_profile_questions,
    profile_to_response,
    update_profile,
)

router = APIRouter(prefix='/v1/profile', tags=['profile'])


@router.get('', response_model=ProfileResponse)
def get_profile(db: Session = Depends(get_db), user=Depends(get_current_user)) -> ProfileResponse:
    profile = get_or_create_profile(db, user)
    db.commit()
    db.refresh(profile)
    return ProfileResponse.model_validate(profile_to_response(profile))


@router.get('/overview', response_model=ProfileOverviewResponse)
def get_overview(db: Session = Depends(get_db), user=Depends(get_current_user)) -> ProfileOverviewResponse:
    return ProfileOverviewResponse.model_validate(get_profile_overview(db, user))


@router.put('', response_model=ProfileResponse)
def put_profile(payload: ProfilePayload, db: Session = Depends(get_db), user=Depends(get_current_user)) -> ProfileResponse:
    profile = update_profile(db, user, payload)
    evaluate_profile_against_catalog(db, profile)
    db.refresh(profile)
    return ProfileResponse.model_validate(profile_to_response(profile))


@router.get('/questions', response_model=ProfileQuestionResponse)
def get_questions(
    step: str | None = Query(default=None),
    module: str | None = Query(default=None),
    db: Session = Depends(get_db),
    user=Depends(get_optional_current_user),
) -> ProfileQuestionResponse:
    return ProfileQuestionResponse.model_validate(get_profile_questions(db, user, requested_step=step, requested_module=module))
