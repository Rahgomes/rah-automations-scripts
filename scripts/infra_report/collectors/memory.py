import logging
import subprocess
from dataclasses import dataclass, field

logger = logging.getLogger(__name__)


@dataclass(frozen=True)
class TopProcess:
    pid: int
    user: str
    rss_mb: float
    command: str


@dataclass(frozen=True)
class MemoryInfo:
    total_mb: float
    used_mb: float
    free_mb: float
    available_mb: float
    used_percent: float
    swap_total_mb: float
    swap_used_mb: float
    top_processes: list[TopProcess] = field(default_factory=list)


def _parse_meminfo() -> dict[str, int]:
    """Parse /proc/meminfo into a dict of kB values."""
    values: dict[str, int] = {}
    with open("/proc/meminfo") as f:
        for line in f:
            parts = line.split()
            if len(parts) >= 2:
                key = parts[0].rstrip(":")
                values[key] = int(parts[1])
    return values


def _get_top_processes(top_n: int) -> list[TopProcess]:
    try:
        result = subprocess.run(
            ["ps", "axo", "pid,user,rss,comm", "--sort=-rss", "--no-headers"],
            capture_output=True,
            text=True,
            timeout=10,
        )
        if result.returncode != 0:
            return []
        processes: list[TopProcess] = []
        for line in result.stdout.strip().split("\n")[:top_n]:
            parts = line.split(maxsplit=3)
            if len(parts) < 4:
                continue
            try:
                processes.append(TopProcess(
                    pid=int(parts[0]),
                    user=parts[1],
                    rss_mb=int(parts[2]) / 1024,
                    command=parts[3].strip(),
                ))
            except ValueError:
                continue
        return processes
    except Exception as e:
        logger.warning("Failed to get top processes: %s", e)
        return []


def collect(top_n: int = 5) -> MemoryInfo:
    mem = _parse_meminfo()
    total_kb = mem.get("MemTotal", 0)
    free_kb = mem.get("MemFree", 0)
    available_kb = mem.get("MemAvailable", 0)
    swap_total_kb = mem.get("SwapTotal", 0)
    swap_free_kb = mem.get("SwapFree", 0)

    used_kb = total_kb - available_kb
    used_percent = (used_kb / total_kb * 100) if total_kb else 0

    return MemoryInfo(
        total_mb=total_kb / 1024,
        used_mb=used_kb / 1024,
        free_mb=free_kb / 1024,
        available_mb=available_kb / 1024,
        used_percent=used_percent,
        swap_total_mb=swap_total_kb / 1024,
        swap_used_mb=(swap_total_kb - swap_free_kb) / 1024,
        top_processes=_get_top_processes(top_n),
    )
