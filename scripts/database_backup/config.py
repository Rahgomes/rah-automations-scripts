import os
from dataclasses import dataclass


@dataclass(frozen=True)
class PostgresConfig:
    host: str
    port: str
    user: str
    password: str
    databases: list[str]


@dataclass(frozen=True)
class StorageConfig:
    endpoint: str
    access_key: str
    secret_key: str
    bucket: str
    region: str


@dataclass(frozen=True)
class BackupConfig:
    postgres: PostgresConfig
    storage: StorageConfig


def _require(name: str) -> str:
    value = os.environ.get(name)
    if not value:
        raise RuntimeError(f"Missing required environment variable: {name}")
    return value


def _parse_databases(raw: str) -> list[str]:
    databases = [db.strip() for db in raw.split(",") if db.strip()]
    if not databases:
        raise RuntimeError("PGDATABASES must contain at least one database name")
    return databases


def load() -> BackupConfig:
    """Load and validate backup configuration from environment variables."""
    postgres = PostgresConfig(
        host=_require("PGHOST"),
        port=os.environ.get("PGPORT", "5432"),
        user=_require("PGUSER"),
        password=_require("PGPASSWORD"),
        databases=_parse_databases(_require("PGDATABASES")),
    )
    storage = StorageConfig(
        endpoint=_require("MINIO_ENDPOINT"),
        access_key=_require("MINIO_ACCESS_KEY"),
        secret_key=_require("MINIO_SECRET_KEY"),
        bucket=_require("MINIO_BUCKET"),
        region=os.environ.get("MINIO_REGION", "us-east-1"),
    )
    return BackupConfig(postgres=postgres, storage=storage)
