from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.api.deps import get_current_user
from app.db.session import get_db
from app.matching.service import evaluate_profile_against_catalog
from app.schemas.profile import ProfilePayload, ProfileQuestion, ProfileResponse
from app.services.profile import PROFILE_QUESTIONS, get_or_create_profile, update_profile

router = APIRouter(prefix='/v1/profile', tags=['profile'])


@router.get('', response_model=ProfileResponse)
def get_profile(db: Session = Depends(get_db), user=Depends(get_current_user)) -> ProfileResponse:
    profile = get_or_create_profile(db, user)
    db.commit()
    db.refresh(profile)
    return ProfileResponse.model_validate(profile)


@router.put('', response_model=ProfileResponse)
def put_profile(payload: ProfilePayload, db: Session = Depends(get_db), user=Depends(get_current_user)) -> ProfileResponse:
    profile = update_profile(db, user, payload)
    evaluate_profile_against_catalog(db, profile)
    db.refresh(profile)
    return ProfileResponse.model_validate(profile)


@router.get('/questions', response_model=list[ProfileQuestion])
def get_questions() -> list[ProfileQuestion]:
    return [ProfileQuestion.model_validate(question) for question in PROFILE_QUESTIONS]
