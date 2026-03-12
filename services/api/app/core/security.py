from datetime import UTC, datetime, timedelta
from typing import Any

from itsdangerous import BadSignature, URLSafeTimedSerializer

from app.core.config import get_settings


class TokenSigner:
    def __init__(self) -> None:
        settings = get_settings()
        self.serializer = URLSafeTimedSerializer(settings.app_secret_key, salt='benefits-opportunity-engine')
        self.max_age = settings.session_max_age_seconds

    def sign(self, payload: dict[str, Any]) -> str:
        return self.serializer.dumps(payload)

    def unsign(self, token: str, max_age: int | None = None) -> dict[str, Any]:
        return self.serializer.loads(token, max_age=max_age or self.max_age)


signer = TokenSigner()


def create_session_token(user_id: str, role: str, email: str) -> str:
    return signer.sign(
        {
            'sub': user_id,
            'role': role,
            'email': email,
            'iat': int(datetime.now(UTC).timestamp()),
        }
    )


def parse_session_token(token: str) -> dict[str, Any] | None:
    try:
        return signer.unsign(token)
    except BadSignature:
        return None


def create_magic_token(token_id: str, email: str) -> str:
    return signer.sign({'token_id': token_id, 'email': email, 'kind': 'magic'})


def parse_magic_token(token: str, max_age_seconds: int = 60 * 30) -> dict[str, Any] | None:
    try:
        payload = signer.unsign(token, max_age=max_age_seconds)
    except BadSignature:
        return None
    if payload.get('kind') != 'magic':
        return None
    return payload
