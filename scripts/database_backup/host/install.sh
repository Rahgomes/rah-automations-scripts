#!/usr/bin/env bash
# Instala o backup no servidor: código em /opt/rah-backup/src, venv fixo,
# unidades do systemd. Idempotente: rodar de novo atualiza o código.
# Pré-requisitos: pg_dump 16, a fila heavy (scripts/capacity/install.sh) e
# /root/.secrets/database-backup.env.
set -euo pipefail
REPO="$(cd "$(dirname "$0")/../../.." && pwd)"
DEST=/opt/rah-backup
[ -r /root/.secrets/database-backup.env ] || { echo "falta /root/.secrets/database-backup.env"; exit 1; }
command -v heavy >/dev/null || { echo "falta a fila heavy (scripts/capacity/install.sh)"; exit 1; }
mkdir -p "$DEST/src/scripts"
rm -rf "$DEST/src/scripts/database_backup" "$DEST/src/scripts/shared"
# scripts/ é pacote de namespace (sem __init__.py), como no repo
cp -r "$REPO/scripts/database_backup" "$REPO/scripts/shared" "$DEST/src/scripts/"
find "$DEST/src" -name __pycache__ -prune -exec rm -rf {} +
git -C "$REPO" rev-parse --short HEAD > "$DEST/VERSION"
[ -x "$DEST/.venv/bin/python" ] || python3 -m venv "$DEST/.venv"
heavy -l rah-backup -k install -- "$DEST/.venv/bin/pip" install -q -r "$REPO/scripts/database_backup/host/requirements.txt"
install -m 755 "$REPO/scripts/database_backup/host/run.sh" "$DEST/run.sh"
install -m 644 "$REPO/scripts/database_backup/host/rah-backup.service" "$REPO/scripts/database_backup/host/rah-backup.timer" /etc/systemd/system/
chmod -R go-rwx "$DEST"
systemctl daemon-reload
echo "ok. Ligar o agendamento: systemctl enable --now rah-backup.timer | Rodar agora: systemctl start rah-backup.service"
