# capacity

Ferramentas para o servidor nunca encostar no teto de CPU do provedor. Instalação: `sudo ./install.sh`.
Contexto e decisões: `tmp-clones/infra-capacidade/ROTEIRO.md` (servidor srv986128).

| Script | O que faz | Custo |
|---|---|---|
| `infra-watch` | vigia de 1 em 1 min: CPU real, steal, RAM disponível, swap, disco. Telegram na mudança de estado | 60 a 130 ms de CPU por rodada (sobe com a carga), orçamento 1000 ms |
| `infra-watch-guard` | vigia do vigia, a cada 10 min: sem batimento há 10 min, aviso crítico, repetido de hora em hora até voltar | 1 leitura de arquivo |
| `infra-snapshot` | fotografia no momento do alerta: processos, fila, CPU e RAM por container, jobs pesados | só no alerta, no máx. 1 a cada 10 min |
| `infra-limits` | teto de RAM e CPU por container a partir de `/etc/infra-limits.tsv`; reaplica a cada 10 min o que um deploy tiver apagado | 1 `docker inspect` para todos |

## heavy (mudou de lugar)

Desde 24/11/2026 a fila heavy vive no rah-crm, em `ops/heavy`, com perfil por servidor (F43:
vagas e tetos em `/etc/heavy.conf`, aviso de espera, `push-fila`, limpeza de `~/trabalho`).
Instalação: `bash ops/heavy/install.sh <srv986128|contabo>`. Uso: `heavy -h`.

## infra-limits

`docker update` vale na hora, mas some quando o container é recriado (deploy do Coolify, `compose up`).
A tabela `/etc/infra-limits.tsv` (`nome  memória  cpus`) é a fonte da verdade e o timer reaplica a cada
10 min. `infra-limits --check` mostra a diferença sem mudar nada. `-` na memória = teto definido em outro
lugar. Container fora da tabela aparece no log como "sem limite".

Como dimensionar: memória **própria** do processo (`anon` em `memory.stat`) com folga de 2x ou mais; o
`memory.peak` inclui cache de disco, que o kernel devolve, e engana (o MinIO marcava 10 GB de pico com
161 MB próprios). A tabela do srv986128 está em `infra-limits.tsv.srv986128`.

## registry-prune (limpeza do registry Docker)

Guarda por repositório as N imagens mais novas (`/etc/registry-prune.tsv`; linha `*` é o padrão),
as tags fixas (latest, prod, manual...) e tudo que algum container do servidor usa. Apaga o resto
pela API e roda o garbage-collect (espera o agente do Azure ficar livre, até 45 min). Sem
`--delete-untagged`, que quebra imagem multi-arquitetura.

- Plano sem apagar: `registry-prune`
- Rodar já: `systemctl start registry-prune` (vai pela fila `heavy`)
- Timer semanal, domingo 05:30. Registro em `/var/log/registry-prune.jsonl`.
- 1ª rodada (17/10/2026): 116 imagens, 12 GiB → 4,8 GiB, 11 min, 1,3 s de CPU, 21 MB de RAM.
- `--orphans` (ou `PRUNE_ORPHANS=1` no `/etc/registry-prune.env`): apaga também manifestos que nenhuma
  tag que ficou alcança. Necessário no registry em disco local que recebe imagem do buildx
  (índice + plataforma + atestado): apagar o índice deixa os filhos soltos e o garbage-collect não
  os pega. Em S3 (o nosso) a listagem não existe e o passo é pulado.
- VPS da AYA (17/10/2026): sem fila `heavy`, unidade `registry-prune-sem-fila.service`; 277 imagens +
  853 manifestos soltos, volume 7,5 GB → 687 MB, 357 blobs das 23 imagens mantidas conferidos.
  Para de enviar novos envios enquanto houver upload aberto em `_uploads` (GitHub Actions).
