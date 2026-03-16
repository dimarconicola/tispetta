from __future__ import annotations

import hashlib
from datetime import UTC, datetime, timedelta
from email.message import EmailMessage
import smtplib
from urllib.parse import urlencode

import httpx
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.core.config import get_settings
from app.core.security import create_magic_token, create_session_token, parse_magic_token
from app.models import MagicLinkToken, NotificationPreference, Role, User

settings = get_settings()


def _hash_token(token: str) -> str:
    return hashlib.sha256(token.encode('utf-8')).hexdigest()


def _is_expired(expires_at: datetime) -> bool:
    now = datetime.now(UTC)
    comparable_now = now if expires_at.tzinfo is not None else now.replace(tzinfo=None)
    return expires_at < comparable_now


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


def _normalize_redirect_to(redirect_to: str | None) -> str | None:
    if redirect_to is None:
        return None

    candidate = redirect_to.strip()
    if not candidate or len(candidate) > 255:
        return None
    if not candidate.startswith('/') or candidate.startswith('//'):
        return None
    return candidate


def request_magic_link(db: Session, email: str, redirect_to: str | None = None) -> str:
    user = get_or_create_user(db, email)
    normalized_redirect_to = _normalize_redirect_to(redirect_to)
    token_record = MagicLinkToken(
        email=user.email,
        token_hash='',
        redirect_to=normalized_redirect_to,
        expires_at=datetime.now(UTC) + timedelta(minutes=30),
    )
    db.add(token_record)
    db.flush()
    signed = create_magic_token(token_record.id, user.email)
    token_record.token_hash = _hash_token(signed)
    db.commit()
    preview_url = f"{settings.app_base_url}/api/auth/callback?{urlencode({'token': signed})}"
    delivered = _send_magic_email(user.email, preview_url)
    if not delivered and settings.environment == 'production':
        raise RuntimeError('Magic link email delivery failed')
    return preview_url


def _send_magic_email(email: str, preview_url: str) -> bool:
    if settings.resend_api_key:
        try:
            _send_magic_email_via_resend(email, preview_url)
            return True
        except (httpx.HTTPError, OSError):
            if not settings.smtp_host:
                return False
    try:
        _send_magic_email_via_smtp(email, preview_url)
        return True
    except (OSError, smtplib.SMTPException):
        # Local development can continue with the preview link when Mailpit/SMTP is unavailable.
        return False


def send_transactional_email(to: str, subject: str, body: str) -> bool:
    if settings.resend_api_key:
        try:
            response = httpx.post(
                'https://api.resend.com/emails',
                headers={
                    'Authorization': f'Bearer {settings.resend_api_key}',
                    'Content-Type': 'application/json',
                },
                json={'from': settings.resend_from_email, 'to': [to], 'subject': subject, 'text': body},
                timeout=10.0,
            )
            response.raise_for_status()
            return True
        except (httpx.HTTPError, OSError):
            if not settings.smtp_host:
                return False
    try:
        message = EmailMessage()
        message['Subject'] = subject
        message['From'] = settings.resend_from_email
        message['To'] = to
        message.set_content(body)
        client_cls = smtplib.SMTP_SSL if settings.smtp_ssl_enabled() else smtplib.SMTP
        with client_cls(settings.smtp_host, settings.smtp_port, timeout=10) as server:
            if settings.smtp_use_starttls and not settings.smtp_ssl_enabled():
                server.starttls()
            if settings.smtp_username and settings.smtp_password:
                server.login(settings.smtp_username, settings.smtp_password)
            server.send_message(message)
        return True
    except (OSError, smtplib.SMTPException):
        return False


def _magic_link_html(url: str) -> str:
    return (
        '<!DOCTYPE html><html lang="it"><body style="font-family:sans-serif;max-width:480px;margin:40px auto;color:#1a1a1a">'
        '<h2 style="margin-bottom:0.5rem">Accedi a Tispetta</h2>'
        '<p style="color:#555">Clicca sul pulsante per accedere al tuo account e aggiornare il profilo.</p>'
        f'<a href="{url}" style="display:inline-block;margin:1.5rem 0;padding:0.75rem 1.5rem;background:#1a1a1a;color:#fff;text-decoration:none;border-radius:6px;font-weight:600">Accedi ora</a>'
        '<p style="font-size:0.85rem;color:#888">Questo link scade tra 30 minuti. Se non hai richiesto l\'accesso, ignora questa email.</p>'
        f'<p style="font-size:0.8rem;color:#aaa;word-break:break-all">Oppure copia: {url}</p>'
        '</body></html>'
    )


def _send_magic_email_via_resend(email: str, preview_url: str) -> None:
    plain = (
        'Clicca sul link per accedere al tuo account e aggiornare il profilo:\n\n'
        f'{preview_url}\n\n'
        'Questo link scade tra 30 minuti.'
    )
    response = httpx.post(
        'https://api.resend.com/emails',
        headers={
            'Authorization': f'Bearer {settings.resend_api_key}',
            'Content-Type': 'application/json',
        },
        json={
            'from': settings.resend_from_email,
            'to': [email],
            'subject': 'Accedi a Tispetta',
            'text': plain,
            'html': _magic_link_html(preview_url),
        },
        timeout=10.0,
    )
    response.raise_for_status()


def _send_magic_email_via_smtp(email: str, preview_url: str) -> None:
    message = EmailMessage()
    message['Subject'] = 'Accedi a Tispetta'
    message['From'] = settings.resend_from_email
    message['To'] = email
    message.set_content(
        'Clicca sul link per accedere al tuo account e aggiornare il profilo:\n\n'
        f'{preview_url}\n\n'
        'Questo link scade tra 30 minuti.'
    )
    message.add_alternative(_magic_link_html(preview_url), subtype='html')
    client_cls = smtplib.SMTP_SSL if settings.smtp_ssl_enabled() else smtplib.SMTP
    with client_cls(settings.smtp_host, settings.smtp_port, timeout=10) as server:
        if settings.smtp_use_starttls and not settings.smtp_ssl_enabled():
            server.starttls()
        if settings.smtp_username and settings.smtp_password:
            server.login(settings.smtp_username, settings.smtp_password)
        server.send_message(message)


def consume_magic_link(db: Session, token: str) -> tuple[User | None, str | None]:
    payload = parse_magic_token(token)
    if payload is None:
        return None, None
    token_hash = _hash_token(token)
    token_record = db.execute(select(MagicLinkToken).where(MagicLinkToken.token_hash == token_hash)).scalar_one_or_none()
    if token_record is None or token_record.consumed_at is not None or _is_expired(token_record.expires_at):
        return None, None
    token_record.consumed_at = datetime.now(UTC)
    user = get_or_create_user(db, payload['email'])
    user.email_verified_at = datetime.now(UTC)
    db.commit()
    return user, _normalize_redirect_to(token_record.redirect_to)


def create_session_for_user(user: User) -> str:
    return create_session_token(user.id, user.role, user.email)
