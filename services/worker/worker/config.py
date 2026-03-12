from pydantic_settings import BaseSettings, SettingsConfigDict


class WorkerSettings(BaseSettings):
    model_config = SettingsConfigDict(env_file='../../.env', env_file_encoding='utf-8', extra='ignore')

    redis_url: str = 'redis://localhost:6379/0'
    worker_poll_interval_seconds: int = 5
    snapshot_dir: str = '../../tmp/snapshots'


settings = WorkerSettings()
