#!/usr/bin/env bash
# Backup da Contabo, com cópia no srv986128. Roda às 03:30 na Contabo.
# 1) dump de cada banco do postgres-central (pg_dump -Fc) + papéis (globals)  -> MinIO local backups/postgres/
# 2) pasta do Rah (Hermes): SQLite pela API de backup + config, memória, skills, .env, cifrado (age) -> backups/hermes/
# 3) config do servidor (compose, .env, units, VPN, firewall), cifrado -> backups/config-contabo/
# 4) cópia para o srv986128: backups/ e os baldes de apps -> copia-contabo/ (destino versionado, 30 dias)
# Retenção local: 14 dias (regra do balde). Carimbo para o retrato do Rah; Telegram só em falha.
source "$(dirname "$(readlink -f "$0")")/lib.sh"
set -a; source /etc/backup-cruzado/contabo.env; source /opt/minio/.env; set +a
mc_host loc 10.66.0.2:9000 "$MINIO_ROOT_USER" "$MINIO_ROOT_PASSWORD"
mc_host dst 10.66.0.1:9000 "$SRV_MINIO_COPIA_CONTABO_USER" "$SRV_MINIO_COPIA_CONTABO_PASSWORD"
EXCLUIR=" backups copia-srv986128 "
TMP=$(mktemp -d /var/tmp/backup-contabo.XXXX); trap 'rm -rf "$TMP"' EXIT
falhas=(); resumo=()
trap 'carimbo contabo falha "erro inesperado na linha $LINENO"; telegram "❌ Backup da Contabo falhou (linha $LINENO). Ver: journalctl -u backup-contabo"' ERR

log "1/4 Postgres"
PG="docker exec -i postgres-central"
$PG pg_dumpall -U admin --globals-only | gzip > "$TMP/globals.sql.gz"
mc cp -q "$TMP/globals.sql.gz" "loc/backups/postgres/_globals/$HOJE.sql.gz" >/dev/null
mapfile -t DBS < <($PG psql -U admin -d postgres -Atc "select datname from pg_database where not datistemplate and datname <> 'postgres' order by 1")
for db in "${DBS[@]}"; do
  if $PG pg_dump -U admin -Fc -d "$db" > "$TMP/$db.dump" && [ -s "$TMP/$db.dump" ]; then
    mc cp -q "$TMP/$db.dump" "loc/backups/postgres/$db/$HOJE.dump" >/dev/null; rm -f "$TMP/$db.dump"
  else falhas+=("pg_dump $db"); fi
done
resumo+=("bancos ${#DBS[@]}")

# Apps com banco próprio, fora do postgres-central (migrados do srv986128 em 21/11/2026).
# Os anexos do Planka podem ter arquivo de cliente, então vão cifrados.
KIMAI_DB=mysql-mv0s8b1r4ub1nvbby96qm9v6; PLANKA_DB=postgres-lfhc8uf0up6w7fu9ch4w3e0r
if docker inspect "$KIMAI_DB" >/dev/null 2>&1; then
  if docker exec "$KIMAI_DB" sh -c 'exec mysqldump -uroot -p"$MYSQL_ROOT_PASSWORD" --single-transaction --routines --databases "$MYSQL_DATABASE"' 2>/dev/null \
      | gzip > "$TMP/kimai.sql.gz" && [ "$(zcat "$TMP/kimai.sql.gz" | head -c 100 | wc -c)" -gt 0 ]; then
    mc cp -q "$TMP/kimai.sql.gz" "loc/backups/apps/kimai-mysql/$HOJE.sql.gz" >/dev/null; resumo+=("kimai")
  else falhas+=("mysqldump kimai"); fi
fi
if docker inspect "$PLANKA_DB" >/dev/null 2>&1; then
  if docker exec "$PLANKA_DB" pg_dump -U postgres -Fc -d planka > "$TMP/planka.dump" && [ -s "$TMP/planka.dump" ]; then
    mc cp -q "$TMP/planka.dump" "loc/backups/apps/planka-postgres/$HOJE.dump" >/dev/null; resumo+=("planka")
  else falhas+=("pg_dump planka"); fi
  V=/var/lib/docker/volumes/lfhc8uf0up6w7fu9ch4w3e0r_planka-data/_data
  if [ -d "$V" ]; then
    tar_vivo -C "$V" -czf - . | age -r "$BACKUP_AGE_PUBLIC_KEY" -o "$TMP/planka-anexos.tar.gz.age"
    mc cp -q "$TMP/planka-anexos.tar.gz.age" "loc/backups/apps/planka-anexos/$HOJE.tar.gz.age" >/dev/null
  fi
fi

log "2/4 pasta do Rah"
H=/home/hermes/.hermes; mkdir -p "$TMP/hermes-sqlite"
for f in "$H"/*.db; do [ -f "$f" ] || continue
  python3 -c 'import sqlite3,sys; s=sqlite3.connect(f"file:{sys.argv[1]}?mode=ro",uri=True); d=sqlite3.connect(sys.argv[2]); s.backup(d); d.close(); s.close()' "$f" "$TMP/hermes-sqlite/$(basename "$f")"; done
tar_vivo -C / -czf - --exclude='home/hermes/.hermes/bin' --exclude='home/hermes/.hermes/node' --exclude='home/hermes/.hermes/logs' --exclude='home/hermes/.hermes/*.db' \
  --exclude='home/hermes/.hermes/*.db-wal' --exclude='home/hermes/.hermes/*.db-shm' --exclude='home/hermes/.hermes/models_dev_cache.json' \
  --exclude='*/__pycache__' --exclude='home/hermes/.hermes/cache' home/hermes/.hermes home/hermes/.ssh -C "$TMP" hermes-sqlite 2>/dev/null \
  | age -r "$BACKUP_AGE_PUBLIC_KEY" -o "$TMP/hermes.tar.gz.age"
mc cp -q "$TMP/hermes.tar.gz.age" "loc/backups/hermes/$HOJE.tar.gz.age" >/dev/null
resumo+=("Rah $(du -h "$TMP/hermes.tar.gz.age" | cut -f1)")

log "3/4 config do servidor"
mapfile -t OPT < <(find /opt -maxdepth 2 \( -name 'docker-compose*.y*ml' -o -name '.env' -o -name '*.env' \) -size -1024k 2>/dev/null)
cifrar_tar "$TMP/config.tar.gz.age" /etc/wireguard /etc/ufw /etc/ssh/sshd_config.d /etc/systemd/system/hermes-gateway.service \
  /etc/systemd/system/rah-status.service /etc/systemd/system/rah-status.timer /etc/systemd/system/backup-contabo.service \
  /etc/systemd/system/backup-contabo.timer /etc/systemd/resolved.conf.d /etc/docker/daemon.json /etc/backup-cruzado "${OPT[@]}"
mc cp -q "$TMP/config.tar.gz.age" "loc/backups/config-contabo/$HOJE.tar.gz.age" >/dev/null

log "4/4 cópia para o srv986128"
mc mirror -q --overwrite --remove "loc/backups" "dst/copia-contabo/backups" >/dev/null 2>"$TMP/err" || falhas+=("espelho backups: $(tail -c 200 "$TMP/err")")
mapfile -t BALDES < <(mc ls --json loc/ | python3 -c 'import sys,json;[print(json.loads(l)["key"].rstrip("/")) for l in sys.stdin]')
for b in "${BALDES[@]}"; do [[ "$EXCLUIR" == *" $b "* ]] && continue
  mc mirror -q --overwrite --remove "loc/$b" "dst/copia-contabo/minio/$b" >/dev/null 2>"$TMP/err" || falhas+=("espelho $b: $(tail -c 200 "$TMP/err")")
  resumo+=("balde $b")
done
conta(){ mc ls -r --json "$1" 2>/dev/null | grep -c '"type":"file"' || true; }
a=$(conta loc/backups); d=$(conta dst/copia-contabo/backups); [ "$a" = "$d" ] || falhas+=("backups: local $a, cópia $d")
resumo+=("arquivos $d")
trap - ERR
if [ ${#falhas[@]} -gt 0 ]; then
  carimbo contabo falha "${falhas[*]}"; telegram "⚠️ Backup da Contabo com problema: ${falhas[*]}"; log "FALHA: ${falhas[*]}"; exit 1; fi
carimbo contabo ok "${resumo[*]}"; log "ok: ${resumo[*]}"
