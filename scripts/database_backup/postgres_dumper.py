import logging
import subprocess
import tempfile
from pathlib import Path

from .config import PostgresConfig

logger = logging.getLogger(__name__)

PG_DUMP_TIMEOUT = 3600  # 1 hour hard cap per database


STALE_DUMP_AGE_SECONDS = 2 * 3600  # acima do PG_DUMP_TIMEOUT, nunca pega dump em curso


def sweep_stale_dumps() -> int:
    """Remove dumps orfaos de execucoes anteriores que morreram sem rodar o finally.

    O cleanup normal vive no `finally` de _backup_single_database, mas ele nao roda
    quando o processo leva SIGKILL (OOM killer, timeout do agente). Cada orfao desses
    e um arquivo de varios GB parado em /tmp.

    So remove arquivos mais velhos que STALE_DUMP_AGE_SECONDS, que e maior que o
    PG_DUMP_TIMEOUT — assim nunca toca num dump que esteja sendo gerado agora.
    """
    import os
    import tempfile
    import time

    tmpdir = Path(tempfile.gettempdir())
    cutoff = time.time() - STALE_DUMP_AGE_SECONDS
    removed = 0
    freed = 0

    for candidate in tmpdir.glob("*.dump"):
        try:
            if not candidate.is_file() or candidate.is_symlink():
                continue
            stat = candidate.stat()
            if stat.st_mtime >= cutoff:
                continue
            size = stat.st_size
            candidate.unlink()
        except OSError as e:
            logger.warning("Nao consegui remover dump orfao '%s': %s", candidate, e)
            continue
        removed += 1
        freed += size
        logger.info("Removido dump orfao: %s (%s)", candidate.name, _format_bytes(size))

    if removed:
        logger.warning(
            "Limpei %d dump(s) orfao(s), liberando %s. "
            "Indica execucao anterior morta antes do cleanup (OOM ou timeout).",
            removed,
            _format_bytes(freed),
        )
    return removed


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
