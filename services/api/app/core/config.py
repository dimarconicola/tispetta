from functools import lru_cache
from typing import Literal

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file='../../.env', env_file_encoding='utf-8', extra='ignore')

    environment: Literal['development', 'test', 'production'] = 'development'
    api_host: str = '0.0.0.0'
    api_port: int = 8000
    app_secret_key: str = 'change-me'
    app_base_url: str = 'http://localhost:3000'
    database_url: str = 'sqlite:///./benefits_engine.db'
    redis_url: str = 'redis://localhost:6379/0'
    object_storage_endpoint: str = 'http://localhost:9000'
    object_storage_access_key: str = 'minioadmin'
    object_storage_secret_key: str = 'minioadmin'
    object_storage_bucket: str = 'benefits-engine'
    object_storage_region: str = 'us-east-1'
    resend_api_key: str | None = None
    resend_from_email: str = 'noreply@example.com'
    smtp_host: str = 'localhost'
    smtp_port: int = 1025
    smtp_username: str | None = None
    smtp_password: str | None = None
    openai_api_key: str | None = None
    sentry_dsn: str | None = None
    posthog_api_key: str | None = None
    session_cookie_name: str = 'boe_session'
    session_max_age_seconds: int = 60 * 60 * 24 * 14
    auto_create_schema: bool = True
    auto_seed_on_startup: bool = False
    demo_admin_email: str = 'admin@benefits.local'
    demo_user_email: str = 'demo@benefits.local'


@lru_cache
def get_settings() -> Settings:
    return Settings()
