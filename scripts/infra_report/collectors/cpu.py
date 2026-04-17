import logging
import os
from dataclasses import dataclass

logger = logging.getLogger(__name__)


@dataclass(frozen=True)
class CpuInfo:
    cpu_count: int
    load_1m: float
    load_5m: float
    load_15m: float
    uptime_seconds: float
    load_per_cpu_1m: float


def _read_uptime() -> float:
    try:
        with open("/proc/uptime") as f:
            return float(f.read().split()[0])
    except Exception as e:
        logger.warning("Failed to read uptime: %s", e)
        return 0.0


def collect() -> CpuInfo:
    cpu_count = os.cpu_count() or 1
    load_1m, load_5m, load_15m = os.getloadavg()
    return CpuInfo(
        cpu_count=cpu_count,
        load_1m=load_1m,
        load_5m=load_5m,
        load_15m=load_15m,
        uptime_seconds=_read_uptime(),
        load_per_cpu_1m=load_1m / cpu_count,
    )
