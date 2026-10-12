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
# O backup roda no host, fora da rede do Docker: o nome do container não resolve
# e o IP muda a cada reboot (09/10 o /etc/hosts fixo quebrou o backup). Pega o IP
# atual do container na hora.
if ip=$(docker inspect -f '{{range .NetworkSettings.Networks}}{{.IPAddress}} {{end}}' "$PGHOST" 2>/dev/null | awk '{print $1}') && [ -n "$ip" ]; then
  export PGHOST="$ip"
fi
cd /opt/rah-backup/src
exec /opt/rah-backup/.venv/bin/python -m scripts.database_backup.main
