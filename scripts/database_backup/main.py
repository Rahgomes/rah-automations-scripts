import logging
import sys
import time
from datetime import datetime, timezone
from pathlib import Path

from . import config, postgres_dumper, storage_uploader
from .notifier import BackupResult, notify_start, notify_summary

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
)
logger = logging.getLogger(__name__)


def _build_object_key(database: str, timestamp: datetime) -> str:
    date_prefix = timestamp.strftime("%Y/%m/%d")
    filename = f"{database}_{timestamp.strftime('%Y%m%d_%H%M%S')}.dump"
    return f"{database}/{date_prefix}/{filename}"


def _backup_single_database(
    cfg: config.BackupConfig,
    database: str,
    timestamp: datetime,
) -> BackupResult:
    started = time.monotonic()
    dump_path: Path | None = None
    try:
        dump_path = postgres_dumper.dump_database(cfg.postgres, database)
        size_bytes = dump_path.stat().st_size
        object_key = _build_object_key(database, timestamp)
        storage_uploader.upload(cfg.storage, dump_path, object_key)
        return BackupResult(
            database=database,
            success=True,
            size_bytes=size_bytes,
            duration_seconds=time.monotonic() - started,
            object_key=object_key,
        )
    except Exception as e:
        logger.exception("Backup failed for database '%s'", database)
        return BackupResult(
            database=database,
            success=False,
            duration_seconds=time.monotonic() - started,
            error=str(e),
        )
    finally:
        if dump_path is not None:
            dump_path.unlink(missing_ok=True)


def main() -> int:
    logger.info("Starting database backup run")
    try:
        cfg = config.load()
    except RuntimeError as e:
        logger.error("Configuration error: %s", e)
        return 1

    databases = cfg.postgres.databases
    logger.info("Will back up %d database(s): %s", len(databases), ", ".join(databases))

    notify_start(databases)

    timestamp = datetime.now(timezone.utc)
    results = [
        _backup_single_database(cfg, db, timestamp)
        for db in databases
    ]

    notify_summary(results)

    all_ok = all(r.success for r in results)
    logger.info("Backup run completed (success=%s)", all_ok)
    return 0 if all_ok else 1


if __name__ == "__main__":
    sys.exit(main())
