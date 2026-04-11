import datetime


GROQ_MODEL = "llama-3.3-70b-versatile"
GEMINI_TTS_MODEL = "gemini-2.5-flash-preview-tts"

LANGUAGES = [
    {
        "name": "INGLÊS",
        "code": "english",
        "flag": "🇬🇧",
        "level": "B2-C1",
        "gemini_voice": "Puck",
        "prompt_instruction": (
            "Use sophisticated, nuanced expressions. Include phrasal verbs, "
            "idioms, or advanced collocations that distinguish fluent speakers. "
            "The examples should reflect natural, everyday usage by native speakers."
        ),
    },
    {
        "name": "ESPANHOL",
        "code": "spanish",
        "flag": "🇪🇸",
        "level": "B2-C1",
        "gemini_voice": "Aoede",
        "prompt_instruction": (
            "Use expressions, proverbs, or advanced vocabulary that reflect "
            "natural, educated speech. Mix Latin American and European Spanish "
            "usage. The examples should sound authentic and conversational."
        ),
    },
    {
        "name": "FRANCÊS",
        "code": "french",
        "flag": "🇫🇷",
        "level": "A1-A2",
        "gemini_voice": "Kore",
        "prompt_instruction": (
            "Use simple, essential vocabulary and basic expressions. Focus on "
            "everyday situations like greetings, shopping, ordering food, asking "
            "directions. Keep sentences short and easy to memorize."
        ),
    },
]

THEME_CATEGORIES = [
    "Phrasal Verbs",
    "Expressões Idiomáticas",
    "Expressões Comuns",
    "Vocabulário Essencial",
    "Cultura & Idiomático",
    "Falsos Cognatos",
    "Gírias & Informal",
    "Registro Formal",
    "Colocações",
    "Provérbios & Ditados",
]

WEEKDAYS_PT = {
    0: "Segunda-feira",
    1: "Terça-feira",
    2: "Quarta-feira",
    3: "Quinta-feira",
    4: "Sexta-feira",
    5: "Sábado",
    6: "Domingo",
}

MONTHS_PT = {
    1: "Janeiro",
    2: "Fevereiro",
    3: "Março",
    4: "Abril",
    5: "Maio",
    6: "Junho",
    7: "Julho",
    8: "Agosto",
    9: "Setembro",
    10: "Outubro",
    11: "Novembro",
    12: "Dezembro",
}


def get_today_theme() -> str:
    day_of_year = datetime.date.today().timetuple().tm_yday
    return THEME_CATEGORIES[day_of_year % len(THEME_CATEGORIES)]


def get_formatted_date() -> tuple[str, str]:
    """Returns (weekday_name, formatted_date) in Portuguese."""
    today = datetime.date.today()
    weekday = WEEKDAYS_PT[today.weekday()]
    date_str = f"{today.day} de {MONTHS_PT[today.month]} de {today.year}"
    return weekday, date_str
