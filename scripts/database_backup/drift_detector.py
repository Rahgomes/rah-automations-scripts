import logging

import boto3
from botocore.client import Config
from botocore.exceptions import ClientError

from .config import StorageConfig

logger = logging.getLogger(__name__)


def find_orphaned_prefixes(
    storage: StorageConfig,
    live_databases: list[str],
) -> list[str]:
    """Return database prefixes that exist in the bucket but not in live_databases.

    Each database is backed up under `<database>/...` in the bucket. A top-level
    prefix with no matching live database signals a DB that was removed from
    Postgres but still has stale backups in storage. Returns an empty list if
    the bucket is empty or unreachable (drift detection is best-effort and must
    never block the backup run).
    """
    client = boto3.client(
        "s3",
        endpoint_url=storage.endpoint,
        aws_access_key_id=storage.access_key,
        aws_secret_access_key=storage.secret_key,
        region_name=storage.region,
        config=Config(signature_version="s3v4"),
    )

    try:
        prefixes = _list_top_level_prefixes(client, storage.bucket)
    except ClientError as e:
        logger.warning("Drift detection skipped (cannot list bucket): %s", e)
        return []

    live_set = set(live_databases)
    orphaned = sorted(p for p in prefixes if p not in live_set)
    if orphaned:
        logger.warning(
            "Drift detected: %d orphaned prefix(es) in bucket: %s",
            len(orphaned),
            ", ".join(orphaned),
        )
    return orphaned


def _list_top_level_prefixes(client, bucket: str) -> list[str]:
    prefixes: list[str] = []
    paginator = client.get_paginator("list_objects_v2")
    for page in paginator.paginate(Bucket=bucket, Delimiter="/"):
        for cp in page.get("CommonPrefixes") or []:
            prefix = cp.get("Prefix", "").rstrip("/")
            if prefix:
                prefixes.append(prefix)
    return prefixes
