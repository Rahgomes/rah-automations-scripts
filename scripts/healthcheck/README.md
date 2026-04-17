# Healthcheck

Watchdog de servicos que roda a cada 2 minutos via cron. Verifica disponibilidade HTTP de todos os servicos do servidor, tenta recuperacao automatica (ate 3x) e notifica via Telegram.

## O que monitora

### Servicos (13 ativos)

| Servico | URL | Recovery |
|---|---|---|
| Dozzle | logs.ramongomessilva.com.br | compose |
| Homepage | home.ramongomessilva.com.br | compose |
| Uptime Kuma | monitor.ramongomessilva.com.br | compose |
| Docker Registry | registry.ramongomessilva.com.br/v2/ | restart |
| Registry UI | registry-ui.ramongomessilva.com.br | restart |
| Keycloak | sso.nexalumedigital.com.br | restart |
| n8n | n8n.nexalumedigital.com.br | restart |
| SiteCloner | site-cloner.ramongomessilva.com.br | restart |
| NexaLume DEV | dev.nexalumedigital.com.br | restart |
| NexaLume PROD | nexalumedigital.com.br | restart |
| MBA-RAG | mba-rag.ramongomessilva.com.br | restart |
| Video Tools | video-tools.ramongomessilva.com.br | restart |
| TranscriLab DEV | transcrilab-dev.ramongomessilva.com.br | restart |

### Checks adicionais

| Check | Threshold | Acao |
|---|---|---|
| Disco | >= 85% uso | Notifica Telegram (1x ate resolver) |
| Docker daemon | nao responde | Notifica e aborta |
| Certificado SSL | <= 7 dias para expirar | Notifica Telegram (1x por dominio) |
| Tempo de resposta | Logado por servico | Visivel no log |

## Como funciona

1. Verifica se o Docker daemon responde
2. Checa uso de disco e alerta se acima do threshold
3. Verifica certificados SSL proximos do vencimento
4. Para cada servico, faz GET na URL e avalia o HTTP status code
5. Se o servico esta fora, incrementa contador de retries (persistido em `/var/lib/healthcheck/`)
6. Tenta recuperacao: `docker compose up -d --force-recreate` (compose) ou `docker restart` (standalone)
7. Aguarda 15s e re-verifica
8. Notifica Telegram em cada tentativa e no resultado final
9. Apos 3 tentativas sem sucesso, para de tentar e pede acao manual

## Estrategias de recovery

| Tipo | Comando | Quando usar |
|---|---|---|
| `compose` | `docker compose up -d --force-recreate {service}` | Servicos com docker-compose.yml |
| `restart` | `docker restart {container}` | Containers standalone ou Coolify |
| `none` | Apenas notifica | Servicos que nao devem ser auto-recuperados |

## Execucao

Roda via cron no servidor (nao eh container nem pipeline):

```
*/2 * * * * cd /tmp/rah-automations-scripts && python3 -m scripts.healthcheck.main >> /var/log/healthcheck.log 2>&1
```

Credenciais Telegram em `/var/lib/healthcheck/` (arquivos `.telegram_token` e `.telegram_chat`, chmod 600).

## Adicionando um novo servico

Editar `config.py` e adicionar um `Service` na lista `SERVICES`:

```python
Service(
    name="Meu Servico",
    url="https://meu-servico.ramongomessilva.com.br/",
    container="meu-servico",
    strategy=RecoveryStrategy.RESTART,
),
```

Parametros opcionais: `compose_dir` (para strategy COMPOSE), `accept_codes` (default: 200, 302, 307), `max_retries` (default: 3).

## Estrutura

```
scripts/healthcheck/
  main.py        Orquestra o fluxo completo
  config.py      Lista de servicos e configuracoes
  checker.py     Verificacao HTTP, disco, Docker, SSL
  recovery.py    Estrategias de recuperacao de containers
  notifier.py    Formatacao e envio de alertas Telegram
```

## Logs

```bash
# Ultimas linhas
tail -50 /var/log/healthcheck.log

# Filtrar problemas
grep -E "DOWN|WARNING|ERROR" /var/log/healthcheck.log | tail -20

# Estado de retries
ls -la /var/lib/healthcheck/*.retries 2>/dev/null
```
