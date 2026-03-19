from app.schemas.common import ApiModel


class NotificationPreferencePayload(ApiModel):
    email_enabled: bool
    weekly_profile_nudges: bool
    deadline_reminders: bool
    new_opportunity_alerts: bool
    source_change_digests: bool


class NotificationHistoryItem(ApiModel):
    id: str
    event_type: str
    opportunity_id: str | None
    status: str
    recipient: str
    subject: str
    created_at: str
    sent_at: str | None
    error_message: str | None
