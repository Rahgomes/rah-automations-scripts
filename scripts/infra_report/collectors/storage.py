import json
import logging
import subprocess
from dataclasses import dataclass

logger = logging.getLogger(__name__)


@dataclass(frozen=True)
class StorageUsage:
    images_total: int
    images_size_gb: float
    images_reclaimable_gb: float
    volumes_total: int
    volumes_size_gb: float
    volumes_reclaimable_gb: float
    build_cache_gb: float


def _parse_size_to_gb(size_str: str) -> float:
    """Parse Docker size strings to GB. Handles GB, MB, kB, B."""
    size_str = size_str.strip()
    try:
        if size_str.endswith("TB"):
            return float(size_str[:-2]) * 1024
        if size_str.endswith("GB"):
            return float(size_str[:-2])
        if size_str.endswith("MB"):
            return float(size_str[:-2]) / 1024
        if size_str.endswith("kB"):
            return float(size_str[:-2]) / (1024 * 1024)
        if size_str.endswith("B"):
            return float(size_str[:-1]) / (1024**3)
    except ValueError:
        pass
    return 0.0


def collect() -> StorageUsage:
    try:
        result = subprocess.run(
            ["docker", "system", "df", "--format", "json"],
            capture_output=True,
            text=True,
            timeout=15,
        )
        if result.returncode != 0:
            return StorageUsage(0, 0, 0, 0, 0, 0, 0)

        data = {"Images": {}, "Volumes": {}, "BuildCache": {}}
        for line in result.stdout.strip().split("\n"):
            if not line:
                continue
            try:
                entry = json.loads(line)
            except json.JSONDecodeError:
                continue
            entry_type = entry.get("Type", "")
            if entry_type == "Images":
                data["Images"] = entry
            elif entry_type == "Local Volumes":
                data["Volumes"] = entry
            elif entry_type == "Build Cache":
                data["BuildCache"] = entry

        return StorageUsage(
            images_total=int(data["Images"].get("TotalCount", 0) or 0),
            images_size_gb=_parse_size_to_gb(data["Images"].get("Size", "0B")),
            images_reclaimable_gb=_parse_size_to_gb(
                data["Images"].get("Reclaimable", "0B").split()[0]
            ),
            volumes_total=int(data["Volumes"].get("TotalCount", 0) or 0),
            volumes_size_gb=_parse_size_to_gb(data["Volumes"].get("Size", "0B")),
            volumes_reclaimable_gb=_parse_size_to_gb(
                data["Volumes"].get("Reclaimable", "0B").split()[0]
            ),
            build_cache_gb=_parse_size_to_gb(data["BuildCache"].get("Size", "0B")),
        )
    except Exception as e:
        logger.warning("Failed to get storage usage: %s", e)
        return StorageUsage(0, 0, 0, 0, 0, 0, 0)
