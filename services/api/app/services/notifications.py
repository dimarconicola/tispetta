from __future__ import annotations

from datetime import UTC, date, datetime, timedelta
import logging
from typing import Any

from sqlalchemy import or_, select
from sqlalchemy.orm import Session

from app.models import (
    Match,
    MatchStatus,
    Notification,
    NotificationEvent,
    NotificationPreference,
    NotificationStatus,
    Opportunity,
    Profile,
    SavedOpportunity,
    User,
)
from app.services.auth import send_transactional_email

logger = logging.getLogger(__name__)

RELEVANT_MATCH_STATUSES = {MatchStatus.CONFIRMED.value, MatchStatus.LIKELY.value}
STATUS_RANK = {
    MatchStatus.NOT_ELIGIBLE.value: 0,
    MatchStatus.UNCLEAR.value: 1,
    MatchStatus.LIKELY.value: 2,
    MatchStatus.CONFIRMED.value: 3,
}


def list_notification_history_for_user(db: Session, user_id: str, *, limit: int = 25) -> list[dict[str, Any]]:
    notifications = (
        db.execute(
            select(Notification, NotificationEvent)
            .join(NotificationEvent, NotificationEvent.id == Notification.notification_event_id)
            .where(NotificationEvent.user_id == user_id)
            .order_by(Notification.created_at.desc())
            .limit(limit)
        )
        .all()
    )
    return [_serialize_notification(notification, event) for notification, event in notifications]


def list_notification_history(db: Session, *, limit: int = 100) -> list[dict[str, Any]]:
    notifications = (
        db.execute(
            select(Notification, NotificationEvent)
            .join(NotificationEvent, NotificationEvent.id == Notification.notification_event_id)
            .order_by(Notification.created_at.desc())
            .limit(limit)
        )
        .all()
    )
    return [_serialize_notification(notification, event) for notification, event in notifications]


def emit_match_transition_events(
    db: Session,
    *,
    profile: Profile,
    opportunity: Opportunity,
    previous_status: str | None,
    current_status: str,
    summary: str,
    missing_fields: list[str],
) -> list[str]:
    if current_status not in RELEVANT_MATCH_STATUSES:
        return []

    previous_rank = STATUS_RANK.get(previous_status or MatchStatus.NOT_ELIGIBLE.value, -1)
    current_rank = STATUS_RANK.get(current_status, -1)
    if previous_status == current_status:
        return []
    if previous_rank >= current_rank:
        return []

    version = opportunity.current_version
    if version is None:
        return []
    user = db.execute(select(User).where(User.id == profile.user_id)).scalar_one_or_none()
    if user is None:
        return []

    reason = 'new_relevant_match'
    subject = f'Nuova opportunita rilevante: {opportunity.title}'
    body = (
        f"Ciao,\n\n{opportunity.title} e ora {current_status} per il tuo profilo.\n\n"
        f"Perche: {summary}\n"
        f"{_format_missing_fields(missing_fields)}"
        f"Dettagli: https://app.tispetta.eu/opportunities/{opportunity.slug}\n"
    )

    if previous_status in RELEVANT_MATCH_STATUSES and previous_rank < current_rank:
        reason = 'match_status_upgrade'
        subject = f'Stato match migliorato: {opportunity.title}'
        body = (
            f"Ciao,\n\n{opportunity.title} e passato da {previous_status} a {current_status}.\n\n"
            f"Perche: {summary}\n"
            f"{_format_missing_fields(missing_fields)}"
            f"Dettagli: https://app.tispetta.eu/opportunities/{opportunity.slug}\n"
        )

    dedupe_key = f'{reason}:{profile.user_id}:{opportunity.id}:{version.id}:{current_status}'
    event = create_notification_event(
        db,
        user_id=profile.user_id,
        event_type=reason,
        opportunity_id=opportunity.id,
        dedupe_key=dedupe_key,
        payload={
            'email': user.email,
            'subject': subject,
            'body': body,
            'status': current_status,
            'previous_status': previous_status,
        },
    )
    delivered = deliver_notification_event(db, event.id, preference_key='new_opportunity_alerts')
    return [event.id] if delivered else []


def emit_opportunity_change_events(db: Session, opportunity: Opportunity) -> int:
    version = opportunity.current_version
    if version is None or version.version_number <= 1:
        return 0

    changed_fields = version.changed_fields or []
    if not changed_fields:
        return 0

    recipients = (
        db.execute(
            select(User.id, User.email)
            .join(NotificationPreference, NotificationPreference.user_id == User.id)
            .outerjoin(Match, Match.user_id == User.id)
            .outerjoin(SavedOpportunity, SavedOpportunity.user_id == User.id)
            .where(
                NotificationPreference.email_enabled.is_(True),
                NotificationPreference.source_change_digests.is_(True),
                or_(
                    Match.opportunity_id == opportunity.id,
                    SavedOpportunity.opportunity_id == opportunity.id,
                ),
            )
        )
        .all()
    )
    unique_recipients = {(user_id, email) for user_id, email in recipients if email}
    sent = 0
    for user_id, email in unique_recipients:
        dedupe_key = f'source-change:{user_id}:{opportunity.id}:{version.id}'
        event = create_notification_event(
            db,
            user_id=user_id,
            event_type='source_change_digest',
            opportunity_id=opportunity.id,
            dedupe_key=dedupe_key,
            payload={
                'email': email,
                'subject': f'Aggiornamento fonte ufficiale: {opportunity.title}',
                'body': (
                    f"Ciao,\n\nLa scheda di {opportunity.title} e stata aggiornata.\n\n"
                    f"Campi cambiati: {', '.join(changed_fields)}\n"
                    f"Dettagli: https://app.tispetta.eu/opportunities/{opportunity.slug}\n"
                ),
                'changed_fields': changed_fields,
            },
        )
        if deliver_notification_event(db, event.id, preference_key='source_change_digests'):
            sent += 1
    return sent


def run_deadline_reminders(db: Session) -> int:
    now = datetime.now(UTC)
    near = now + timedelta(days=30)
    rows = db.execute(
        select(User.id, User.email, Match, Opportunity)
        .join(Match, Match.user_id == User.id)
        .join(Opportunity, Opportunity.id == Match.opportunity_id)
        .join(NotificationPreference, NotificationPreference.user_id == User.id)
        .where(
            NotificationPreference.email_enabled.is_(True),
            Match.match_status.in_(list(RELEVANT_MATCH_STATUSES)),
            Opportunity.deadline_date <= near,
            Opportunity.deadline_date >= now,
        )
    ).all()
    by_user: dict[tuple[str, str], list[tuple[str, object]]] = {}
    for user_id, email, _match, opp in rows:
        by_user.setdefault((user_id, email), []).append((opp.title, opp.deadline_date))

    dispatched = 0
    for (user_id, email), items in by_user.items():
        sorted_items = sorted(items, key=lambda item: str(item[1] or '9999-12-31'))
        lines = '\n'.join(
            f"- {title}: scadenza {dl.strftime('%d/%m/%Y') if hasattr(dl, 'strftime') else str(dl) if dl else 'N/D'}"
            for title, dl in sorted_items
        )
        event = create_notification_event(
            db,
            user_id=user_id,
            event_type='deadline_reminder',
            opportunity_id=None,
            dedupe_key=f'deadline-reminder:{user_id}:{now.date().isoformat()}',
            payload={
                'email': email,
                'subject': 'Scadenze in arrivo - Tispetta',
                'body': (
                    f"Ciao,\n\nHai {len(items)} opportunita con scadenza nei prossimi 30 giorni:\n\n"
                    f"{lines}\n\nAccedi per vedere i dettagli: https://app.tispetta.eu\n"
                ),
            },
        )
        if deliver_notification_event(db, event.id, preference_key='deadline_reminders'):
            dispatched += 1
            logger.info('Deadline reminder sent to %s (%d items)', email, len(items))
    return dispatched


def run_weekly_digest(db: Session) -> int:
    user_rows = db.execute(
        select(NotificationPreference.user_id, User.email)
        .join(User, User.id == NotificationPreference.user_id)
        .where(
            NotificationPreference.email_enabled.is_(True),
        )
    ).all()
    dispatched = 0
    year, week, _ = datetime.now(UTC).isocalendar()
    for user_id, email in user_rows:
        match_rows = db.execute(
            select(Match, Opportunity)
            .join(Opportunity, Opportunity.id == Match.opportunity_id)
            .where(
                Match.user_id == user_id,
                Match.match_status.in_(list(RELEVANT_MATCH_STATUSES)),
            )
            .order_by(Match.match_score.desc())
            .limit(5)
        ).all()
        if not match_rows:
            continue
        profile = db.execute(select(Profile).where(Profile.user_id == user_id)).scalar_one_or_none()
        score = int(profile.profile_completeness_score) if profile else 0
        lines = '\n'.join(f"- {opp.title} ({match.match_status})" for match, opp in match_rows)
        nudge = (
            "\nIl tuo profilo non e ancora completo. Aggiungi piu informazioni per sbloccare match:\nhttps://app.tispetta.eu/onboarding\n"
            if score < 60
            else ''
        )
        event = create_notification_event(
            db,
            user_id=user_id,
            event_type='weekly_digest',
            opportunity_id=None,
            dedupe_key=f'weekly-digest:{user_id}:{year}-W{week:02d}',
            payload={
                'email': email,
                'subject': 'Le tue opportunita della settimana - Tispetta',
                'body': (
                    f"Ciao,\n\nEcco le tue opportunita piu rilevanti (profilo al {score}%):\n\n"
                    f"{lines}\n{nudge}\nAccedi per i dettagli: https://app.tispetta.eu\n"
                ),
            },
        )
        if deliver_notification_event(db, event.id, preference_key='weekly_profile_nudges'):
            dispatched += 1
            logger.info('Weekly digest sent to user %s', user_id)
    return dispatched


def create_notification_event(
    db: Session,
    *,
    user_id: str,
    event_type: str,
    opportunity_id: str | None,
    dedupe_key: str,
    payload: dict[str, Any],
) -> NotificationEvent:
    event = db.execute(select(NotificationEvent).where(NotificationEvent.dedupe_key == dedupe_key)).scalar_one_or_none()
    if event is not None:
        return event
    event = NotificationEvent(
        user_id=user_id,
        event_type=event_type,
        opportunity_id=opportunity_id,
        dedupe_key=dedupe_key,
        payload=payload,
    )
    db.add(event)
    db.flush()
    return event


def deliver_notification_event(db: Session, event_id: str, *, preference_key: str | None = None) -> bool:
    event = db.execute(select(NotificationEvent).where(NotificationEvent.id == event_id)).scalar_one_or_none()
    if event is None:
        return False

    notification = db.execute(
        select(Notification).where(Notification.notification_event_id == event.id)
    ).scalar_one_or_none()
    if notification is not None and notification.status == NotificationStatus.SENT.value:
        logger.info('Skipping already sent notification for event %s', event.id)
        return False

    recipient = (event.payload or {}).get('email', 'unknown@example.com')
    subject = (event.payload or {}).get('subject', 'Aggiornamento opportunita')
    body = (event.payload or {}).get('body', '')

    if notification is None:
        notification = Notification(
            notification_event_id=event.id,
            recipient=recipient,
            subject=subject,
            body=body,
            status=NotificationStatus.PENDING.value,
        )
        db.add(notification)
    else:
        notification.recipient = recipient
        notification.subject = subject
        notification.body = body
        notification.status = NotificationStatus.PENDING.value
        notification.sent_at = None
        notification.error_message = None

    if preference_key is not None:
        pref = db.execute(select(NotificationPreference).where(NotificationPreference.user_id == event.user_id)).scalar_one_or_none()
        if pref is not None and (not pref.email_enabled or not getattr(pref, preference_key)):
            notification.status = NotificationStatus.SUPPRESSED.value
            notification.error_message = f'Suppressed by preference: {preference_key}'
            db.commit()
            return False

    delivered = send_transactional_email(notification.recipient, notification.subject, notification.body)
    notification.status = NotificationStatus.SENT.value if delivered else NotificationStatus.FAILED.value
    notification.sent_at = datetime.now(UTC) if delivered else None
    notification.error_message = None if delivered else 'Delivery failed'
    db.commit()
    return delivered


def _serialize_notification(notification: Notification, event: NotificationEvent) -> dict[str, Any]:
    return {
        'id': notification.id,
        'event_type': event.event_type,
        'opportunity_id': event.opportunity_id,
        'status': notification.status,
        'recipient': notification.recipient,
        'subject': notification.subject,
        'created_at': notification.created_at.isoformat(),
        'sent_at': notification.sent_at.isoformat() if notification.sent_at else None,
        'error_message': notification.error_message,
    }


def _format_missing_fields(missing_fields: list[str]) -> str:
    if not missing_fields:
        return ''
    return f"Mancano ancora questi dati per migliorare la precisione: {', '.join(missing_fields)}.\n\n"
