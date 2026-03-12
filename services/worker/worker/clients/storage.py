from __future__ import annotations

from functools import lru_cache
from pathlib import Path
from urllib.parse import urlparse

import boto3

from worker.config import settings


@lru_cache(maxsize=1)
def _s3_client():
    return boto3.client(
        's3',
        endpoint_url=settings.object_storage_endpoint,
        aws_access_key_id=settings.object_storage_access_key,
        aws_secret_access_key=settings.object_storage_secret_key,
        region_name=settings.object_storage_region,
    )


def persist_snapshot(source_endpoint_id: str, suffix: str, content: bytes, content_type: str | None = None) -> str:
    if settings.snapshot_storage_backend == 's3':
        key = f'snapshots/{source_endpoint_id}/{suffix}'
        put_kwargs = {
            'Bucket': settings.object_storage_bucket,
            'Key': key,
            'Body': content,
        }
        if content_type:
            put_kwargs['ContentType'] = content_type
        _s3_client().put_object(**put_kwargs)
        return f's3://{settings.object_storage_bucket}/{key}'

    directory = Path(settings.snapshot_dir) / source_endpoint_id
    directory.mkdir(parents=True, exist_ok=True)
    path = directory / suffix
    path.write_bytes(content)
    return str(path)


def read_snapshot(location: str) -> bytes:
    if location.startswith('s3://'):
        parsed = urlparse(location)
        response = _s3_client().get_object(Bucket=parsed.netloc, Key=parsed.path.lstrip('/'))
        return response['Body'].read()
    return Path(location).read_bytes()
