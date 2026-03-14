from typing import Literal

from pydantic_settings import BaseSettings, SettingsConfigDict


class WorkerSettings(BaseSettings):
    model_config = SettingsConfigDict(env_file='../../.env', env_file_encoding='utf-8', extra='ignore')

    redis_url: str = 'redis://localhost:6379/0'
    worker_poll_interval_seconds: int = 5
    worker_endpoint_refresh_interval_seconds: int = 60 * 60 * 6
    worker_family_refresh_interval_seconds: int = 60 * 60 * 6
    worker_survey_refresh_interval_seconds: int = 60 * 60 * 24
    snapshot_storage_backend: Literal['local', 's3'] = 'local'
    snapshot_dir: str = '../../tmp/snapshots'
    object_storage_endpoint: str | None = 'http://localhost:9000'
    object_storage_access_key: str | None = 'minioadmin'
    object_storage_secret_key: str | None = 'minioadmin'
    object_storage_bucket: str = 'benefits-engine'
    object_storage_region: str = 'us-east-1'


settings = WorkerSettings()
