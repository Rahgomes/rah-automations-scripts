# Funções comuns do backup cruzado (srv986128 <-> Contabo). Usado por envio-srv986128.sh e backup-contabo.sh.
set -euo pipefail
umask 077
STAMP_DIR=/var/lib/rah-status
HOJE=$(TZ=America/Sao_Paulo date +%F)
log(){ printf '%s %s\n' "$(TZ=America/Sao_Paulo date '+%H:%M:%S')" "$*"; }
urlq(){ python3 -c 'import urllib.parse,sys;print(urllib.parse.quote(sys.argv[1],safe=""))' "$1"; }
mc_host(){ # mc_host <alias> <url-sem-esquema> <user> <senha>
  export "MC_HOST_$1=http://$(urlq "$3"):$(urlq "$4")@$2"; }
telegram(){ # só em falha ou aviso; nunca manda segredo
  [ -n "${TELEGRAM_BOT_TOKEN:-}" ] || return 0
  curl -s -m 15 -o /dev/null "https://api.telegram.org/bot${TELEGRAM_BOT_TOKEN}/sendMessage" \
    --data-urlencode "chat_id=${TELEGRAM_CHAT_ID}" --data-urlencode "text=$1" || true; }
carimbo(){ # carimbo <nome> <ok|falha> <resumo>: o retrato do Rah lê daqui
  mkdir -p "$STAMP_DIR"; printf '%s|%s|%s\n' "$(date +%s)" "$2" "$3" > "$STAMP_DIR/backup-$1.txt"; chmod 644 "$STAMP_DIR/backup-$1.txt"; }
tar_vivo(){ # tar de pasta em uso: código 1 = "arquivo mudou durante a leitura" (aceito); 2 = erro de verdade
  local rc=0; tar "$@" || rc=$?; [ "$rc" -le 1 ]; }
cifrar_tar(){ # cifrar_tar <saida.tar.gz.age> <lista-de-caminhos...>: tar só do que existe, cifrado com a chave pública
  local out=$1; shift; local paths=(); for p in "$@"; do [ -e "$p" ] && paths+=("$p"); done
  tar_vivo --ignore-failed-read -czf - --exclude='*.sock' --exclude='__pycache__' "${paths[@]}" 2>/dev/null | age -r "$BACKUP_AGE_PUBLIC_KEY" -o "$out"; }
