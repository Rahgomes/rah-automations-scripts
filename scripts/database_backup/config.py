import os
from dataclasses import dataclass, field


DEFAULT_SYSTEM_DATABASES = frozenset({"postgres", "template0", "template1"})


@dataclass(frozen=True)
class PostgresConfig:
    host: str
    port: str
    user: str
    password: str
    explicit_databases: list[str] = field(default_factory=list)
    excluded_databases: frozenset[str] = field(default_factory=frozenset)


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


def _parse_csv(raw: str | None) -> list[str]:
    if not raw:
        return []
    return [item.strip() for item in raw.split(",") if item.strip()]


def load() -> BackupConfig:
    """Load and validate backup configuration from environment variables.

    PGDATABASES is optional: when empty, the script auto-discovers databases
    by querying pg_database at runtime. PGDATABASES_EXCLUDE accepts a CSV of
    database names to skip during auto-discovery (system databases are
    always excluded).
    """
    explicit = _parse_csv(os.environ.get("PGDATABASES"))
    excluded = frozenset(
        _parse_csv(os.environ.get("PGDATABASES_EXCLUDE"))
    ) | DEFAULT_SYSTEM_DATABASES

    postgres = PostgresConfig(
        host=_require("PGHOST"),
        port=os.environ.get("PGPORT", "5432"),
        user=_require("PGUSER"),
        password=_require("PGPASSWORD"),
        explicit_databases=explicit,
        excluded_databases=excluded,
    )
    storage = StorageConfig(
        endpoint=_require("MINIO_ENDPOINT"),
        access_key=_require("MINIO_ACCESS_KEY"),
        secret_key=_require("MINIO_SECRET_KEY"),
        bucket=_require("MINIO_BUCKET"),
        region=os.environ.get("MINIO_REGION", "us-east-1"),
    )
    return BackupConfig(postgres=postgres, storage=storage)
