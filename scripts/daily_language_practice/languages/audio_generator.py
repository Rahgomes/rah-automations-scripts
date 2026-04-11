import io
import logging
import os
import wave

from google import genai
from google.genai import types
from pydub import AudioSegment

from . import config

logger = logging.getLogger(__name__)

GEMINI_TTS_SAMPLE_RATE = 24000
GEMINI_TTS_CHANNELS = 1
GEMINI_TTS_SAMPLE_WIDTH = 2  # 16-bit


def _pcm_to_wav(pcm_data: bytes) -> io.BytesIO:
    """Convert raw PCM data to WAV format in memory."""
    wav_buffer = io.BytesIO()
    with wave.open(wav_buffer, "wb") as wav_file:
        wav_file.setnchannels(GEMINI_TTS_CHANNELS)
        wav_file.setsampwidth(GEMINI_TTS_SAMPLE_WIDTH)
        wav_file.setframerate(GEMINI_TTS_SAMPLE_RATE)
        wav_file.writeframes(pcm_data)
    wav_buffer.seek(0)
    return wav_buffer


def _wav_to_ogg(wav_buffer: io.BytesIO) -> bytes:
    """Convert WAV buffer to OGG OPUS bytes for Telegram."""
    audio = AudioSegment.from_wav(wav_buffer)
    ogg_buffer = io.BytesIO()
    audio.export(ogg_buffer, format="ogg", codec="libopus")
    ogg_buffer.seek(0)
    return ogg_buffer.read()


def _build_tts_text(content: dict, language_code: str) -> str:
    """Build the text to be spoken from the content."""
    parts = [content.get("term", "")]
    for example in content.get("examples", []):
        original = example.get("original", "")
        if original:
            parts.append(original)
    return ". ".join(parts)


def generate_audio(text: str, voice: str) -> bytes | None:
    """Generate TTS audio using Gemini API.

    Returns OGG OPUS bytes or None if generation fails.
    """
    api_key = os.environ.get("GEMINI_API_KEY")
    if not api_key:
        logger.warning("GEMINI_API_KEY not set, skipping audio generation")
        return None

    try:
        client = genai.Client(api_key=api_key)
        response = client.models.generate_content(
            model=config.GEMINI_TTS_MODEL,
            contents=text,
            config=types.GenerateContentConfig(
                response_modalities=["AUDIO"],
                speech_config=types.SpeechConfig(
                    voice_config=types.VoiceConfig(
                        prebuilt_voice_config=types.PrebuiltVoiceConfig(
                            voice_name=voice,
                        )
                    )
                ),
            ),
        )

        audio_data = response.candidates[0].content.parts[0].inline_data.data
        wav_buffer = _pcm_to_wav(audio_data)
        ogg_bytes = _wav_to_ogg(wav_buffer)

        logger.info("Generated audio for voice '%s' (%d bytes)", voice, len(ogg_bytes))
        return ogg_bytes

    except Exception as e:
        logger.error("Gemini TTS error (voice=%s): %s", voice, e)
        return None


def generate_all_audio(
    contents: list[dict], languages: list[dict] | None = None
) -> list[bytes | None]:
    """Generate TTS audio for all languages.

    Returns a list of OGG bytes (or None per language if failed).
    """
    if languages is None:
        languages = config.LANGUAGES

    audios = []
    for content, lang in zip(contents, languages):
        tts_text = _build_tts_text(content, lang["code"])
        audio = generate_audio(tts_text, lang["gemini_voice"])
        audios.append(audio)

    return audios
