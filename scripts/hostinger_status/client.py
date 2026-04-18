import logging
from dataclasses import dataclass

import requests

logger = logging.getLogger(__name__)

USER_AGENT = "rah-automations-hostinger-status/1.0"


@dataclass(frozen=True)
class ComponentStatus:
    name: str
    status: str
    description: str | None


@dataclass(frozen=True)
class Incident:
    name: str
    status: str
    impact: str
    created_at: str
    shortlink: str


@dataclass(frozen=True)
class StatusSnapshot:
    component: ComponentStatus
    incidents: list[Incident]


def fetch_snapshot(summary_url: str, watched_component: str, timeout: int) -> StatusSnapshot:
    response = requests.get(
        summary_url,
        timeout=timeout,
        headers={"User-Agent": USER_AGENT, "Accept": "application/json"},
    )
    response.raise_for_status()
    data = response.json()

    component = _find_component(data.get("components", []), watched_component)
    incidents = [_parse_incident(i) for i in data.get("incidents", [])]

    return StatusSnapshot(component=component, incidents=incidents)


def _find_component(components: list[dict], name: str) -> ComponentStatus:
    for c in components:
        if c.get("name") == name:
            return ComponentStatus(
                name=c["name"],
                status=c["status"],
                description=c.get("description"),
            )
    raise LookupError(f"Component '{name}' not found in Hostinger summary")


def _parse_incident(raw: dict) -> Incident:
    return Incident(
        name=raw.get("name", ""),
        status=raw.get("status", ""),
        impact=raw.get("impact", "none"),
        created_at=raw.get("created_at", ""),
        shortlink=raw.get("shortlink", ""),
    )
