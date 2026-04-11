"""Daily Language Practice — Entry Point.

Generates multilingual practice content via Groq LLM,
produces native-speaker audio via Gemini TTS,
and delivers everything to Telegram.
"""

import logging
import sys

from .languages import audio_generator, content_generator, telegram_sender

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
)
logger = logging.getLogger(__name__)


def main() -> int:
    logger.info("Starting daily language practice generation")

    logger.info("Generating content via Groq LLM...")
    theme, contents = content_generator.generate_all_content()
    logger.info("Theme of the day: %s", theme)

    logger.info("Generating audio via Gemini TTS...")
    audios = audio_generator.generate_all_audio(contents)
    audio_count = sum(1 for a in audios if a is not None)
    logger.info("Audio generated for %d/%d languages", audio_count, len(audios))

    logger.info("Sending to Telegram...")
    success = telegram_sender.send_daily_practice(theme, contents, audios)

    if success:
        logger.info("Daily language practice completed successfully")
        return 0

    logger.error("Daily language practice completed with errors")
    return 1


if __name__ == "__main__":
    sys.exit(main())
