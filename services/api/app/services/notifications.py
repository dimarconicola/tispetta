from __future__ import annotations

from datetime import UTC, datetime, timedelta
import logging

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models import Match, NotificationPreference, Opportunity, Profile, User
from app.services.auth import send_transactional_email

logger = logging.getLogger(__name__)


def run_deadline_reminders(db: Session) -> int:
    """Send deadline alerts for confirmed/likely matches expiring within 30 days.

    Returns the number of emails dispatched.
    """
    now = datetime.now(UTC)
    near = now + timedelta(days=30)
    rows = db.execute(
        select(User.email, Match, Opportunity)
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
    by_user: dict[str, list[tuple[str, object]]] = {}
    for email, _match, opp in rows:
        by_user.setdefault(email, []).append((opp.title, opp.deadline_date))
    dispatched = 0
    for email, items in by_user.items():
        sorted_items = sorted(items, key=lambda x: str(x[1] or '9999-12-31'))
        lines = '\n'.join(
            f"- {title}: scadenza {dl.strftime('%d/%m/%Y') if hasattr(dl, 'strftime') else str(dl) if dl else 'N/D'}"
            for title, dl in sorted_items
        )
        send_transactional_email(
            email,
            'Scadenze in arrivo - Tispetta',
            f"Ciao,\n\nHai {len(items)} opportunita con scadenza nei prossimi 30 giorni:\n\n{lines}\n\nAccedi per vedere i dettagli: https://app.tispetta.eu\n",
        )
        dispatched += 1
        logger.info('Deadline reminder sent to %s (%d items)', email, len(items))
    return dispatched


def run_weekly_digest(db: Session) -> int:
    """Send weekly top-matches digest to users with weekly_profile_nudges enabled.

    Returns the number of emails dispatched.
    """
    user_rows = db.execute(
        select(NotificationPreference.user_id, User.email)
        .join(User, User.id == NotificationPreference.user_id)
        .where(
            NotificationPreference.email_enabled.is_(True),
            NotificationPreference.weekly_profile_nudges.is_(True),
        )
    ).all()
    dispatched = 0
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
        lines = '\n'.join(f"- {opp.title} ({m.match_status})" for m, opp in match_rows)
        nudge = (
            "\nIl tuo profilo non e ancora completo. Aggiungi piu informazioni per sbloccare match:\nhttps://app.tispetta.eu/onboarding\n"
            if score < 60 else ""
        )
        send_transactional_email(
            email,
            'Le tue opportunita della settimana - Tispetta',
            f"Ciao,\n\nEcco le tue opportunita piu rilevanti (profilo al {score}%):\n\n{lines}\n{nudge}\nAccedi per i dettagli: https://app.tispetta.eu\n",
        )
        dispatched += 1
        logger.info('Weekly digest sent to user %s', user_id)
    return dispatched
