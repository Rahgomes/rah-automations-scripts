# Infra Report

Snapshot diario do servidor srv986128. Roda as 4h BRT (apos o backup PostgreSQL terminar) e envia relatorio completo no Telegram com CPU, RAM, disco, containers Docker, storage e info do ultimo backup.

## O que coleta

| Categoria | Metricas |
|---|---|
| CPU | Cores, load average (1m/5m/15m), uptime, load por CPU |
| RAM | Total, usado, disponivel, swap, top 5 processos por RAM |
| Disco | Por particao: total, usado, livre, % uso |
| Docker | Containers (total/rodando/parados), top 5 por RAM, top 5 por CPU |
| Storage Docker | Imagens, volumes, build cache (com espaco reciclavel) |
| Backup | Ultimo backup no MinIO (data, idade, total objetos, tamanho) |

## Thresholds

Icones usados na mensagem:

| Icone | Significado |
|---|---|
| `[OK]` | Dentro do esperado |
| `[WARN]` | Acima do warn threshold |
| `[CRIT]` | Acima do critical threshold |

| Recurso | Warn | Critical |
|---|---|---|
| RAM | 80% | 90% |
| Disco | 80% | 90% |
| Load (por CPU) | 1.5 | — |

## Execucao

Pipeline Azure DevOps (`infra-report.yml`):
- Schedule: `0 7 * * *` UTC (4h BRT)
- Pool: `rah-self-hosted` (precisa rodar no servidor para coletar metricas reais)
- Variable Groups: `Telegram-Rah-Automation-Notifier-Credentials`, `Database-Backup-Credentials`

## Variaveis de ambiente

| Variavel | Obrigatoria | Descricao |
|---|---|---|
| `TELEGRAM_BOT_TOKEN` | Sim | Token do bot Telegram |
| `TELEGRAM_CHAT_ID` | Sim | Chat ID para envio |
| `MINIO_ENDPOINT` | Nao | Endpoint MinIO (omitir = sem secao backup) |
| `MINIO_ACCESS_KEY` | Nao | Credencial MinIO |
| `MINIO_SECRET_KEY` | Nao | Credencial MinIO |
| `MINIO_BUCKET` | Nao | Bucket de backups |
| `MINIO_REGION` | Nao (default: us-east-1) | Regiao S3 |

## Por que nao reusa o healthcheck?

| | Healthcheck | Infra Report |
|---|---|---|
| Proposito | Servico caiu? Recuperar | Snapshot do servidor para planejamento |
| Frequencia | A cada 2 min (cron) | 1x/dia (pipeline, apos backup) |
| Output | Alerta pontual no Telegram | Relatorio completo (RAM, disco, containers) |
| Acao | Automatica (restart) | Informativa (Ramon decide) |

## Estrutura

```
scripts/infra_report/
  main.py                Orquestra a coleta e o envio
  config.py              Thresholds e config opcional do MinIO
  formatter.py           Monta a mensagem HTML do Telegram
  collectors/
    cpu.py               Load average, uptime, CPU count
    memory.py            /proc/meminfo + ps top RSS
    disk.py              /proc/mounts + shutil.disk_usage
    docker.py            docker ps + docker stats --no-stream
    storage.py           docker system df
    backup.py            boto3 list_objects no bucket MinIO
```

Cada collector eh um modulo independente que retorna um dataclass `frozen=True`. O `main.py` orquestra a coleta e passa os resultados para o `formatter` que monta a mensagem final.

## Logs

```bash
# Ultimo log da pipeline pode ser visto no Azure DevOps
# Ou rodar manualmente no servidor:
cd /tmp/rah-automations-scripts
TELEGRAM_BOT_TOKEN=... TELEGRAM_CHAT_ID=... python3 -m scripts.infra_report.main
```
