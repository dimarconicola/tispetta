from datetime import UTC, datetime, timedelta

from sqlalchemy import delete, select

from app.db.init_db import reset_db
from app.db.session import SessionLocal
from app.matching.service import evaluate_profile_against_catalog
from app.models import Match, Notification, NotificationEvent, NotificationPreference, Opportunity, OpportunityRule, User
from app.seeds.catalog import seed_all
from app.services.admin import publish_opportunity
from app.services.notifications import list_notification_history, run_deadline_reminders, run_weekly_digest


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

        history = list_notification_history(db)

    assert user_id
    assert first == 1
    assert second == 0
    assert calls == [('demo@example.com', 'Scadenze in arrivo - Tispetta')]
    assert history[0]['event_type'] == 'deadline_reminder'
    assert history[0]['status'] == 'sent'


def test_weekly_digest_returns_zero_when_delivery_fails(monkeypatch) -> None:
    def fake_send(_recipient: str, _subject: str, _body: str) -> bool:
        return False

    monkeypatch.setattr('app.services.notifications.send_transactional_email', fake_send)

    with SessionLocal() as db:
        _prepare_single_demo_recipient(db, deadline_in_days=10)
        dispatched = run_weekly_digest(db)
        history = list_notification_history(db)

    assert dispatched == 0
    assert history[0]['event_type'] == 'weekly_digest'
    assert history[0]['status'] == 'failed'


def test_match_transition_emits_only_one_new_relevant_event(monkeypatch) -> None:
    calls: list[str] = []

    def fake_send(recipient: str, subject: str, body: str) -> bool:
        calls.append(subject)
        return True

    monkeypatch.setattr('app.services.notifications.send_transactional_email', fake_send)

    with SessionLocal() as db:
        demo_user = db.execute(select(User).where(User.email == 'demo@example.com')).scalar_one()
        profile = demo_user.profile
        profile.user_type = 'startup'

        opportunity = db.execute(select(Opportunity).order_by(Opportunity.created_at.asc())).scalars().first()
        version = opportunity.current_version
        assert version is not None
        version.target_entities = ['startup']
        rule = next(rule for rule in version.rules if rule.is_active)
        rule.rule_json = {'required': [{'eq': {'field': 'user_type', 'value': 'startup'}}], 'disqualifiers': [], 'boosters': []}

        db.execute(delete(Match).where(Match.user_id == demo_user.id, Match.opportunity_id == opportunity.id))
        db.commit()

        evaluate_profile_against_catalog(db, profile)
        evaluate_profile_against_catalog(db, profile)

        events = db.execute(
            select(NotificationEvent).where(
                NotificationEvent.user_id == demo_user.id,
                NotificationEvent.opportunity_id == opportunity.id,
                NotificationEvent.event_type == 'new_relevant_match',
            )
        ).scalars().all()

    assert len(events) == 1
    assert calls == [f'Nuova opportunita rilevante: {opportunity.title}']


def test_match_upgrade_emits_upgrade_event(monkeypatch) -> None:
    calls: list[str] = []

    def fake_send(_recipient: str, subject: str, _body: str) -> bool:
        calls.append(subject)
        return True

    monkeypatch.setattr('app.services.notifications.send_transactional_email', fake_send)

    with SessionLocal() as db:
        demo_user = db.execute(select(User).where(User.email == 'demo@example.com')).scalar_one()
        profile = demo_user.profile
        profile.user_type = 'startup'
        profile.hiring_intent = None

        opportunity = db.execute(select(Opportunity).order_by(Opportunity.created_at.asc())).scalars().first()
        version = opportunity.current_version
        assert version is not None
        version.target_entities = ['startup']
        rule = next(rule for rule in version.rules if rule.is_active)
        rule.rule_json = {
            'required': [
                {'eq': {'field': 'user_type', 'value': 'startup'}},
                {'eq': {'field': 'hiring_intent', 'value': True}},
            ],
            'disqualifiers': [],
            'boosters': [],
            'tolerated_missing': [{'missing': {'field': 'hiring_intent'}}],
        }

        db.execute(delete(Match).where(Match.user_id == demo_user.id, Match.opportunity_id == opportunity.id))
        db.commit()

        evaluate_profile_against_catalog(db, profile)
        profile.hiring_intent = True
        db.commit()
        evaluate_profile_against_catalog(db, profile)

        events = db.execute(
            select(NotificationEvent)
            .where(NotificationEvent.user_id == demo_user.id, NotificationEvent.opportunity_id == opportunity.id)
            .order_by(NotificationEvent.created_at.asc())
        ).scalars().all()

    assert [event.event_type for event in events] == ['new_relevant_match', 'match_status_upgrade']
    assert calls == [
        f'Nuova opportunita rilevante: {opportunity.title}',
        f'Stato match migliorato: {opportunity.title}',
    ]


def test_publish_opportunity_emits_source_change_digest(monkeypatch) -> None:
    calls: list[str] = []

    def fake_send(_recipient: str, subject: str, _body: str) -> bool:
        calls.append(subject)
        return True

    monkeypatch.setattr('app.services.notifications.send_transactional_email', fake_send)

    with SessionLocal() as db:
        demo_user = db.execute(select(User).where(User.email == 'demo@example.com')).scalar_one()
        opportunity = db.execute(select(Opportunity).order_by(Opportunity.created_at.asc())).scalars().first()
        version = opportunity.current_version
        assert version is not None
        version.version_number = 2
        version.changed_fields = ['deadline_date', 'official_links']

        match = db.execute(
            select(Match).where(Match.user_id == demo_user.id, Match.opportunity_id == opportunity.id)
        ).scalar_one_or_none()
        if match is None:
            match = Match(
                user_id=demo_user.id,
                opportunity_id=opportunity.id,
                match_status='likely',
                match_score=72,
                user_visible_reasoning='rilevante',
                explanation_summary='rilevante',
                missing_fields=[],
            )
            db.add(match)
        else:
            match.match_status = 'likely'
        db.commit()

        publish_opportunity(db, opportunity.id, demo_user.id)

        events = db.execute(
            select(NotificationEvent).where(
                NotificationEvent.user_id == demo_user.id,
                NotificationEvent.opportunity_id == opportunity.id,
                NotificationEvent.event_type == 'source_change_digest',
            )
        ).scalars().all()

    assert len(events) == 1
    assert calls == [f'Aggiornamento fonte ufficiale: {opportunity.title}']


def test_suppressed_notification_is_recorded(monkeypatch) -> None:
    monkeypatch.setattr('app.services.notifications.send_transactional_email', lambda *_args, **_kwargs: True)

    with SessionLocal() as db:
        demo_user = db.execute(select(User).where(User.email == 'demo@example.com')).scalar_one()
        prefs = db.execute(select(NotificationPreference).where(NotificationPreference.user_id == demo_user.id)).scalar_one()
        prefs.email_enabled = True
        prefs.deadline_reminders = False
        db.commit()

        _prepare_single_demo_recipient(db, deadline_in_days=2, preserve_preferences=True)
        dispatched = run_deadline_reminders(db)
        notifications = db.execute(select(Notification).order_by(Notification.created_at.desc())).scalars().all()

    assert dispatched == 0
    assert notifications[0].status == 'suppressed'


def _prepare_single_demo_recipient(db, deadline_in_days: int, *, preserve_preferences: bool = False):
    demo_user = db.execute(select(User).where(User.email == 'demo@example.com')).scalar_one()
    if not preserve_preferences:
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
