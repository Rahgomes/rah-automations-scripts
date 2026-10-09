#!/usr/bin/env bash
# Instala o infra-watch e o infra-snapshot neste servidor. Idempotente.
set -euo pipefail
cd "$(dirname "$0")"
install -m 755 infra-watch infra-snapshot /usr/local/bin/
install -m 644 infra-watch.service infra-watch.timer /etc/systemd/system/
[ -f /etc/infra-watch.env ] || install -m 600 infra-watch.env.example /etc/infra-watch.env
systemctl daemon-reload
systemctl enable --now infra-watch.timer
echo "ok: ajuste /etc/infra-watch.env e acompanhe com: tail -f /var/lib/infra-watch/metrics-\$(date -u +%F).csv"
