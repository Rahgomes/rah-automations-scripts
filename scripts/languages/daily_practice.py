# daily_practice.py
import random
import os
import json

# Placeholder for message sending (will be handled by OpenClaw's message tool)
def send_message_to_user(message_text):
    # This function will be replaced by the OpenClaw message tool call
    # when executed within the pipeline or by Rah directly.
    # For now, it just prints.
    print(f"MESSAGE_TO_USER: {message_text}")

def get_language_practice(language, level):
    # For simplicity, hardcoding a few examples.
    # In a real scenario, this would come from a database, file, or more complex logic.
    practices = {
        "english": {
            "b2-c1": [
                {
                    "type": "Phrasal Verb",
                    "term": "Call off",
                    "meaning": "To cancel something that was planned.",
                    "examples": [
                        "They had to call off the meeting due to a sudden emergency.",
                        "The football match was called off because of the heavy rain."
                    ],
                    "translation": "Cancelar algo que já estava planejado."
                },
                {
                    "type": "Idiom",
                    "term": "Bite the bullet",
                    "meaning": "To endure a painful or difficult situation that is unavoidable.",
                    "examples": [
                        "I had to bite the bullet and work extra hours to finish the project.",
                        "She had to bite the bullet and accept the pay cut."
                    ],
                    "translation": "Enfrentar uma situação difícil ou desagradável com coragem."
                }
            ]
        },
        "spanish": {
            "b2-c1": [
                {
                    "type": "Expresión",
                    "term": "Estar en las nubes",
                    "meaning": "Estar distraído, sonhando acordado, com a cabeça no mundo da lua.",
                    "examples": [
                        "Juan siempre está en las nubes cuando le hablo, no me escucha.",
                        "Deja de estar en las nubes y concéntrate en tu trabajo."
                    ]
                },
                {
                    "type": "Refrán",
                    "term": "No hay mal que por bien no venga",
                    "meaning": "Não há mal que não traga algum bem (Toda nuvem tem um lado bom).",
                    "examples": [
                        "Perdí mi trabajo, pero gracias a eso encontré uno mejor. No hay mal que por bien no venga."
                    ]
                }
            ]
        },
        "french": {
            "a1-a2": [
                {
                    "type": "Vocabulário Básico",
                    "term": "Saudações Comuns",
                    "meaning": "Frases básicas para cumprimentar e se apresentar.",
                    "examples": [
                        "Bonjour!", "Bonsoir!", "Salut!", "Comment ça va?", "Ça va bien, merci.", "Enchanté(e)!"
                    ]
                }
            ]
        }
    }
    
    # Get practice for a random language/level based on availability
    chosen_language = random.choice(list(practices.keys()))
    chosen_level = random.choice(list(practices[chosen_language].keys()))
    
    return random.choice(practices[chosen_language][chosen_level])

if __name__ == "__main__":
    practice_item = get_language_practice("english", "b2-c1") # For now, let's pick one
    
    message_parts = []
    message_parts.append(f"📚 **Prática de Idiomas: {practice_item['type']} ({practice_item['term']})** 📚\n")
    if 'meaning' in practice_item:
        message_parts.append(f"📖 **Significado:** {practice_item['meaning']}\n")
    if 'translation' in practice_item:
        message_parts.append(f"🇧🇷 **Tradução:** {practice_item['translation']}\n")
    if 'examples' in practice_item:
        message_parts.append("\n✏️ **Exemplos:**")
        for example in practice_item['examples']:
            message_parts.append(f"• {example}")
    
    final_message = "\n".join(message_parts) # Use \n for Telegram markdown newline
    
    # This will be replaced by the OpenClaw message tool in the pipeline
    # For direct execution, it prints a special tag
    print(f"MESSAGE_TO_RAH: {final_message}")

