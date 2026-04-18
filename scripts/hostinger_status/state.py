import json
import logging
import os
from dataclasses import dataclass

logger = logging.getLogger(__name__)


@dataclass(frozen=True)
class State:
    last_status: str
    last_changed_at: str


def load(path: str) -> State | None:
    if not os.path.exists(path):
        return None
    try:
        with open(path, "r") as f:
            raw = json.load(f)
        return State(
            last_status=raw["last_status"],
            last_changed_at=raw["last_changed_at"],
        )
    except (json.JSONDecodeError, KeyError) as e:
        logger.warning("Invalid state file at %s: %s — treating as absent", path, e)
        return None


def save(path: str, state: State) -> None:
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, "w") as f:
        json.dump(
            {
                "last_status": state.last_status,
                "last_changed_at": state.last_changed_at,
            },
            f,
        )
