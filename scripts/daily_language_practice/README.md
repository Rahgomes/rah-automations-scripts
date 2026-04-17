# Daily Language Practice

Conteudo diario de pratica de idiomas gerado por IA. Envia mensagem de texto + audio no Telegram todas as manhas com frases, vocabulario e dicas em ingles, espanhol e frances.

## O que faz

1. Seleciona um tema do dia (rotacao entre categorias: viagem, negocios, cotidiano, etc.)
2. Gera conteudo via Groq LLM (Llama) com frases contextualizadas por idioma
3. Sintetiza audio via Google Gemini TTS para cada idioma
4. Formata e envia no Telegram: mensagem de texto + audio em OGG

## Execucao

Pipeline Azure DevOps (`daily-language-practice.yml`):
- Schedule: `0 12 * * *` UTC (9h BRT)
- Pool: `ubuntu-latest` (Microsoft-hosted)
- Variable Groups: `Telegram-Rah-Automation-Notifier-Credentials`, `LLM-Credentials`

## Variaveis de ambiente

| Variavel | Descricao |
|---|---|
| `GROQ_API_KEY` | API key Groq (geracao de conteudo) |
| `GEMINI_API_KEY` | API key Google Gemini (TTS) |
| `TELEGRAM_BOT_TOKEN` | Token do bot Telegram |
| `TELEGRAM_CHAT_ID` | Chat ID para envio |

## Estrutura

```
scripts/daily_language_practice/
  main.py                Entry point
  languages/
    config.py            Configs de idiomas, temas, modelos
    content_generator.py Geracao via Groq LLM
    audio_generator.py   Sintese TTS via Gemini
    telegram_sender.py   Formatacao e envio
```
