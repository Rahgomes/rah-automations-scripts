#!/usr/bin/env bash
# Backup diário dos bancos do postgres-central para o MinIO, rodando no
# servidor (antes era um pipeline agendado do Azure que recriava o venv e
# rodava pip install a cada execução). Chamado pelo rah-backup.service, que
# passa pela fila heavy.
set -euo pipefail
set -a
. /root/.secrets/database-backup.env   # PG*, MINIO_* (usuário database-backup), PGDATABASES_EXCLUDE
. /root/.secrets/telegram.env          # TELEGRAM_BOT_TOKEN, TELEGRAM_CHAT_ID
set +a
cd /opt/rah-backup/src
exec /opt/rah-backup/.venv/bin/python -m scripts.database_backup.main
