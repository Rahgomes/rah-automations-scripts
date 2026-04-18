from dataclasses import dataclass


@dataclass(frozen=True)
class Config:
    summary_url: str = "https://statuspage.hostinger.com/api/v2/summary.json"
    status_page_url: str = "https://statuspage.hostinger.com"
    state_file: str = "/var/lib/hostinger-status/state.json"
    watched_component: str = "BR Datacenter"
    http_timeout: int = 15


def load() -> Config:
    return Config()
