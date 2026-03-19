from __future__ import annotations

from datetime import UTC, date, datetime, timedelta
import logging

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models import (
    Match,
    Notification,
    NotificationEvent,
    NotificationPreference,
    NotificationStatus,
    Opportunity,
    Profile,
    User,
)
from app.services.auth import send_transactional_email

logger = logging.getLogger(__name__)


def run_deadline_reminders(db: Session) -> int:
    """Send one deduped deadline reminder per user per UTC day."""

    now = datetime.now(UTC)
    near = now + timedelta(days=30)
    rows = db.execute(
        select(User.id, User.email, Match, Opportunity)
        .join(Match, Match.user_id == User.id)
        .join(Opportunity, Opportunity.id == Match.opportunity_id)
        .join(NotificationPreference, NotificationPreference.user_id == User.id)
        .where(
            NotificationPreference.email_enabled.is_(True),
            NotificationPreference.deadline_reminders.is_(True),
            Match.match_status.in_(['confirmed', 'likely']),
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
        delivered = _deliver_scheduled_email(
            db,
            user_id=user_id,
            recipient=email,
            event_type='deadline_reminder',
            dedupe_key=f'deadline-reminder:{user_id}:{now.date().isoformat()}',
            subject='Scadenze in arrivo - Tispetta',
            body=(
                f"Ciao,\n\nHai {len(items)} opportunita con scadenza nei prossimi 30 giorni:\n\n"
                f"{lines}\n\nAccedi per vedere i dettagli: https://app.tispetta.eu\n"
            ),
        )
        if delivered:
            dispatched += 1
            logger.info('Deadline reminder sent to %s (%d items)', email, len(items))
    return dispatched


def run_weekly_digest(db: Session) -> int:
    """Send one deduped weekly digest per user and ISO week."""

    user_rows = db.execute(
        select(NotificationPreference.user_id, User.email)
        .join(User, User.id == NotificationPreference.user_id)
        .where(
            NotificationPreference.email_enabled.is_(True),
            NotificationPreference.weekly_profile_nudges.is_(True),
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
                Match.match_status.in_(['confirmed', 'likely']),
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
        delivered = _deliver_scheduled_email(
            db,
            user_id=user_id,
            recipient=email,
            event_type='weekly_digest',
            dedupe_key=f'weekly-digest:{user_id}:{year}-W{week:02d}',
            subject='Le tue opportunita della settimana - Tispetta',
            body=(
                f"Ciao,\n\nEcco le tue opportunita piu rilevanti (profilo al {score}%):\n\n"
                f"{lines}\n{nudge}\nAccedi per i dettagli: https://app.tispetta.eu\n"
            ),
        )
        if delivered:
            dispatched += 1
            logger.info('Weekly digest sent to user %s', user_id)
    return dispatched


def _deliver_scheduled_email(
    db: Session,
    *,
    user_id: str,
    recipient: str,
    event_type: str,
    dedupe_key: str,
    subject: str,
    body: str,
) -> bool:
    event = db.execute(select(NotificationEvent).where(NotificationEvent.dedupe_key == dedupe_key)).scalar_one_or_none()
    if event is None:
        event = NotificationEvent(
            user_id=user_id,
            event_type=event_type,
            opportunity_id=None,
            dedupe_key=dedupe_key,
            payload={'email': recipient, 'subject': subject, 'body': body},
        )
        db.add(event)
        db.flush()

    notification = db.execute(
        select(Notification).where(Notification.notification_event_id == event.id)
    ).scalar_one_or_none()
    if notification is not None and notification.status in {
        NotificationStatus.SENT.value,
        NotificationStatus.PENDING.value,
    }:
        logger.info('Skipping duplicate scheduled notification %s for %s', dedupe_key, recipient)
        return False

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

    delivered = send_transactional_email(recipient, subject, body)
    notification.status = NotificationStatus.SENT.value if delivered else NotificationStatus.FAILED.value
    notification.sent_at = datetime.now(UTC) if delivered else None
    if not delivered:
        notification.error_message = 'Delivery failed'
    db.commit()
    return delivered
