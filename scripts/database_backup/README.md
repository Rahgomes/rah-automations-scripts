# Database Backup

Backup automatico de todos os bancos PostgreSQL para MinIO (S3). Roda diariamente as 3h BRT via pipeline Azure DevOps no self-hosted agent.

## O que faz

1. Descobre bancos automaticamente (ou usa lista explicita via env var)
2. Faz `pg_dump` de cada banco em formato custom (comprimido)
3. Upload para MinIO com path organizado: `{banco}/{ano}/{mes}/{dia}/{banco}_{timestamp}.dump`
4. Detecta drift: prefixos no bucket que nao correspondem a bancos ativos
5. Notifica Telegram no inicio e no fim com resumo (tamanho, duracao, sucesso/falha)

## Execucao

Pipeline Azure DevOps (`database-backup.yml`):
- Schedule: `0 6 * * *` UTC (3h BRT)
- Pool: `rah-self-hosted`
- Variable Groups: `Telegram-Rah-Automation-Notifier-Credentials`, `Database-Backup-Credentials`

## Variaveis de ambiente

| Variavel | Obrigatoria | Descricao |
|---|---|---|
| `PGHOST` | Sim | Host do PostgreSQL |
| `PGPORT` | Nao (default: 5432) | Porta |
| `PGUSER` | Sim | Usuario |
| `PGPASSWORD` | Sim | Senha |
| `PGDATABASES` | Nao | CSV de bancos (vazio = auto-discovery) |
| `PGDATABASES_EXCLUDE` | Nao | CSV de bancos a ignorar |
| `MINIO_ENDPOINT` | Sim | Host do MinIO |
| `MINIO_ACCESS_KEY` | Sim | Credencial |
| `MINIO_SECRET_KEY` | Sim | Credencial |
| `MINIO_BUCKET` | Sim | Nome do bucket |
| `MINIO_REGION` | Nao (default: us-east-1) | Regiao S3 |
| `TELEGRAM_BOT_TOKEN` | Sim | Token do bot Telegram |
| `TELEGRAM_CHAT_ID` | Sim | Chat ID para notificacoes |

## Estrutura

```
scripts/database_backup/
  main.py               Orquestra backup completo
  config.py             Dataclass config de env vars
  database_discovery.py Auto-discovery de bancos via pg_database
  postgres_dumper.py    Wrapper pg_dump
  storage_uploader.py   Upload boto3/S3 para MinIO
  drift_detector.py     Detecta prefixos orfaos no bucket
  notifier.py           Formatacao e envio Telegram
```
