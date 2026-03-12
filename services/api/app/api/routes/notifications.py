from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.api.deps import get_current_user
from app.db.session import get_db
from app.schemas.notification import NotificationPreferencePayload

router = APIRouter(prefix='/v1/notifications', tags=['notifications'])


@router.get('/preferences', response_model=NotificationPreferencePayload)
def get_preferences(db: Session = Depends(get_db), user=Depends(get_current_user)) -> NotificationPreferencePayload:
    prefs = user.notification_preferences
    return NotificationPreferencePayload.model_validate(prefs)


@router.put('/preferences', response_model=NotificationPreferencePayload)
def update_preferences(payload: NotificationPreferencePayload, db: Session = Depends(get_db), user=Depends(get_current_user)) -> NotificationPreferencePayload:
    prefs = user.notification_preferences
    for key, value in payload.model_dump().items():
        setattr(prefs, key, value)
    db.commit()
    db.refresh(prefs)
    return NotificationPreferencePayload.model_validate(prefs)
