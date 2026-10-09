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
heavy -u -- ...                       # urgente: fura a fila, nunca interrompe quem roda
heavy -s                              # mostra a fila
```

- Cada job roda num serviço transitório do systemd com `CPUQuota` (padrão 1 vCPU), `MemoryMax` (4G), tempo máximo (30 min) e prioridade baixa. Estourou tempo ou memória: é morto e o motivo aparece.
- O job roda na pasta e com o ambiente de quem chamou. O ambiente vai para um arquivo 600 apagado no início do job.
- Sair com Ctrl+C não cancela o job. Cancelar: `TS_SOCKET=/run/heavy/tsp.sock tsp -r <id>` (na fila) ou `-k <id>` (rodando).
- Rastro: `/var/log/heavy/jobs.jsonl`, uma linha por job com projeto, tipo, espera, duração, CPU, pico de RAM e resultado.
- **`docker build` não fica sob o teto**: quem compila é o dockerd/BuildKit, fora do serviço do job. Para limitar build, use um builder buildx dedicado com limite (item B7 do roteiro).
