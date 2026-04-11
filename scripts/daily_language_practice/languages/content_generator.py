import json
import logging
import os

from groq import Groq

from . import config

logger = logging.getLogger(__name__)

SYSTEM_PROMPT = """\
You are an expert multilingual language teacher. Your student is a native \
Brazilian Portuguese speaker learning multiple languages.

You create engaging, practical daily language practice content that helps \
the student build real-world fluency.

Always respond with valid JSON only. No markdown, no extra text, no code fences.\
"""

USER_PROMPT_TEMPLATE = """\
Create a daily language practice item for {language} at {level} level.
Today's theme category is: {theme}

Choose a specific, practical item within this theme that a {level} student should know.

Return a JSON object with exactly these keys:
- "category": the specific sub-category you chose (e.g., "Phrasal Verbs de Trabalho", "Expressões de Surpresa")
- "term": the word, phrase, or expression in {language}
- "meaning": clear explanation in Brazilian Portuguese
- "pronunciation": simplified phonetic guide (e.g., "/kɔːl ɒf/" for English, "sé la vi" for French)
- "examples": array of exactly 2 objects, each with:
  - "original": a natural sentence in {language} using the term
  - "translation": the translation in Brazilian Portuguese in brackets
- "tip": a practical usage tip in Brazilian Portuguese that helps the student remember or use this correctly in real conversations
- "challenge": a mini interactive exercise in Brazilian Portuguese (e.g., "Complete a frase: They had to ___ the meeting." or "Como você diria 'X' em {language}?" or "Traduza: ...")

Important guidelines for {language} at {level}:
{level_instruction}\
"""

FALLBACK_CONTENT = {
    "english": {
        "category": "Phrasal Verbs",
        "term": "Look forward to",
        "meaning": "Aguardar ansiosamente por algo; estar animado com algo que vai acontecer.",
        "pronunciation": "/lʊk ˈfɔːrwərd tuː/",
        "examples": [
            {
                "original": "I'm looking forward to the weekend.",
                "translation": "Estou ansioso pelo fim de semana.",
            },
            {
                "original": "We look forward to hearing from you.",
                "translation": "Aguardamos ansiosamente seu retorno.",
            },
        ],
        "tip": "Essa expressão é seguida de substantivo ou gerúndio (-ing). "
        'Nunca diga "look forward to go", e sim "look forward to going".',
        "challenge": 'Complete: I\'m really ___ ___ ___ my vacation next month.',
    },
    "spanish": {
        "category": "Expressões Idiomáticas",
        "term": "Estar en las nubes",
        "meaning": "Estar distraído, sonhando acordado, com a cabeça no mundo da lua.",
        "pronunciation": "es-TAR en las NU-bes",
        "examples": [
            {
                "original": "Juan siempre está en las nubes cuando le hablo.",
                "translation": "Juan está sempre no mundo da lua quando falo com ele.",
            },
            {
                "original": "Deja de estar en las nubes y concéntrate.",
                "translation": "Para de ficar no mundo da lua e se concentra.",
            },
        ],
        "tip": "Use quando alguém parece distraído ou desatento. "
        'É informal e muito comum no dia a dia.',
        "challenge": "Como você diria 'Ela está sempre distraída' usando esta expressão?",
    },
    "french": {
        "category": "Expressões Comuns",
        "term": "C'est la vie",
        "meaning": 'É a vida" ou "Faz parte da vida". Expressa resignação ou aceitação.',
        "pronunciation": "sé la vi",
        "examples": [
            {
                "original": "J'ai raté mon bus, c'est la vie !",
                "translation": "Eu perdi meu ônibus, é a vida!",
            },
            {
                "original": "Il pleut encore aujourd'hui, c'est la vie.",
                "translation": "Está chovendo de novo hoje, é a vida.",
            },
        ],
        "tip": "Esta é uma expressão francesa muito conhecida internacionalmente. "
        "Use para demonstrar aceitação diante de uma situação inevitável.",
        "challenge": "Traduza para o francês: 'Eu não consegui o emprego, mas é a vida.'",
    },
}


def _build_prompt(language_config: dict, theme: str) -> str:
    return USER_PROMPT_TEMPLATE.format(
        language=language_config["code"].capitalize(),
        level=language_config["level"],
        theme=theme,
        level_instruction=language_config["prompt_instruction"],
    )


def generate_language_content(language_config: dict, theme: str) -> dict:
    """Generate practice content for a single language using Groq LLM."""
    api_key = os.environ.get("GROQ_API_KEY")
    if not api_key:
        logger.warning("GROQ_API_KEY not set, using fallback content")
        return FALLBACK_CONTENT.get(language_config["code"], {})

    client = Groq(api_key=api_key)
    prompt = _build_prompt(language_config, theme)

    for attempt in range(2):
        try:
            response = client.chat.completions.create(
                model=config.GROQ_MODEL,
                messages=[
                    {"role": "system", "content": SYSTEM_PROMPT},
                    {"role": "user", "content": prompt},
                ],
                temperature=0.8,
                max_tokens=1024,
                response_format={"type": "json_object"},
            )
            content = json.loads(response.choices[0].message.content)
            logger.info("Generated content for %s", language_config["name"])
            return content
        except json.JSONDecodeError:
            logger.warning(
                "JSON parse error for %s (attempt %d/2)",
                language_config["name"],
                attempt + 1,
            )
        except Exception as e:
            logger.error(
                "Groq API error for %s: %s", language_config["name"], e
            )
            break

    logger.warning("Using fallback content for %s", language_config["name"])
    return FALLBACK_CONTENT.get(language_config["code"], {})


def generate_all_content() -> tuple[str, list[dict]]:
    """Generate practice content for all languages.

    Returns the theme and a list of content dicts (one per language).
    """
    theme = config.get_today_theme()
    contents = []
    for lang in config.LANGUAGES:
        content = generate_language_content(lang, theme)
        contents.append(content)
    return theme, contents
