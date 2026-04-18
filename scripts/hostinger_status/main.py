import logging
import sys
from datetime import datetime, timezone

from scripts.shared import telegram

from . import client, config, formatter, state

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
)
logger = logging.getLogger(__name__)


def main() -> int:
    cfg = config.load()
    logger.info("Fetching Hostinger status summary")

    try:
        snapshot = client.fetch_snapshot(
            cfg.summary_url, cfg.watched_component, cfg.http_timeout
        )
    except Exception as e:
        logger.error("Failed to fetch Hostinger status: %s", e)
        return 1

    current_status = snapshot.component.status
    logger.info("%s status: %s", cfg.watched_component, current_status)

    previous = state.load(cfg.state_file)
    previous_status = previous.last_status if previous else None

    if previous_status == current_status:
        logger.info("No change — staying silent")
        return 0

    logger.info(
        "Status changed: %s -> %s — sending Telegram notification",
        previous_status,
        current_status,
    )

    message = formatter.build_change_message(
        snapshot=snapshot,
        previous_status=previous_status,
        status_page_url=cfg.status_page_url,
    )

    if not telegram.send_text_message(message):
        logger.error("Failed to send Telegram message")
        return 1

    state.save(
        cfg.state_file,
        state.State(
            last_status=current_status,
            last_changed_at=datetime.now(timezone.utc).isoformat(),
        ),
    )
    logger.info("State persisted")
    return 0


if __name__ == "__main__":
    sys.exit(main())
