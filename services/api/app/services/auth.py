from __future__ import annotations

import hashlib
from datetime import UTC, datetime, timedelta
from email.message import EmailMessage
import smtplib
from urllib.parse import urlencode

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.core.config import get_settings
from app.core.security import create_magic_token, create_session_token, parse_magic_token
from app.models import MagicLinkToken, NotificationPreference, Role, User

settings = get_settings()


def _hash_token(token: str) -> str:
    return hashlib.sha256(token.encode('utf-8')).hexdigest()


def get_or_create_user(db: Session, email: str) -> User:
    user = db.execute(select(User).where(User.email == email.lower())).scalar_one_or_none()
    if user is not None:
        return user
    role = Role.ADMIN.value if email.lower() == settings.demo_admin_email.lower() else Role.USER.value
    user = User(email=email.lower(), role=role, email_verified_at=None)
    db.add(user)
    db.flush()
    db.add(NotificationPreference(user_id=user.id))
    db.commit()
    db.refresh(user)
    return user


def request_magic_link(db: Session, email: str) -> str:
    user = get_or_create_user(db, email)
    token_record = MagicLinkToken(
        email=user.email,
        token_hash='',
        expires_at=datetime.now(UTC) + timedelta(minutes=30),
    )
    db.add(token_record)
    db.flush()
    signed = create_magic_token(token_record.id, user.email)
    token_record.token_hash = _hash_token(signed)
    db.commit()
    preview_url = f"{settings.app_base_url}/api/auth/callback?{urlencode({'token': signed})}"
    _send_magic_email(user.email, preview_url)
    return preview_url


def _send_magic_email(email: str, preview_url: str) -> None:
    message = EmailMessage()
    message['Subject'] = 'Accedi a Benefits Opportunity Engine'
    message['From'] = settings.resend_from_email
    message['To'] = email
    message.set_content(
        'Clicca sul link per accedere al tuo account e aggiornare il profilo:\n\n'
        f'{preview_url}\n\n'
        'Questo link scade tra 30 minuti.'
    )
    try:
        with smtplib.SMTP(settings.smtp_host, settings.smtp_port, timeout=5) as server:
            if settings.smtp_username and settings.smtp_password:
                server.login(settings.smtp_username, settings.smtp_password)
            server.send_message(message)
    except OSError:
        # Mailpit or SMTP may not be running in development; return the preview link to the caller.
        return


def consume_magic_link(db: Session, token: str) -> User | None:
    payload = parse_magic_token(token)
    if payload is None:
        return None
    token_hash = _hash_token(token)
    token_record = db.execute(select(MagicLinkToken).where(MagicLinkToken.token_hash == token_hash)).scalar_one_or_none()
    if token_record is None or token_record.consumed_at is not None or token_record.expires_at < datetime.now(UTC):
        return None
    token_record.consumed_at = datetime.now(UTC)
    user = get_or_create_user(db, payload['email'])
    user.email_verified_at = datetime.now(UTC)
    db.commit()
    return user


def create_session_for_user(user: User) -> str:
    return create_session_token(user.id, user.role, user.email)
