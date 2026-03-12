from app.schemas.common import ApiModel


class NotificationPreferencePayload(ApiModel):
    email_enabled: bool
    weekly_profile_nudges: bool
    deadline_reminders: bool
    new_opportunity_alerts: bool
    source_change_digests: bool
