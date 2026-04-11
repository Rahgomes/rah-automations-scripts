import logging
import subprocess

from .config import PostgresConfig

logger = logging.getLogger(__name__)

DISCOVERY_TIMEOUT = 60
DISCOVERY_QUERY = (
    "SELECT datname FROM pg_database "
    "WHERE datistemplate = false AND datallowconn = true "
    "ORDER BY datname;"
)


def list_databases(postgres: PostgresConfig) -> list[str]:
    """Query pg_database for non-template, connectable databases.

    Applies `excluded_databases` from config. Used only when the caller did
    not provide an explicit list via PGDATABASES.
    """
    command = [
        "psql",
        "--host", postgres.host,
        "--port", postgres.port,
        "--username", postgres.user,
        "--dbname", "postgres",
        "--no-align",
        "--tuples-only",
        "--no-psqlrc",
        "--command", DISCOVERY_QUERY,
    ]

    import os
    env = {
        "PGPASSWORD": postgres.password,
        "PATH": os.environ.get(
            "PATH", "/usr/local/sbin:/usr/local/bin:/usr/sbin:/usr/bin:/sbin:/bin"
        ),
    }

    logger.info("Auto-discovering databases on %s:%s", postgres.host, postgres.port)
    try:
        result = subprocess.run(
            command,
            env=env,
            check=True,
            capture_output=True,
            text=True,
            timeout=DISCOVERY_TIMEOUT,
        )
    except subprocess.CalledProcessError as e:
        raise RuntimeError(
            f"Failed to query pg_database: {e.stderr.strip()}"
        ) from e
    except subprocess.TimeoutExpired as e:
        raise RuntimeError("Database discovery query timed out") from e

    found = [line.strip() for line in result.stdout.splitlines() if line.strip()]
    kept = [db for db in found if db not in postgres.excluded_databases]
    skipped = sorted(set(found) - set(kept))

    logger.info(
        "Discovered %d database(s); %d kept after exclusion, %d skipped: %s",
        len(found),
        len(kept),
        len(skipped),
        ", ".join(skipped) if skipped else "(none)",
    )
    return kept


def resolve_databases(postgres: PostgresConfig) -> list[str]:
    """Return the final list of databases to back up.

    If PGDATABASES was provided, use it as-is (explicit wins over discovery).
    Otherwise, auto-discover from the server.
    """
    if postgres.explicit_databases:
        logger.info(
            "Using explicit PGDATABASES (%d): %s",
            len(postgres.explicit_databases),
            ", ".join(postgres.explicit_databases),
        )
        return postgres.explicit_databases
    return list_databases(postgres)
