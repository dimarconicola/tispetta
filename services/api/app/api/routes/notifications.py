from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.api.deps import get_current_user
from app.db.session import get_db
from app.schemas.notification import NotificationHistoryItem, NotificationPreferencePayload
from app.services.notifications import list_notification_history_for_user

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


@router.get('/history', response_model=list[NotificationHistoryItem])
def get_history(db: Session = Depends(get_db), user=Depends(get_current_user)) -> list[NotificationHistoryItem]:
    return [NotificationHistoryItem.model_validate(item) for item in list_notification_history_for_user(db, user.id)]
