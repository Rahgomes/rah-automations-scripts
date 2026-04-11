from dataclasses import dataclass

from scripts.shared import telegram


@dataclass
class BackupResult:
    database: str
    success: bool
    size_bytes: int = 0
    duration_seconds: float = 0.0
    object_key: str = ""
    error: str = ""


def _format_bytes(size: int) -> str:
    if size <= 0:
        return "0 B"
    value = float(size)
    for unit in ("B", "KB", "MB", "GB"):
        if value < 1024:
            return f"{value:.1f} {unit}"
        value /= 1024
    return f"{value:.1f} TB"


def _format_duration(seconds: float) -> str:
    if seconds < 60:
        return f"{seconds:.1f}s"
    minutes, sec = divmod(seconds, 60)
    return f"{int(minutes)}m {int(sec)}s"


def notify_start(databases: list[str]) -> None:
    count = len(databases)
    plural = "s" if count > 1 else ""
    db_list = "\n".join(f"• <code>{db}</code>" for db in databases)
    message = (
        f"🟡 <b>BACKUP INICIADO</b>\n"
        f"{count} banco{plural} na fila:\n"
        f"{db_list}"
    )
    telegram.send_text_message(message)


def notify_summary(results: list[BackupResult]) -> None:
    total = len(results)
    successes = [r for r in results if r.success]
    failures = [r for r in results if not r.success]

    icon = "✅" if not failures else ("❌" if not successes else "⚠️")
    title = "BACKUP CONCLUÍDO" if not failures else (
        "BACKUP FALHOU" if not successes else "BACKUP PARCIAL"
    )

    total_size = sum(r.size_bytes for r in successes)
    total_duration = sum(r.duration_seconds for r in results)

    lines = [
        f"{icon} <b>{title}</b>",
        f"Sucesso: {len(successes)}/{total}",
        f"Tamanho total: {_format_bytes(total_size)}",
        f"Duração total: {_format_duration(total_duration)}",
        "━━━━━━━━━━━━━━━━━━━━",
    ]

    for r in results:
        if r.success:
            lines.append(
                f"✅ <code>{r.database}</code> — "
                f"{_format_bytes(r.size_bytes)} em {_format_duration(r.duration_seconds)}"
            )
        else:
            lines.append(f"❌ <code>{r.database}</code> — {r.error}")

    telegram.send_text_message("\n".join(lines))
