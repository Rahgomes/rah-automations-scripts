import logging
import time

from scripts.shared import telegram

from . import config

logger = logging.getLogger(__name__)

MESSAGE_DELAY = 0.5  # seconds between messages


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
    success = telegram.send_text_message(header)
    time.sleep(MESSAGE_DELAY)

    for i, lang in enumerate(config.LANGUAGES):
        content = contents[i]
        audio = audios[i] if i < len(audios) else None

        text = format_language_message(content, lang)
        telegram.send_text_message(text)
        time.sleep(MESSAGE_DELAY)

        if audio:
            caption = f"🔊 {lang['flag']} Áudio — {content.get('term', '')}"
            telegram.send_voice_message(audio, caption)
            time.sleep(MESSAGE_DELAY)

    logger.info("Daily practice delivery completed")
    return success
