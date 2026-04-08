import datetime

def get_language_practice_message():
    today = datetime.date.today()
    # Exemplo simplificado. A logica real da skill de idiomas eh mais complexa.
    # Aqui, a ideia eh que o script gere um output para a pipeline.

    message = f"⚡️ Prática de Idiomas do dia {today.strftime('%d/%m/%Y')}!\n\n"
    message += "🇬🇧 **INGLÊS** (B2-C1) — Phrasal Verbs\n"
    message += "📖 \"Call off\": Cancelar algo que já estava planejado.\n"
    message += "✏️ Exemplo: 'They had to call off the meeting.'\n\n"
    message += "🇪🇸 **ESPANHOL** (B2-C1) — Expressões\n"
    message += "📖 \"Estar en las nubes\": Estar distraído, sonhando acordado.\n"
    message += "✏️ Exemplo: 'Juan siempre está en las nubes.'\n\n"
    message += "🇫🇷 **FRANCÊS** (A1-A2) — Vocabulário Básico\n"
    message += "📖 Saudações: 'Bonjour!', 'Salut!'\n"
    message += "✏️ Exemplo: 'Bonjour! Comment ça va?'\n"
    
    message += "\nContinue praticando! 🚀"
    return message

if __name__ == '__main__':
    print(get_language_practice_message())
