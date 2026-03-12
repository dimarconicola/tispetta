from __future__ import annotations

from pathlib import Path

from worker.config import settings


def persist_snapshot(source_endpoint_id: str, suffix: str, content: bytes) -> str:
    directory = Path(settings.snapshot_dir) / source_endpoint_id
    directory.mkdir(parents=True, exist_ok=True)
    path = directory / suffix
    path.write_bytes(content)
    return str(path)
