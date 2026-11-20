# Backup cruzado srv986128 ⇄ Contabo

Cada servidor guarda uma cópia do outro, pela VPN (WireGuard 10.66.0.0/24). Criado em 20/11/2026.

| Quando | Onde roda | O que faz | Destino |
|---|---|---|---|
| 03:00 | srv986128 (pipeline `database_backup`) | dump dos bancos do postgres-central | MinIO local `postgres-backups` (14 dias) |
| 03:30 | Contabo (`backup-contabo.timer`) | dump dos bancos, pasta do Rah (cifrada), config do servidor (cifrada) | MinIO da Contabo `backups` (14 dias) e cópia em `copia-contabo/` no srv986128 |
| 04:30 | srv986128 (`backup-cruzado.timer`, fila heavy) | config + segredos do servidor (cifrados) e espelho de todos os baldes, menos `docker-registry` e `rah-assistente-testes` | `copia-srv986128/` no MinIO da Contabo |

- **Baldes de cópia versionados:** o que some na origem vira versão antiga e expira em **30 dias**. Um apagão por engano na origem tem 30 dias para ser desfeito.
- **Cifra:** `age`. A chave pública fica nos servidores, e a privada só em `/root/.secrets/backup-cruzado-age.env` e no Vaultwarden. Quem rouba o MinIO de um lado não abre config, segredo nem a pasta do Rah.
- **Acesso mínimo:** cada lado grava só no próprio balde de cópia (`contabo-backup-writer`, `srv986128-backup-writer`). O leitor do srv986128 (`backup-cruzado-leitor`) só lê.
- **Aviso:** o Telegram só manda mensagem em falha. O carimbo em `/var/lib/rah-status/backup-*.txt` aparece no retrato que o Rah lê ("backup X: ok há Nh", FALHOU ou ATRASADO acima de 26 h).
- **Conferência:** depois do espelho, compara a quantidade de objetos de cada balde entre origem e cópia.

## Restaurar

```bash
set -a; source /root/.secrets/backup-cruzado-age.env; set +a
printf '%s\n' "$BACKUP_AGE_PRIVATE_KEY" > /tmp/k && mc cp <alias>/copia-contabo/backups/hermes/AAAA-MM-DD.tar.gz.age . \
  && age -d -i /tmp/k AAAA-MM-DD.tar.gz.age | tar -xzf - ; rm -f /tmp/k
# Postgres: pg_restore -d <banco> <arquivo>.dump ; papéis: zcat _globals/AAAA-MM-DD.sql.gz | psql
```

O teste de restauração da pasta do Rah foi feito em 20/11/2026: os dois bancos SQLite passaram no integrity_check, e a configuração e a personalidade estavam presentes.

## Instalar

- srv986128: `lib.sh` e `envio-srv986128.sh` em `/usr/local/lib/backup-cruzado/`, `backup-cruzado.{service,timer}` em `/etc/systemd/system/`.
- Contabo: `lib.sh` e `backup-contabo.sh` no mesmo caminho, `backup-contabo.{service,timer}` e `/etc/backup-cruzado/contabo.env` (600), que leva só o usuário de cópia, a chave pública e o Telegram.
