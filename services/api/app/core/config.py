from functools import lru_cache
from typing import Literal

from pydantic_settings import BaseSettings, SettingsConfigDict

CookieSameSite = Literal['lax', 'strict', 'none']


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file='../../.env', env_file_encoding='utf-8', extra='ignore')

    environment: Literal['development', 'test', 'production'] = 'development'
    api_host: str = '0.0.0.0'
    api_port: int = 8000
    app_secret_key: str = 'change-me'
    app_base_url: str = 'http://localhost:3000'
    database_url: str = 'sqlite:///./benefits_engine.db'
    redis_url: str = 'redis://localhost:6379/0'
    object_storage_endpoint: str | None = 'http://localhost:9000'
    object_storage_access_key: str | None = 'minioadmin'
    object_storage_secret_key: str | None = 'minioadmin'
    object_storage_bucket: str = 'benefits-engine'
    object_storage_region: str = 'us-east-1'
    resend_api_key: str | None = None
    resend_from_email: str = 'noreply@example.com'
    smtp_host: str = 'localhost'
    smtp_port: int = 1025
    smtp_username: str | None = None
    smtp_password: str | None = None
    smtp_use_ssl: bool = False
    smtp_use_starttls: bool = False
    openai_api_key: str | None = None
    sentry_dsn: str | None = None
    posthog_api_key: str | None = None
    session_cookie_name: str = 'boe_session'
    session_cookie_domain: str | None = None
    session_cookie_secure: bool = False
    session_cookie_same_site: CookieSameSite = 'lax'
    session_max_age_seconds: int = 60 * 60 * 24 * 14
    cors_allowed_origins: str = ''
    auto_create_schema: bool = True
    auto_seed_on_startup: bool = False
    demo_admin_email: str = 'admin@example.com'
    demo_user_email: str = 'demo@example.com'

    def cors_origins(self) -> list[str]:
        configured = [origin.strip() for origin in self.cors_allowed_origins.split(',') if origin.strip()]
        if configured:
            return configured
        defaults = ['http://localhost:3000', self.app_base_url]
        deduped: list[str] = []
        for origin in defaults:
            if origin and origin not in deduped:
                deduped.append(origin)
        return deduped

    def cookie_domain(self) -> str | None:
        return self.session_cookie_domain.strip() if self.session_cookie_domain else None

    def cookie_secure(self) -> bool:
        return self.session_cookie_secure or self.environment == 'production'

    def smtp_ssl_enabled(self) -> bool:
        return self.smtp_use_ssl or self.smtp_port == 465


@lru_cache
def get_settings() -> Settings:
    return Settings()
