# Hostinger Status

Monitor do statuspage da Hostinger focado no componente `BR Datacenter` (onde o servidor srv986128 vive). Roda a cada 15 min via pipeline Azure DevOps e notifica no Telegram **somente quando o status muda**.

## Comportamento

| Evento | Acao |
|---|---|
| Status igual ao anterior | Silencio (nenhuma notificacao) |
| Primeira execucao | Notifica estado inicial e persiste |
| Mudanca de estado (ex: operational -> partial_outage) | Notifica Telegram com icone, estado anterior e atual, incidentes ativos |
| Falha ao buscar API | Exit 1 (aparece nos logs da pipeline) |

## Estados possiveis

| Status Hostinger | Icone |
|---|---|
| operational | [OK] |
| degraded_performance | [WARN] |
| partial_outage | [WARN] |
| major_outage | [CRIT] |
| under_maintenance | [MAINT] |

## Execucao

Pipeline Azure DevOps (`hostinger-status.yml`):
- Schedule: `*/15 * * * *` UTC (a cada 15 min)
- Pool: `rah-self-hosted` (state persistido em disco local)
- Variable Group: `Telegram-Rah-Automation-Notifier-Credentials`

## Variaveis de ambiente

| Variavel | Obrigatoria | Descricao |
|---|---|---|
| `TELEGRAM_BOT_TOKEN` | Sim | Token do bot Telegram |
| `TELEGRAM_CHAT_ID` | Sim | Chat ID para envio |

## Estrutura

```
scripts/hostinger_status/
  main.py         Orquestra fetch -> diff -> notify
  config.py       URL da API, componente monitorado, path do state
  client.py       Fetch do summary.json, parse de componentes e incidentes
  state.py        Read/write do state.json (ultimo status conhecido)
  formatter.py    Monta mensagem HTML do Telegram
```

## State

Arquivo JSON em `/var/lib/hostinger-status/state.json`:
```json
{
  "last_status": "operational",
  "last_changed_at": "2026-04-18T23:15:00+00:00"
}
```

Persistente no agente self-hosted, sobrevive entre execucoes. Se o arquivo sumir (reset do agente), o proximo run trata como primeira execucao e notifica estado inicial.

## Por que nao reusa o infra_report?

| | Infra Report | Hostinger Status |
|---|---|---|
| Escopo | Servidor proprio (srv986128) | Infra externa (Hostinger) |
| Frequencia | 1x/dia | Cada 15 min |
| Output | Sempre envia relatorio | So envia em mudanca de estado |
| Proposito | Planejamento (quanto de RAM/disco?) | Alerta de incidente upstream |

## Logs

```bash
# Executar manualmente no servidor
cd /tmp/rah-automations-scripts
TELEGRAM_BOT_TOKEN=... TELEGRAM_CHAT_ID=... python3 -m scripts.hostinger_status.main
```
