#!/usr/bin/env bash
# Instala infra-watch, infra-snapshot e a fila heavy neste servidor. Idempotente.
set -euo pipefail
cd "$(dirname "$0")"
command -v tsp >/dev/null || DEBIAN_FRONTEND=noninteractive apt-get install -y -qq task-spooler
install -m 755 infra-watch infra-snapshot heavy heavy-run infra-limits registry-prune /usr/local/bin/
mkdir -p /var/lib/heavy /var/log/heavy/out && chmod 700 /var/lib/heavy
install -m 644 infra-watch.service infra-watch.timer infra-limits.service infra-limits.timer registry-prune.service registry-prune.timer /etc/systemd/system/
[ -f /etc/infra-watch.env ] || install -m 600 infra-watch.env.example /etc/infra-watch.env
# Builder com teto para docker build (o BuildKit roda fora de qualquer cota de serviço).
docker buildx inspect limitado >/dev/null 2>&1 || docker buildx create --name limitado --driver docker-container \
  --driver-opt cpu-quota=150000,cpu-period=100000,memory=4g,memory-swap=4g,default-load=true >/dev/null
systemctl daemon-reload
systemctl enable --now infra-watch.timer
# a tabela é por servidor: copie infra-limits.tsv.<servidor> ou escreva a sua
[ -f /etc/infra-limits.tsv ] && systemctl enable --now infra-limits.timer
echo "ok: ajuste /etc/infra-watch.env e acompanhe com: tail -f /var/lib/infra-watch/metrics-\$(date -u +%F).csv"
# limpeza do registry: só onde há registry próprio (a tabela é por servidor)
if [ -f /etc/registry-prune.tsv ]; then
  [ -f /etc/registry-prune.env ] || install -m 600 registry-prune.env.example /etc/registry-prune.env
  systemctl enable --now registry-prune.timer
fi
