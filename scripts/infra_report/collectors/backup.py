import logging
from dataclasses import dataclass
from datetime import datetime, timezone

import boto3
from botocore.client import Config

from ..config import StorageConfig

logger = logging.getLogger(__name__)


@dataclass(frozen=True)
class BackupInfo:
    found: bool
    last_backup_at: datetime | None = None
    total_objects: int = 0
    total_size_gb: float = 0.0
    error: str = ""


def collect(storage: StorageConfig) -> BackupInfo:
    try:
        client = boto3.client(
            "s3",
            endpoint_url=storage.endpoint,
            aws_access_key_id=storage.access_key,
            aws_secret_access_key=storage.secret_key,
            region_name=storage.region,
            config=Config(signature_version="s3v4"),
        )

        last_modified: datetime | None = None
        total_objects = 0
        total_size = 0

        paginator = client.get_paginator("list_objects_v2")
        for page in paginator.paginate(Bucket=storage.bucket):
            for obj in page.get("Contents", []) or []:
                total_objects += 1
                total_size += obj.get("Size", 0)
                obj_modified = obj.get("LastModified")
                if obj_modified and (last_modified is None or obj_modified > last_modified):
                    last_modified = obj_modified

        if last_modified and last_modified.tzinfo is None:
            last_modified = last_modified.replace(tzinfo=timezone.utc)

        return BackupInfo(
            found=total_objects > 0,
            last_backup_at=last_modified,
            total_objects=total_objects,
            total_size_gb=total_size / (1024**3),
        )
    except Exception as e:
        logger.warning("Failed to query MinIO: %s", e)
        return BackupInfo(found=False, error=str(e))
