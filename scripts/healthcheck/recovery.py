import logging
import subprocess

from .config import RecoveryStrategy, Service

logger = logging.getLogger(__name__)


def attempt_recovery(service: Service) -> bool:
    if service.strategy == RecoveryStrategy.NONE:
        logger.info("No recovery strategy for %s — skipping", service.name)
        return False

    if service.strategy == RecoveryStrategy.COMPOSE:
        return _recover_compose(service)

    if service.strategy == RecoveryStrategy.RESTART:
        return _recover_restart(service)

    return False


def _recover_compose(service: Service) -> bool:
    if not service.compose_dir:
        logger.error("No compose_dir for %s", service.name)
        return False
    try:
        result = subprocess.run(
            ["docker", "compose", "up", "-d", "--force-recreate", service.container],
            cwd=service.compose_dir,
            capture_output=True,
            text=True,
            timeout=60,
        )
        if result.returncode == 0:
            logger.info("Compose recreate succeeded for %s", service.name)
            return True
        logger.error(
            "Compose recreate failed for %s: %s",
            service.name,
            result.stderr,
        )
        return False
    except Exception as e:
        logger.error("Compose recovery error for %s: %s", service.name, e)
        return False


def _recover_restart(service: Service) -> bool:
    try:
        result = subprocess.run(
            ["docker", "restart", service.container],
            capture_output=True,
            text=True,
            timeout=30,
        )
        if result.returncode == 0:
            logger.info("Docker restart succeeded for %s", service.name)
            return True
        logger.error(
            "Docker restart failed for %s: %s",
            service.name,
            result.stderr,
        )
        return False
    except Exception as e:
        logger.error("Restart recovery error for %s: %s", service.name, e)
        return False
