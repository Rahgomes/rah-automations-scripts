import logging
import sys
import time
from pathlib import Path

from . import config
from .checker import check_disk, check_docker_daemon, check_service, check_ssl_expiry
from .notifier import (
    notify_disk_warning,
    notify_docker_down,
    notify_service_down,
    notify_service_failed,
    notify_service_recovered,
    notify_ssl_expiring,
)
from .recovery import attempt_recovery

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
)
logger = logging.getLogger(__name__)


def _read_retries(state_dir: Path, container: str) -> int:
    state_file = state_dir / f"{container}.retries"
    if state_file.exists():
        try:
            return int(state_file.read_text().strip())
        except ValueError:
            return 0
    return 0


def _write_retries(state_dir: Path, container: str, count: int) -> None:
    state_file = state_dir / f"{container}.retries"
    state_file.write_text(str(count))


def _clear_retries(state_dir: Path, container: str) -> None:
    state_file = state_dir / f"{container}.retries"
    state_file.unlink(missing_ok=True)


def main() -> int:
    logger.info("Starting healthcheck run")
    cfg = config.load()

    state_dir = Path(cfg.state_dir)
    state_dir.mkdir(parents=True, exist_ok=True)

    # Docker daemon check — if down, nothing works
    if not check_docker_daemon():
        logger.error("Docker daemon is not responding")
        notify_docker_down()
        return 1

    # Disk usage check
    disk = check_disk()
    logger.info(
        "Disk: %.1f%% used (%.1f GB free / %.1f GB total)",
        disk.used_percent,
        disk.free_gb,
        disk.total_gb,
    )
    disk_state = state_dir / "disk_warned"
    if disk.used_percent >= cfg.disk_warn_percent:
        if not disk_state.exists():
            notify_disk_warning(disk)
            disk_state.write_text("1")
    else:
        disk_state.unlink(missing_ok=True)

    # SSL expiry check (once per run, lightweight)
    checked_domains: set[str] = set()
    for service in cfg.services:
        ssl_status = check_ssl_expiry(service.url, cfg.ssl_warn_days)
        if ssl_status is None or ssl_status.domain in checked_domains:
            continue
        checked_domains.add(ssl_status.domain)
        if ssl_status.error:
            logger.warning("SSL check failed for %s: %s", ssl_status.domain, ssl_status.error)
        elif ssl_status.days_remaining <= cfg.ssl_warn_days:
            ssl_state = state_dir / f"ssl_{ssl_status.domain}.warned"
            if not ssl_state.exists():
                logger.warning(
                    "SSL cert for %s expires in %d days",
                    ssl_status.domain,
                    ssl_status.days_remaining,
                )
                notify_ssl_expiring(ssl_status)
                ssl_state.write_text("1")

    # Service checks
    for service in cfg.services:
        result = check_service(service, timeout=cfg.http_timeout)

        if result.healthy:
            logger.info(
                "%s OK (HTTP %d, %.0fms)",
                service.name,
                result.status_code,
                result.response_time_ms,
            )
            _clear_retries(state_dir, service.container)
            continue

        # Service is down
        retries = _read_retries(state_dir, service.container)
        if retries >= service.max_retries:
            continue

        retries += 1
        _write_retries(state_dir, service.container, retries)

        logger.warning(
            "%s DOWN — attempt %d/%d",
            service.name,
            retries,
            service.max_retries,
        )
        notify_service_down(result, retries, service.max_retries)

        attempt_recovery(service)
        time.sleep(cfg.recovery_wait)

        # Re-check after recovery
        recheck = check_service(service, timeout=cfg.http_timeout)
        if recheck.healthy:
            logger.info(
                "%s recovered (HTTP %d, %.0fms)",
                service.name,
                recheck.status_code,
                recheck.response_time_ms,
            )
            notify_service_recovered(result, retries, recheck.response_time_ms)
            _clear_retries(state_dir, service.container)
        elif retries >= service.max_retries:
            logger.error("%s failed to recover after %d attempts", service.name, retries)
            notify_service_failed(result, service.max_retries)

    logger.info("Healthcheck run completed")
    return 0


if __name__ == "__main__":
    sys.exit(main())
