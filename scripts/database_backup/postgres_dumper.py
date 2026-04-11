import logging
import subprocess
import tempfile
from pathlib import Path

from .config import PostgresConfig

logger = logging.getLogger(__name__)

PG_DUMP_TIMEOUT = 3600  # 1 hour hard cap per database


def dump_database(postgres: PostgresConfig, database: str) -> Path:
    """Run pg_dump in custom format for a single database.

    Returns the path to the temporary .dump file. Caller is responsible
    for removing it after upload.
    """
    tmp = tempfile.NamedTemporaryFile(
        prefix=f"{database}_",
        suffix=".dump",
        delete=False,
    )
    tmp.close()
    output_path = Path(tmp.name)

    command = [
        "pg_dump",
        "--host", postgres.host,
        "--port", postgres.port,
        "--username", postgres.user,
        "--dbname", database,
        "--format=custom",
        "--no-owner",
        "--no-privileges",
        "--file", str(output_path),
    ]

    logger.info("Running pg_dump for database '%s'", database)
    env = {"PGPASSWORD": postgres.password, "PATH": _safe_path()}

    try:
        subprocess.run(
            command,
            env=env,
            check=True,
            capture_output=True,
            text=True,
            timeout=PG_DUMP_TIMEOUT,
        )
    except subprocess.CalledProcessError as e:
        output_path.unlink(missing_ok=True)
        logger.error("pg_dump failed for '%s': %s", database, e.stderr)
        raise RuntimeError(f"pg_dump failed for {database}: {e.stderr.strip()}") from e
    except subprocess.TimeoutExpired as e:
        output_path.unlink(missing_ok=True)
        logger.error("pg_dump timed out for '%s' after %ds", database, PG_DUMP_TIMEOUT)
        raise RuntimeError(f"pg_dump timed out for {database}") from e

    size_bytes = output_path.stat().st_size
    logger.info(
        "pg_dump completed for '%s' (%s)",
        database,
        _format_bytes(size_bytes),
    )
    return output_path


def _safe_path() -> str:
    import os
    return os.environ.get("PATH", "/usr/local/sbin:/usr/local/bin:/usr/sbin:/usr/bin:/sbin:/bin")


def _format_bytes(size: int) -> str:
    for unit in ("B", "KB", "MB", "GB"):
        if size < 1024:
            return f"{size:.1f} {unit}"
        size /= 1024
    return f"{size:.1f} TB"
