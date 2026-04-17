from scripts.shared import telegram

from .checker import CheckResult, DiskStatus, SslStatus


def notify_service_down(result: CheckResult, attempt: int, max_retries: int) -> None:
    status = f"HTTP {result.status_code}" if result.status_code else result.error
    telegram.send_text_message(
        f"<b>{result.service.name}</b> caiu ({status})\n"
        f"Tentativa {attempt}/{max_retries} de recuperacao..."
    )


def notify_service_recovered(
    result: CheckResult,
    attempt: int,
    response_time_ms: float,
) -> None:
    telegram.send_text_message(
        f"<b>{result.service.name}</b> restaurado na tentativa {attempt}\n"
        f"Tempo de resposta: {response_time_ms:.0f}ms"
    )


def notify_service_failed(result: CheckResult, max_retries: int) -> None:
    status = f"HTTP {result.status_code}" if result.status_code else result.error
    telegram.send_text_message(
        f"<b>{result.service.name}</b> nao recuperou apos {max_retries} tentativas ({status})\n"
        f"Recuperacao automatica INTERROMPIDA\n"
        f"Ramon, precisa de acao manual!"
    )


def notify_disk_warning(disk: DiskStatus) -> None:
    telegram.send_text_message(
        f"<b>Disco em {disk.used_percent:.1f}%</b>\n"
        f"Usado: {disk.used_gb:.1f} GB / {disk.total_gb:.1f} GB\n"
        f"Livre: {disk.free_gb:.1f} GB"
    )


def notify_docker_down() -> None:
    telegram.send_text_message(
        "<b>Docker daemon nao responde!</b>\n"
        "Nenhum container pode ser verificado ou recuperado.\n"
        "Ramon, precisa de acao manual!"
    )


def notify_ssl_expiring(ssl_status: SslStatus) -> None:
    telegram.send_text_message(
        f"<b>Certificado SSL expirando</b>\n"
        f"Dominio: <code>{ssl_status.domain}</code>\n"
        f"Expira em: {ssl_status.days_remaining} dias\n"
        f"Data: {ssl_status.expires_at.strftime('%d/%m/%Y') if ssl_status.expires_at else 'N/A'}"
    )
