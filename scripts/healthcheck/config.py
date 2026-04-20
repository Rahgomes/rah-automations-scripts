from dataclasses import dataclass
from enum import Enum


class RecoveryStrategy(Enum):
    COMPOSE = "compose"
    RESTART = "restart"
    NONE = "none"


@dataclass(frozen=True)
class Service:
    name: str
    url: str
    container: str
    strategy: RecoveryStrategy
    compose_dir: str = ""
    accept_codes: frozenset[int] = frozenset({200, 302, 307})
    max_retries: int = 3


@dataclass(frozen=True)
class HealthcheckConfig:
    services: list[Service]
    state_dir: str = "/var/lib/healthcheck"
    http_timeout: int = 10
    recovery_wait: int = 15
    disk_warn_percent: int = 85
    ssl_warn_days: int = 7


SERVICES: list[Service] = [
    # --- Infra ---
    Service(
        name="Dozzle",
        url="https://logs.ramongomessilva.com.br/",
        container="dozzle",
        strategy=RecoveryStrategy.COMPOSE,
        compose_dir="/opt/dozzle",
    ),
    Service(
        name="Homepage",
        url="https://home.ramongomessilva.com.br/",
        container="homepage",
        strategy=RecoveryStrategy.COMPOSE,
        compose_dir="/opt/homepage",
    ),
    Service(
        name="Uptime Kuma",
        url="https://monitor.ramongomessilva.com.br/",
        container="uptime-kuma",
        strategy=RecoveryStrategy.COMPOSE,
        compose_dir="/opt/uptime-kuma",
    ),
    Service(
        name="Docker Registry",
        url="https://registry.ramongomessilva.com.br/v2/",
        container="docker-registry",
        strategy=RecoveryStrategy.RESTART,
    ),
    Service(
        name="Registry UI",
        url="https://registry-ui.ramongomessilva.com.br/",
        container="docker-registry-ui",
        strategy=RecoveryStrategy.RESTART,
    ),
    Service(
        name="Keycloak",
        url="https://sso.nexalumedigital.com.br/",
        container="keycloak",
        strategy=RecoveryStrategy.RESTART,
    ),
    # --- Automacao ---
    Service(
        name="n8n",
        url="https://n8n.nexalumedigital.com.br/",
        container="n8n-o48ckswc8sok4scokoskws4c",
        strategy=RecoveryStrategy.RESTART,
    ),
    # --- Projetos ---
    Service(
        name="SiteCloner",
        url="https://site-cloner.ramongomessilva.com.br/",
        container="sitecloner",
        strategy=RecoveryStrategy.RESTART,
    ),
    Service(
        name="NexaLume DEV",
        url="https://dev.nexalumedigital.com.br/",
        container="nexalume-dev",
        strategy=RecoveryStrategy.RESTART,
    ),
    Service(
        name="NexaLume PROD",
        url="https://nexalumedigital.com.br/",
        container="nexalume-prod",
        strategy=RecoveryStrategy.RESTART,
    ),
    Service(
        name="MBA-RAG",
        url="https://mba-rag.ramongomessilva.com.br/",
        container="mba-rag",
        strategy=RecoveryStrategy.RESTART,
    ),
    # VideoInsight: Streamlit app responde internamente (localhost:8501) mas
    # Traefik nao roteia corretamente (WebSocket). Fix de infra pendente.
    # Service(
    #     name="VideoInsight",
    #     url="https://insta.ramongomessilva.com.br/",
    #     container="videoinsight",
    #     strategy=RecoveryStrategy.RESTART,
    # ),
    Service(
        name="Video Tools",
        url="https://video-tools.ramongomessilva.com.br/",
        container="video-tools",
        strategy=RecoveryStrategy.RESTART,
    ),
    Service(
        name="RAG NexaLume API",
        url="https://rag-site.nexalumedigital.com.br/health",
        container="rag-nexalume-api",
        strategy=RecoveryStrategy.RESTART,
    ),
]


def load() -> HealthcheckConfig:
    return HealthcheckConfig(services=SERVICES)
