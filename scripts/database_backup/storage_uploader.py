import logging
from pathlib import Path

import boto3
from botocore.client import Config

from .config import StorageConfig

logger = logging.getLogger(__name__)


def _build_client(storage: StorageConfig):
    return boto3.client(
        "s3",
        endpoint_url=storage.endpoint,
        aws_access_key_id=storage.access_key,
        aws_secret_access_key=storage.secret_key,
        region_name=storage.region,
        config=Config(signature_version="s3v4"),
    )


def upload(storage: StorageConfig, local_path: Path, object_key: str) -> None:
    """Upload a local file to the MinIO bucket at the given object key."""
    client = _build_client(storage)
    logger.info(
        "Uploading '%s' to s3://%s/%s",
        local_path.name,
        storage.bucket,
        object_key,
    )
    client.upload_file(
        Filename=str(local_path),
        Bucket=storage.bucket,
        Key=object_key,
        ExtraArgs={"ContentType": "application/octet-stream"},
    )
    logger.info("Upload completed: %s", object_key)
