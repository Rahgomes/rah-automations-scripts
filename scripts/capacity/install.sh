#!/usr/bin/env bash
# Instala infra-watch, infra-snapshot e a fila heavy neste servidor. Idempotente.
set -euo pipefail
cd "$(dirname "$0")"
command -v tsp >/dev/null || DEBIAN_FRONTEND=noninteractive apt-get install -y -qq task-spooler
install -m 755 infra-watch infra-snapshot heavy heavy-run /usr/local/bin/
mkdir -p /var/lib/heavy /var/log/heavy/out && chmod 700 /var/lib/heavy
install -m 644 infra-watch.service infra-watch.timer /etc/systemd/system/
[ -f /etc/infra-watch.env ] || install -m 600 infra-watch.env.example /etc/infra-watch.env
systemctl daemon-reload
systemctl enable --now infra-watch.timer
echo "ok: ajuste /etc/infra-watch.env e acompanhe com: tail -f /var/lib/infra-watch/metrics-\$(date -u +%F).csv"
