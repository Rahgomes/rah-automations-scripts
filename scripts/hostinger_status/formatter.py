from .client import StatusSnapshot

STATUS_ICONS = {
    "operational": "[OK]",
    "degraded_performance": "[WARN]",
    "partial_outage": "[WARN]",
    "major_outage": "[CRIT]",
    "under_maintenance": "[MAINT]",
}


def status_icon(status: str) -> str:
    return STATUS_ICONS.get(status, "[?]")


def humanize_status(status: str) -> str:
    return status.replace("_", " ").title()


def build_change_message(
    snapshot: StatusSnapshot,
    previous_status: str | None,
    status_page_url: str,
) -> str:
    component = snapshot.component
    icon = status_icon(component.status)
    current = humanize_status(component.status)

    if previous_status is None:
        header = f"{icon} <b>Hostinger {component.name}</b>\nEstado inicial: {current}"
    else:
        prev = humanize_status(previous_status)
        header = (
            f"{icon} <b>Hostinger {component.name}</b>\n"
            f"Mudanca: {prev} -> {current}"
        )

    lines = [header]

    relevant = [i for i in snapshot.incidents if i.status != "resolved"]
    if relevant:
        lines.append("\n<b>Incidentes ativos:</b>")
        for inc in relevant[:5]:
            lines.append(
                f"- {inc.name} ({inc.impact}) — {inc.status}"
            )

    lines.append(f"\n<a href=\"{status_page_url}\">Status page</a>")
    return "\n".join(lines)
