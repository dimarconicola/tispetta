from datetime import UTC, datetime, timedelta

from sqlalchemy import select

from app.db.init_db import reset_db
from app.db.session import SessionLocal
from app.models import Match, NotificationPreference, Opportunity, User
from app.seeds.catalog import seed_all
from app.services.notifications import run_deadline_reminders, run_weekly_digest


def setup_function() -> None:
    reset_db()
    with SessionLocal() as db:
        seed_all(db)


def test_deadline_reminders_are_deduped_and_count_only_success(monkeypatch) -> None:
    calls: list[tuple[str, str]] = []

    def fake_send(recipient: str, subject: str, body: str) -> bool:
        calls.append((recipient, subject))
        return True

    monkeypatch.setattr('app.services.notifications.send_transactional_email', fake_send)

    with SessionLocal() as db:
        user_id = _prepare_single_demo_recipient(db, deadline_in_days=2)
        first = run_deadline_reminders(db)
        second = run_deadline_reminders(db)

    assert user_id
    assert first == 1
    assert second == 0
    assert calls == [('demo@example.com', 'Scadenze in arrivo - Tispetta')]


def test_weekly_digest_returns_zero_when_delivery_fails(monkeypatch) -> None:
    def fake_send(_recipient: str, _subject: str, _body: str) -> bool:
        return False

    monkeypatch.setattr('app.services.notifications.send_transactional_email', fake_send)

    with SessionLocal() as db:
        _prepare_single_demo_recipient(db, deadline_in_days=10)
        dispatched = run_weekly_digest(db)

    assert dispatched == 0


def _prepare_single_demo_recipient(db, deadline_in_days: int):
    demo_user = db.execute(select(User).where(User.email == 'demo@example.com')).scalar_one()
    prefs = db.execute(select(NotificationPreference)).scalars().all()
    for pref in prefs:
        pref.email_enabled = pref.user_id == demo_user.id
        pref.deadline_reminders = pref.user_id == demo_user.id
        pref.weekly_profile_nudges = pref.user_id == demo_user.id

    row = db.execute(
        select(Match, Opportunity)
        .join(Opportunity, Opportunity.id == Match.opportunity_id)
        .where(Match.user_id == demo_user.id)
        .order_by(Match.match_score.desc())
    ).first()
    assert row is not None
    match, opportunity = row
    match.match_status = 'confirmed'
    opportunity.deadline_date = datetime.now(UTC) + timedelta(days=deadline_in_days)
    db.commit()
    return demo_user.id
