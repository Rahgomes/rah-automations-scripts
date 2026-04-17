import logging
import sys

from scripts.shared import telegram

from . import config, formatter
from .collectors import backup, cpu, disk, docker, memory, storage

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
)
logger = logging.getLogger(__name__)


def main() -> int:
    logger.info("Starting infra report run")
    cfg = config.load()
    t = cfg.thresholds

    logger.info("Collecting CPU info")
    cpu_info = cpu.collect()

    logger.info("Collecting memory info")
    memory_info = memory.collect(top_n=t.container_top_n)

    logger.info("Collecting disk info")
    disk_info = disk.collect()

    logger.info("Collecting Docker info")
    docker_info = docker.collect(top_n=t.container_top_n)

    logger.info("Collecting storage usage")
    storage_info = storage.collect()

    backup_info = None
    if cfg.storage:
        logger.info("Collecting backup info from MinIO")
        backup_info = backup.collect(cfg.storage)
    else:
        logger.info("MinIO config absent — skipping backup section")

    message = formatter.build_message(
        memory=memory_info,
        disks=disk_info,
        cpu=cpu_info,
        docker=docker_info,
        storage=storage_info,
        backup=backup_info,
        thresholds=t,
    )

    if not telegram.send_text_message(message):
        logger.error("Failed to send Telegram message")
        return 1

    logger.info("Infra report sent successfully")
    return 0


if __name__ == "__main__":
    sys.exit(main())
