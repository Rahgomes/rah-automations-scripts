#!/usr/bin/env bash
# Backup cruzado, lado srv986128 -> Contabo. Roda às 04:30 (depois do dump das 03:00) pela fila heavy.
# 1) config + segredos do servidor, cifrados (age) -> copia-srv986128/config-srv986128/
# 2) espelho de cada balde do MinIO local -> copia-srv986128/<balde>/ (destino versionado: apagado aqui
#    some lá como versão antiga e expira em 30 dias)
# 3) confere contagem de objetos por balde; carimbo para o retrato do Rah; Telegram só em falha.
source "$(dirname "$(readlink -f "$0")")/lib.sh"
set -a; source /root/.secrets/backup-cruzado.env; source /root/.secrets/backup-cruzado-age.env
source /root/.secrets/telegram.env; set +a; unset BACKUP_AGE_PRIVATE_KEY
EXCLUIR=" docker-registry rah-assistente-testes copia-contabo "   # registry se refaz pela pipeline; testes não valem
mc_host src 127.0.0.1:9000 "$SRV_MINIO_LEITOR_USER" "$SRV_MINIO_LEITOR_PASSWORD"
mc_host dst 10.66.0.2:9000 "$CONTABO_MINIO_COPIA_SRV_USER" "$CONTABO_MINIO_COPIA_SRV_PASSWORD"
falhas=(); resumo=()
trap 'carimbo srv986128 falha "erro inesperado na linha $LINENO"; telegram "❌ Backup cruzado srv986128 → Contabo falhou (linha $LINENO). Ver: journalctl -u backup-cruzado"' ERR

log "1/3 config e segredos (cifrado)"
TMP=$(mktemp -d); trap 'rm -rf "$TMP"' EXIT
mapfile -t OPT < <(find /opt -maxdepth 2 \( -name 'docker-compose*.y*ml' -o -name '.env' -o -name '*.env' \) -size -1024k 2>/dev/null)
mapfile -t UNITS < <(find /etc/systemd/system -maxdepth 2 \( -name '*.service' -o -name '*.timer' -o -name '*.conf' \) -newer /etc/hostname -type f 2>/dev/null)
mapfile -t BINS < <(find /usr/local/bin /usr/local/sbin /root/bin -maxdepth 1 -type f -size -1024k 2>/dev/null)
crontab -l > "$TMP/crontab-root.txt" 2>/dev/null || true
cifrar_tar "$TMP/config.tar.gz.age" /root/.secrets /root/.ssh /etc/wireguard /etc/ufw /etc/ssh/sshd_config.d \
  /data/coolify/source/.env /data/coolify/proxy/dynamic /etc/docker/daemon.json /etc/systemd/resolved.conf.d \
  "$TMP/crontab-root.txt" "${OPT[@]}" "${UNITS[@]}" "${BINS[@]}"
mc cp -q "$TMP/config.tar.gz.age" "dst/copia-srv986128/config-srv986128/$HOJE.tar.gz.age" >/dev/null
resumo+=("config $(du -h "$TMP/config.tar.gz.age" | cut -f1)")

log "2/3 espelho dos baldes"
mapfile -t BALDES < <(mc ls --json src/ | python3 -c 'import sys,json;[print(json.loads(l)["key"].rstrip("/")) for l in sys.stdin]')
for b in "${BALDES[@]}"; do
  [[ "$EXCLUIR" == *" $b "* ]] && continue
  if ! mc mirror -q --overwrite --remove --limit-upload 40MiB "src/$b" "dst/copia-srv986128/$b" >/dev/null 2>"$TMP/err"; then
    falhas+=("$b: $(tail -c 200 "$TMP/err")"); continue; fi
done

log "3/3 conferência"
conta(){ mc ls -r --json "$1" 2>/dev/null | grep -c '"type":"file"' || true; }
for b in "${BALDES[@]}"; do
  [[ "$EXCLUIR" == *" $b "* ]] && continue
  a=$(conta "src/$b"); d=$(conta "dst/copia-srv986128/$b")
  [ "$a" = "$d" ] || falhas+=("$b: origem $a objetos, cópia $d")
  resumo+=("$b $d")
done
trap - ERR
if [ ${#falhas[@]} -gt 0 ]; then
  carimbo srv986128 falha "${falhas[*]}"; telegram "⚠️ Backup cruzado srv986128 → Contabo com problema: ${falhas[*]}"; log "FALHA: ${falhas[*]}"; exit 1; fi
carimbo srv986128 ok "${resumo[*]}"; log "ok: ${resumo[*]}"
