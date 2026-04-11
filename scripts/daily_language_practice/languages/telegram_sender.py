import logging
import os
import time

import requests

from . import config

logger = logging.getLogger(__name__)

TELEGRAM_API_URL = "https://api.telegram.org/bot{token}/{method}"
MESSAGE_DELAY = 0.5  # seconds between messages


def _get_credentials() -> tuple[str, str]:
    token = os.environ["TELEGRAM_BOT_TOKEN"]
    chat_id = os.environ["TELEGRAM_CHAT_ID"]
    return token, chat_id


def _api_url(method: str) -> str:
    token, _ = _get_credentials()
    return TELEGRAM_API_URL.format(token=token, method=method)


def send_text_message(text: str) -> bool:
    """Send a text message to Telegram using HTML parse mode."""
    _, chat_id = _get_credentials()
    try:
        response = requests.post(
            _api_url("sendMessage"),
            json={
                "chat_id": chat_id,
                "text": text,
                "parse_mode": "HTML",
            },
            timeout=30,
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
    """Send an audio voice message to Telegram."""
    _, chat_id = _get_credentials()
    try:
        data = {"chat_id": chat_id}
        if caption:
            data["caption"] = caption
        files = {"voice": ("audio.ogg", audio_bytes, "audio/ogg")}
        response = requests.post(
            _api_url("sendVoice"),
            data=data,
            files=files,
            timeout=60,
        )
        if response.ok:
            logger.info("Voice message sent successfully")
            return True
        logger.error("Telegram sendVoice failed: %s", response.text)
        return False
    except Exception as e:
        logger.error("Error sending voice message: %s", e)
        return False


def format_header(theme: str) -> str:
    """Format the header message with date and theme."""
    weekday, date_str = config.get_formatted_date()
    return (
        f"📚 <b>PRÁTICA DE IDIOMAS</b> — {weekday}, {date_str}\n"
        f"Tema: <i>{theme}</i>\n"
        "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
    )


def format_language_message(content: dict, language_config: dict) -> str:
    """Format a language practice message block."""
    flag = language_config["flag"]
    name = language_config["name"]
    level = language_config["level"]
    category = content.get("category", "")
    term = content.get("term", "")
    meaning = content.get("meaning", "")
    pronunciation = content.get("pronunciation", "")
    tip = content.get("tip", "")
    challenge = content.get("challenge", "")
    examples = content.get("examples", [])

    lines = [
        f"{flag} <b>{name}</b> ({level}) — {category}",
        "",
        f'"{term}"',
        "",
        f"📖 <b>Significado:</b> {meaning}",
    ]

    if pronunciation:
        lines.append(f"\n🗣️ <b>Pronúncia:</b> {pronunciation}")

    if examples:
        lines.append("\n✏️ <b>Exemplos:</b>")
        for ex in examples:
            original = ex.get("original", "")
            translation = ex.get("translation", "")
            lines.append(f'• "{original}"')
            if translation:
                lines.append(f"<i>[{translation}]</i>")

    if tip:
        lines.append(f"\n💡 <b>Dica:</b> {tip}")

    if challenge:
        lines.append(f"\n🎯 <b>Desafio:</b> {challenge}")

    return "\n".join(lines)


def send_daily_practice(
    theme: str,
    contents: list[dict],
    audios: list[bytes | None],
) -> bool:
    """Send the complete daily practice to Telegram.

    Sends a header, then for each language: text message + voice message.
    """
    header = format_header(theme)
    success = send_text_message(header)
    time.sleep(MESSAGE_DELAY)

    for i, lang in enumerate(config.LANGUAGES):
        content = contents[i]
        audio = audios[i] if i < len(audios) else None

        text = format_language_message(content, lang)
        send_text_message(text)
        time.sleep(MESSAGE_DELAY)

        if audio:
            caption = f"🔊 {lang['flag']} Áudio — {content.get('term', '')}"
            send_voice_message(audio, caption)
            time.sleep(MESSAGE_DELAY)

    logger.info("Daily practice delivery completed")
    return success
