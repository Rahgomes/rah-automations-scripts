# Rah Automations Scripts

Colecao de scripts de automacao para o servidor srv986128. Cada script eh um modulo Python independente com seu proprio pipeline Azure DevOps ou cron schedule.

## Scripts

| Script | Descricao | Frequencia | Execucao |
|---|---|---|---|
| [Healthcheck](scripts/healthcheck/README.md) | Watchdog de 13 servicos com auto-recovery e alertas Telegram | A cada 2 min | Cron no servidor |
| [Database Backup](scripts/database_backup/README.md) | Backup PostgreSQL para MinIO com drift detection | Diario 3h BRT | Pipeline Azure DevOps |
| [Daily Language Practice](scripts/daily_language_practice/README.md) | Conteudo diario de idiomas (EN/ES/FR) via IA | Diario 9h BRT | Pipeline Azure DevOps |

## Tech Stack

- **Linguagem:** Python 3.12
- **Notificacoes:** Telegram Bot API (modulo compartilhado `scripts/shared/telegram.py`)
- **CI/CD:** Azure DevOps Pipelines (scheduled)
- **Infra:** Servidor self-hosted srv986128

## Estrutura

```
scripts/
  shared/
    telegram.py                  Modulo compartilhado de notificacoes Telegram
  healthcheck/
    main.py, config.py, ...      Watchdog de servicos (cron)
  database_backup/
    main.py, config.py, ...      Backup PostgreSQL (pipeline)
  daily_language_practice/
    main.py, config.py, ...      Conteudo de idiomas (pipeline)

database-backup.yml              Pipeline Azure DevOps
daily-language-practice.yml      Pipeline Azure DevOps
requirements.txt                 Dependencias Python
```

## Getting Started

### Rodar um script localmente

```bash
git clone https://github.com/Rahgomes/rah-automations-scripts.git
cd rah-automations-scripts
pip install -r requirements.txt

# Definir variaveis de ambiente necessarias (ver README de cada script)
export TELEGRAM_BOT_TOKEN="..."
export TELEGRAM_CHAT_ID="..."

# Executar
python3 -m scripts.healthcheck.main
python3 -m scripts.database_backup.main
python3 -m scripts.daily_language_practice.main
```

### Adicionar um novo script

1. Criar modulo em `scripts/{nome_do_script}/` com `__init__.py` e `main.py`
2. Seguir padrao: `main() -> int` com exit code 0 (sucesso) ou 1 (falha)
3. Config via dataclasses + env vars (nunca hardcoded)
4. Usar `scripts.shared.telegram` para notificacoes
5. Criar `README.md` no diretorio do script
6. Criar pipeline `.yml` na raiz (se scheduled) ou adicionar ao cron (se frequente)
7. Atualizar este README com o novo script na tabela

## Padroes

- **Logging:** `logging.basicConfig` com formato ISO 8601 + level + logger name
- **Config:** Dataclasses `frozen=True`, carregadas de env vars
- **Credenciais:** Sempre via env vars ou arquivos seguros, nunca no codigo
- **Entry point:** `python3 -m scripts.{modulo}.main`
- **Notificacoes:** Via `scripts.shared.telegram` (texto, audio, documentos)
