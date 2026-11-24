#!/usr/bin/env bash
# Instala infra-watch (e o vigia dele), infra-snapshot, infra-limits, registry-prune e notify
# neste servidor. Idempotente. A fila heavy saiu daqui em 24/11/2026: vive no rah-crm,
# em ops/heavy (perfil por servidor, F43); instale por lá com `bash ops/heavy/install.sh <servidor>`.
set -euo pipefail
cd "$(dirname "$0")"
install -m 755 infra-watch infra-watch-guard infra-snapshot infra-limits registry-prune notify /usr/local/bin/
mkdir -p /var/lib/notify && chmod 700 /var/lib/notify
install -m 644 infra-watch.service infra-watch.timer infra-watch-guard.service infra-watch-guard.timer \
  infra-limits.service infra-limits.timer registry-prune.service registry-prune.timer /etc/systemd/system/
[ -f /etc/infra-watch.env ] || install -m 600 infra-watch.env.example /etc/infra-watch.env
# Builder com teto para docker build (o BuildKit roda fora de qualquer cota de serviço).
docker buildx inspect limitado >/dev/null 2>&1 || docker buildx create --name limitado --driver docker-container \
  --driver-opt cpu-quota=150000,cpu-period=100000,memory=4g,memory-swap=4g,default-load=true >/dev/null
systemctl daemon-reload
systemctl enable --now infra-watch.timer infra-watch-guard.timer
# a tabela é por servidor: copie infra-limits.tsv.<servidor> ou escreva a sua
[ -f /etc/infra-limits.tsv ] && systemctl enable --now infra-limits.timer
echo "ok: ajuste /etc/infra-watch.env e acompanhe com: tail -f /var/lib/infra-watch/metrics-\$(date -u +%F).csv"
# limpeza do registry: só onde há registry próprio (a tabela é por servidor)
if [ -f /etc/registry-prune.tsv ]; then
  [ -f /etc/registry-prune.env ] || install -m 600 registry-prune.env.example /etc/registry-prune.env
  systemctl enable --now registry-prune.timer
fi
