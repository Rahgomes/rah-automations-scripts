# capacity

Ferramentas para o servidor nunca encostar no teto de CPU do provedor. Instalação: `sudo ./install.sh`.
Contexto e decisões: `tmp-clones/infra-capacidade/ROTEIRO.md` (servidor srv986128).

| Script | O que faz | Custo |
|---|---|---|
| `infra-watch` | vigia de 1 em 1 min: CPU real, steal, RAM disponível, swap, disco. Telegram na mudança de estado | ~60 ms de CPU por rodada, teto 20% / 64 MB |
| `infra-snapshot` | fotografia no momento do alerta: processos, fila, CPU e RAM por container, jobs pesados | só no alerta, no máx. 1 a cada 10 min |
| `heavy` | fila única para trabalho pesado, 1 job por vez no servidor inteiro | o do próprio job, com teto |

## heavy

```
heavy -- pnpm test                    # entra na fila, espera a vez, mostra a saída, devolve o rc
heavy -l rah-crm -k test -- pytest -n 2
heavy -c 200 -m 6G -t 45 -- docker build .   # mais CPU, RAM e tempo (veja a nota abaixo)
heavy -u -- ...                       # urgente: fura a fila; se quem roda é pausável, congela e retoma no fim
heavy -p -t 120 -- ./crawler.sh       # longo e pausável (crawler e backfill já são por padrão)
heavy -s                              # mostra a fila
```

- Cada job roda num serviço transitório do systemd com `CPUQuota` (padrão 1 vCPU), `MemoryMax` (4G), tempo máximo (30 min) e prioridade baixa. Estourou tempo (rc 124) ou memória: é morto e o motivo aparece.
- O tempo máximo conta só o tempo **ativo**: job congelado para um urgente não morre por timeout ao ser retomado. Um urgente por vez; o retomar acontece mesmo se o urgente falhar.
- Quem espera na fila vê, a cada 30 s, quantos estão na frente e o que está rodando.
- O job roda na pasta e com o ambiente de quem chamou. O ambiente vai para um arquivo 600 apagado no início do job.
- Sair com Ctrl+C não cancela o job. Cancelar: `TS_SOCKET=/run/heavy/tsp.sock tsp -r <id>` (na fila) ou `-k <id>` (rodando).
- Rastro: `/var/log/heavy/jobs.jsonl`, uma linha por job com projeto, tipo, espera, duração, CPU, pico de RAM e resultado.
- **`docker build`**: quem compila é o BuildKit, fora do serviço do job. Por isso existe o builder `limitado` (container com 1,5 vCPU e 4G, `default-load=true`, criado pelo `install.sh`): use `BUILDX_BUILDER=limitado docker build ...`. O agente do Azure já aponta para ele (drop-in `cpu-limit.conf`).
