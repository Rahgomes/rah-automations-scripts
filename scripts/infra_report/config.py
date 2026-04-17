import os
from dataclasses import dataclass


@dataclass(frozen=True)
class Thresholds:
    memory_warn_percent: int = 80
    memory_critical_percent: int = 90
    disk_warn_percent: int = 80
    disk_critical_percent: int = 90
    load_warn_per_cpu: float = 1.5
    container_top_n: int = 5


@dataclass(frozen=True)
class StorageConfig:
    endpoint: str
    access_key: str
    secret_key: str
    bucket: str
    region: str


@dataclass(frozen=True)
class InfraReportConfig:
    thresholds: Thresholds
    storage: StorageConfig | None


def _get_optional_storage() -> StorageConfig | None:
    endpoint = os.environ.get("MINIO_ENDPOINT")
    access_key = os.environ.get("MINIO_ACCESS_KEY")
    secret_key = os.environ.get("MINIO_SECRET_KEY")
    bucket = os.environ.get("MINIO_BUCKET")
    if not all([endpoint, access_key, secret_key, bucket]):
        return None
    return StorageConfig(
        endpoint=endpoint,
        access_key=access_key,
        secret_key=secret_key,
        bucket=bucket,
        region=os.environ.get("MINIO_REGION", "us-east-1"),
    )


def load() -> InfraReportConfig:
    return InfraReportConfig(
        thresholds=Thresholds(),
        storage=_get_optional_storage(),
    )
