import logging
import subprocess
from dataclasses import dataclass, field

logger = logging.getLogger(__name__)


@dataclass(frozen=True)
class ContainerStat:
    name: str
    cpu_percent: float
    mem_mb: float
    mem_percent: float


@dataclass(frozen=True)
class DockerInfo:
    total: int
    running: int
    stopped: int
    top_by_memory: list[ContainerStat] = field(default_factory=list)
    top_by_cpu: list[ContainerStat] = field(default_factory=list)


def _count_containers() -> tuple[int, int, int]:
    """Return (total, running, stopped)."""
    try:
        all_result = subprocess.run(
            ["docker", "ps", "-aq"],
            capture_output=True,
            text=True,
            timeout=10,
        )
        running_result = subprocess.run(
            ["docker", "ps", "-q"],
            capture_output=True,
            text=True,
            timeout=10,
        )
        total = len([l for l in all_result.stdout.strip().split("\n") if l])
        running = len([l for l in running_result.stdout.strip().split("\n") if l])
        return total, running, total - running
    except Exception as e:
        logger.warning("Failed to count containers: %s", e)
        return 0, 0, 0


def _parse_size_to_mb(size_str: str) -> float:
    """Parse '123.4MiB' or '1.2GiB' to MB. Returns 0 on failure."""
    size_str = size_str.strip()
    try:
        if size_str.endswith("GiB"):
            return float(size_str[:-3]) * 1024
        if size_str.endswith("MiB"):
            return float(size_str[:-3])
        if size_str.endswith("KiB"):
            return float(size_str[:-3]) / 1024
        if size_str.endswith("B"):
            return float(size_str[:-1]) / (1024 * 1024)
    except ValueError:
        pass
    return 0.0


def _parse_percent(pct_str: str) -> float:
    try:
        return float(pct_str.strip().rstrip("%"))
    except ValueError:
        return 0.0


def _get_container_stats() -> list[ContainerStat]:
    try:
        result = subprocess.run(
            [
                "docker", "stats", "--no-stream",
                "--format", "{{.Name}}|{{.CPUPerc}}|{{.MemUsage}}|{{.MemPerc}}",
            ],
            capture_output=True,
            text=True,
            timeout=30,
        )
        if result.returncode != 0:
            return []
        stats: list[ContainerStat] = []
        for line in result.stdout.strip().split("\n"):
            if not line:
                continue
            parts = line.split("|")
            if len(parts) < 4:
                continue
            name = parts[0]
            cpu_pct = _parse_percent(parts[1])
            # MemUsage format: "123.4MiB / 7.7GiB"
            mem_used_str = parts[2].split("/")[0].strip()
            mem_mb = _parse_size_to_mb(mem_used_str)
            mem_pct = _parse_percent(parts[3])
            stats.append(ContainerStat(
                name=name,
                cpu_percent=cpu_pct,
                mem_mb=mem_mb,
                mem_percent=mem_pct,
            ))
        return stats
    except Exception as e:
        logger.warning("Failed to get container stats: %s", e)
        return []


def collect(top_n: int = 5) -> DockerInfo:
    total, running, stopped = _count_containers()
    stats = _get_container_stats()
    top_mem = sorted(stats, key=lambda s: s.mem_mb, reverse=True)[:top_n]
    top_cpu = sorted(stats, key=lambda s: s.cpu_percent, reverse=True)[:top_n]
    return DockerInfo(
        total=total,
        running=running,
        stopped=stopped,
        top_by_memory=top_mem,
        top_by_cpu=top_cpu,
    )
