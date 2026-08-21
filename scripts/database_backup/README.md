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

## Retencao

**A retencao nao esta neste codigo.** O script so escreve; quem apaga e uma regra
de ciclo de vida (ILM) do proprio MinIO, no bucket `postgres-backups`. Sem ela, os
dumps se acumulariam para sempre.

Estado atual (definido em 2026-08-21):

| Regra | Prefixo | Dias |
|---|---|---|
| `expire-imoveis-crawler-after-3-days` | `imoveis_crawler/` | 3 |
| `expire-backups-after-14-days` | bucket inteiro | 14 |

O `imoveis_crawler` tem regra propria porque sozinho pesa **6,9 GB por dump**,
contra menos de 60 MB somando **todos** os outros bancos. Com sete copias ele
ocupava 41 GB, mais de 98% do bucket. Como o projeto esta congelado, historico
ali vale pouco: tres dias cobrem um fim de semana e e o suficiente.

Os demais bancos foram de 7 para 14 dias no mesmo movimento. Dobrar a janela para
perceber um problema custa uns 400 MB, e ha coisa em producao no meio deles.

**Quando duas regras alcancam o mesmo objeto, o MinIO aplica a de prefixo mais
especifico.** Nao e preciso deduzir: `mc stat --json` devolve `expiration` e
`expirationRuleID` ja calculados para o objeto.

```bash
# Ver as regras
mc ilm rule ls rahminio/postgres-backups

# Conferir qual regra pegou um objeto especifico
mc stat --json rahminio/postgres-backups/<banco>/<ano>/<mes>/<dia>/<arquivo>.dump \
  | python3 -c "import json,sys; d=json.load(sys.stdin); print(d['expiration'], d['expirationRuleID'])"

# Alterar (exporta, edita, importa)
mc ilm rule export rahminio/postgres-backups > ilm.json
mc ilm rule import rahminio/postgres-backups < ilm.json
```

Banco novo e pesado que aparecer merece regra propria. O `drift_detector` avisa
sobre prefixo orfao, mas ninguem avisa sobre prefixo gordo: vale olhar
`du -sh /opt/minio-data/postgres-backups/*` de vez em quando.

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
