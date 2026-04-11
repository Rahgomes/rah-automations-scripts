import logging
import os
from pathlib import Path

import requests

logger = logging.getLogger(__name__)

TELEGRAM_API_URL = "https://api.telegram.org/bot{token}/{method}"
DEFAULT_TIMEOUT = 30
UPLOAD_TIMEOUT = 120


def _get_credentials() -> tuple[str, str]:
    token = os.environ["TELEGRAM_BOT_TOKEN"]
    chat_id = os.environ["TELEGRAM_CHAT_ID"]
    return token, chat_id


def _api_url(method: str) -> str:
    token, _ = _get_credentials()
    return TELEGRAM_API_URL.format(token=token, method=method)


def send_text_message(text: str, parse_mode: str = "HTML") -> bool:
    """Send a text message to Telegram."""
    _, chat_id = _get_credentials()
    try:
        response = requests.post(
            _api_url("sendMessage"),
            json={
                "chat_id": chat_id,
                "text": text,
                "parse_mode": parse_mode,
            },
            timeout=DEFAULT_TIMEOUT,
        )
        if response.ok:
            logger.info("Text message sent successfully")
            return True
        logger.error("Telegram sendMessage failed: %s", response.text)
        return False
    except Exception as e:
        logger.error("Error sending text message: %s", e)
        return False


def send_voice_message(audio_bytes: bytes, caption: str | None = None) -> bool:
    """Send an audio voice message (OGG OPUS) to Telegram."""
    _, chat_id = _get_credentials()
    try:
        data: dict[str, str] = {"chat_id": chat_id}
        if caption:
            data["caption"] = caption
        files = {"voice": ("audio.ogg", audio_bytes, "audio/ogg")}
        response = requests.post(
            _api_url("sendVoice"),
            data=data,
            files=files,
            timeout=UPLOAD_TIMEOUT,
        )
        if response.ok:
            logger.info("Voice message sent successfully")
            return True
        logger.error("Telegram sendVoice failed: %s", response.text)
        return False
    except Exception as e:
        logger.error("Error sending voice message: %s", e)
        return False


def send_document(file_path: Path, caption: str | None = None) -> bool:
    """Send a document file to Telegram. Useful for reports/logs (50MB limit)."""
    _, chat_id = _get_credentials()
    try:
        data: dict[str, str] = {"chat_id": chat_id}
        if caption:
            data["caption"] = caption
            data["parse_mode"] = "HTML"
        with open(file_path, "rb") as f:
            files = {"document": (file_path.name, f)}
            response = requests.post(
                _api_url("sendDocument"),
                data=data,
                files=files,
                timeout=UPLOAD_TIMEOUT,
            )
        if response.ok:
            logger.info("Document sent successfully: %s", file_path.name)
            return True
        logger.error("Telegram sendDocument failed: %s", response.text)
        return False
    except Exception as e:
        logger.error("Error sending document: %s", e)
        return False
