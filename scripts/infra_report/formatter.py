from datetime import datetime, timezone

from .collectors.backup import BackupInfo
from .collectors.cpu import CpuInfo
from .collectors.disk import DiskPartition
from .collectors.docker import DockerInfo
from .collectors.memory import MemoryInfo
from .collectors.storage import StorageUsage
from .config import Thresholds


def _format_uptime(seconds: float) -> str:
    days = int(seconds // 86400)
    hours = int((seconds % 86400) // 3600)
    minutes = int((seconds % 3600) // 60)
    parts: list[str] = []
    if days:
        parts.append(f"{days}d")
    if hours:
        parts.append(f"{hours}h")
    parts.append(f"{minutes}m")
    return " ".join(parts)


def _format_age(timestamp: datetime) -> str:
    if timestamp.tzinfo is None:
        timestamp = timestamp.replace(tzinfo=timezone.utc)
    delta = datetime.now(timezone.utc) - timestamp
    hours = delta.total_seconds() / 3600
    if hours < 1:
        return f"{int(delta.total_seconds() / 60)}min atras"
    if hours < 24:
        return f"{hours:.1f}h atras"
    return f"{int(hours / 24)}d atras"


def _truncate_command(cmd: str, max_len: int = 35) -> str:
    if len(cmd) <= max_len:
        return cmd
    return cmd[: max_len - 1] + "…"


def _memory_icon(percent: float, t: Thresholds) -> str:
    if percent >= t.memory_critical_percent:
        return "[CRIT]"
    if percent >= t.memory_warn_percent:
        return "[WARN]"
    return "[OK]"


def _disk_icon(percent: float, t: Thresholds) -> str:
    if percent >= t.disk_critical_percent:
        return "[CRIT]"
    if percent >= t.disk_warn_percent:
        return "[WARN]"
    return "[OK]"


def _cpu_icon(load_per_cpu: float, t: Thresholds) -> str:
    if load_per_cpu >= t.load_warn_per_cpu:
        return "[WARN]"
    return "[OK]"


def build_message(
    memory: MemoryInfo,
    disks: list[DiskPartition],
    cpu: CpuInfo,
    docker: DockerInfo,
    storage: StorageUsage,
    backup: BackupInfo | None,
    thresholds: Thresholds,
) -> str:
    today = datetime.now().strftime("%d/%m/%Y")
    lines: list[str] = [
        f"<b>INFRA REPORT — {today}</b>",
        f"<i>Snapshot diario do servidor srv986128</i>",
        "",
    ]

    # CPU
    lines.append(
        f"{_cpu_icon(cpu.load_per_cpu_1m, thresholds)} <b>CPU</b> "
        f"({cpu.cpu_count} cores)"
    )
    lines.append(
        f"  Load: {cpu.load_1m:.2f} / {cpu.load_5m:.2f} / {cpu.load_15m:.2f} (1m/5m/15m)"
    )
    lines.append(f"  Uptime: {_format_uptime(cpu.uptime_seconds)}")
    lines.append("")

    # Memory
    lines.append(
        f"{_memory_icon(memory.used_percent, thresholds)} <b>RAM</b> "
        f"({memory.used_percent:.1f}%)"
    )
    lines.append(
        f"  Usado: {memory.used_mb / 1024:.1f} GB / {memory.total_mb / 1024:.1f} GB"
    )
    lines.append(f"  Disponivel: {memory.available_mb / 1024:.1f} GB")
    if memory.swap_total_mb > 0:
        swap_pct = (memory.swap_used_mb / memory.swap_total_mb) * 100
        lines.append(
            f"  Swap: {memory.swap_used_mb / 1024:.1f} GB / "
            f"{memory.swap_total_mb / 1024:.1f} GB ({swap_pct:.0f}%)"
        )
    if memory.top_processes:
        lines.append(f"  <i>Top processos por RAM:</i>")
        for proc in memory.top_processes:
            lines.append(
                f"  • {proc.rss_mb:.0f} MB — <code>{_truncate_command(proc.command)}</code>"
            )
    lines.append("")

    # Disk
    lines.append(f"<b>DISCO</b>")
    for part in disks:
        icon = _disk_icon(part.used_percent, thresholds)
        lines.append(
            f"{icon} <code>{part.mountpoint}</code> — "
            f"{part.used_gb:.1f} / {part.total_gb:.1f} GB ({part.used_percent:.1f}%)"
        )
        lines.append(f"  Livre: {part.free_gb:.1f} GB")
    lines.append("")

    # Docker
    lines.append(f"<b>DOCKER</b>")
    lines.append(
        f"  Containers: {docker.running} rodando / {docker.total} total "
        f"({docker.stopped} parados)"
    )
    if docker.top_by_memory:
        lines.append(f"  <i>Top por RAM:</i>")
        for c in docker.top_by_memory:
            lines.append(
                f"  • {c.mem_mb:.0f} MB ({c.mem_percent:.1f}%) — <code>{c.name}</code>"
            )
    if docker.top_by_cpu:
        lines.append(f"  <i>Top por CPU:</i>")
        for c in docker.top_by_cpu:
            if c.cpu_percent < 0.1:
                continue
            lines.append(
                f"  • {c.cpu_percent:.1f}% — <code>{c.name}</code>"
            )
    lines.append("")

    # Storage (Docker)
    lines.append(f"<b>STORAGE DOCKER</b>")
    lines.append(
        f"  Imagens: {storage.images_total} ({storage.images_size_gb:.1f} GB) — "
        f"reciclavel: {storage.images_reclaimable_gb:.1f} GB"
    )
    lines.append(
        f"  Volumes: {storage.volumes_total} ({storage.volumes_size_gb:.1f} GB) — "
        f"reciclavel: {storage.volumes_reclaimable_gb:.1f} GB"
    )
    if storage.build_cache_gb > 0:
        lines.append(f"  Build cache: {storage.build_cache_gb:.1f} GB")
    lines.append("")

    # Backup
    if backup is not None:
        lines.append(f"<b>BACKUP (MinIO)</b>")
        if backup.error:
            lines.append(f"  Erro ao consultar: {backup.error[:80]}")
        elif backup.found:
            age = _format_age(backup.last_backup_at) if backup.last_backup_at else "?"
            lines.append(
                f"  Ultimo: {backup.last_backup_at.strftime('%d/%m %H:%M UTC') if backup.last_backup_at else '?'} ({age})"
            )
            lines.append(
                f"  Total: {backup.total_objects} objetos / {backup.total_size_gb:.2f} GB"
            )
        else:
            lines.append(f"  Bucket vazio ou sem acesso")

    return "\n".join(lines)
