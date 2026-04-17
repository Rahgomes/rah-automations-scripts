import logging
import ssl
import socket
import time
from dataclasses import dataclass
from datetime import datetime, timezone
from urllib.parse import urlparse

import requests

from .config import HealthcheckConfig, Service

logger = logging.getLogger(__name__)


@dataclass
class CheckResult:
    service: Service
    healthy: bool
    status_code: int = 0
    response_time_ms: float = 0.0
    error: str = ""


@dataclass
class DiskStatus:
    total_gb: float
    used_gb: float
    free_gb: float
    used_percent: float


@dataclass
class SslStatus:
    domain: str
    expires_at: datetime | None = None
    days_remaining: int = 0
    error: str = ""


def check_service(service: Service, timeout: int) -> CheckResult:
    started = time.monotonic()
    try:
        response = requests.get(
            service.url,
            timeout=timeout,
            allow_redirects=False,
            verify=True,
        )
        elapsed = (time.monotonic() - started) * 1000
        healthy = response.status_code in service.accept_codes
        if not healthy:
            logger.warning(
                "%s returned HTTP %d (expected %s)",
                service.name,
                response.status_code,
                service.accept_codes,
            )
        return CheckResult(
            service=service,
            healthy=healthy,
            status_code=response.status_code,
            response_time_ms=elapsed,
        )
    except requests.Timeout:
        elapsed = (time.monotonic() - started) * 1000
        logger.warning("%s timed out after %dms", service.name, elapsed)
        return CheckResult(
            service=service,
            healthy=False,
            response_time_ms=elapsed,
            error="timeout",
        )
    except Exception as e:
        elapsed = (time.monotonic() - started) * 1000
        logger.warning("%s request failed: %s", service.name, e)
        return CheckResult(
            service=service,
            healthy=False,
            response_time_ms=elapsed,
            error=str(e),
        )


def check_disk() -> DiskStatus:
    import shutil

    usage = shutil.disk_usage("/")
    total_gb = usage.total / (1024**3)
    used_gb = usage.used / (1024**3)
    free_gb = usage.free / (1024**3)
    used_percent = (usage.used / usage.total) * 100
    return DiskStatus(
        total_gb=total_gb,
        used_gb=used_gb,
        free_gb=free_gb,
        used_percent=used_percent,
    )


def check_docker_daemon() -> bool:
    import subprocess

    try:
        result = subprocess.run(
            ["docker", "info"],
            capture_output=True,
            timeout=10,
        )
        return result.returncode == 0
    except Exception as e:
        logger.error("Docker daemon check failed: %s", e)
        return False


def check_ssl_expiry(url: str, warn_days: int) -> SslStatus | None:
    parsed = urlparse(url)
    if parsed.scheme != "https":
        return None
    domain = parsed.hostname
    if not domain:
        return None
    try:
        context = ssl.create_default_context()
        with socket.create_connection((domain, 443), timeout=5) as sock:
            with context.wrap_socket(sock, server_hostname=domain) as tls:
                cert = tls.getpeercert()
        if not cert:
            return SslStatus(domain=domain, error="no certificate")
        expires_str = cert["notAfter"]
        expires_at = datetime.strptime(expires_str, "%b %d %H:%M:%S %Y %Z").replace(
            tzinfo=timezone.utc,
        )
        days_remaining = (expires_at - datetime.now(timezone.utc)).days
        return SslStatus(
            domain=domain,
            expires_at=expires_at,
            days_remaining=days_remaining,
        )
    except Exception as e:
        return SslStatus(domain=domain, error=str(e))
