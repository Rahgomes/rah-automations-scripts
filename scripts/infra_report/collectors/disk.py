import logging
import shutil
from dataclasses import dataclass

logger = logging.getLogger(__name__)


@dataclass(frozen=True)
class DiskPartition:
    mountpoint: str
    total_gb: float
    used_gb: float
    free_gb: float
    used_percent: float


def _read_mountpoints() -> list[str]:
    """Return relevant mountpoints from /proc/mounts (skip pseudo filesystems)."""
    skip_fstypes = {
        "proc", "sysfs", "cgroup", "cgroup2", "devpts", "tmpfs", "devtmpfs",
        "mqueue", "overlay", "squashfs", "fuse.lxcfs", "binfmt_misc",
        "autofs", "configfs", "fusectl", "pstore", "ramfs", "tracefs",
        "debugfs", "bpf", "hugetlbfs", "rpc_pipefs", "nsfs", "fuse.gvfsd-fuse",
    }
    mountpoints: list[str] = []
    seen: set[str] = set()
    try:
        with open("/proc/mounts") as f:
            for line in f:
                parts = line.split()
                if len(parts) < 3:
                    continue
                mountpoint, fstype = parts[1], parts[2]
                if fstype in skip_fstypes:
                    continue
                if mountpoint in seen:
                    continue
                seen.add(mountpoint)
                mountpoints.append(mountpoint)
    except Exception as e:
        logger.warning("Failed to read /proc/mounts: %s", e)
        return ["/"]
    return mountpoints or ["/"]


def collect() -> list[DiskPartition]:
    partitions: list[DiskPartition] = []
    for mountpoint in _read_mountpoints():
        try:
            usage = shutil.disk_usage(mountpoint)
        except (OSError, PermissionError) as e:
            logger.debug("Skipping %s: %s", mountpoint, e)
            continue
        if usage.total == 0:
            continue
        partitions.append(DiskPartition(
            mountpoint=mountpoint,
            total_gb=usage.total / (1024**3),
            used_gb=usage.used / (1024**3),
            free_gb=usage.free / (1024**3),
            used_percent=(usage.used / usage.total) * 100,
        ))
    return partitions
