# Aula 08 — Roteiro do walkthrough (Bloco 3)

Apoio ao instrutor para o walkthrough ao vivo do PR #2 dentro da aula 08
("Extraindo métricas do pipeline de CI/CD", 22/05/2026, José Romualdo).

**Tempo alvo:** 30min de walkthrough dentro do Bloco 3 (aula de 120min total).

## Pré-aula (instrutor)

- [ ] Confirmar que **PR #2 está mergeado** em `main` e o último CI ficou verde.
- [ ] Abrir 4 abas no navegador, na ordem:
  1. `https://github.com/josercf/inteli-px4-cicd-demo/pull/2` (com o comentário de métricas)
  2. Trecho do código no GitHub: `tools/extract_metrics.py` (mostra a leitura ULog)
  3. Trecho do `ci.yml` no GitHub: bloco do job `mission-test` (mostra workflow)
  4. Aba Actions do último run verde no main, focada no job `mission-test` (logs do compose)
- [ ] Confirmar que o runner self-hosted `srv-simulador` está online (visível em Settings → Actions → Runners).
- [ ] Ter terminal aberto, conectado via SSH na VM:
  ```
  ssh -i ~/Downloads/srv-simulador_key.pem azureuser@20.226.17.227
  ```
  Pra mostrar `docker images` + `docker ps` em vivo se alguém perguntar onde a imagem mora.

## Roteiro de 30 min

### (5 min) Recap visual: o comentário do PR — Aba 1

- Mostrar o comentário **📊 Métricas da missão (square_50m)** no PR #2.
- Provocar: "O que vocês veem aqui?" Esperar resposta sobre cada linha.
- Apontar o pé do comentário ("Quality gates obrigatórios entram no PR #4") — antecipa a Aula 10.

**Mensagem-chave:** o reviewer não rodou simulador. Ele lê a tabela e decide.

### (8 min) Onde os números vêm? — Aba 2

- Abrir `tools/extract_metrics.py` no GitHub (ou na IDE local).
- Mostrar o helper `get_topic(name)` — pyulog devolve lista, não dict.
- Mostrar `vehicle_local_position` sendo lido → conversão `altitudes_m = [-z]`.
- Mostrar `compute_metrics_from_data()` — onde a redução vira política
  (max vs p99, cruise window ≥ 5m, etc).

**Mensagem-chave:** cada decisão na função é uma política. Outro time decidiria diferente. Versionar essas decisões no repo é a diferença entre "medir" e "fingir que mede".

### (7 min) Como o pipeline acopla isso? — Aba 3

- Abrir `.github/workflows/ci.yml` no GitHub, navegar até o job `mission-test`.
- Apontar `runs-on: [self-hosted, px4-sitl]` — runner próprio.
- Mostrar o `run:` do step "Run mission compose" — destacar:
  - `docker compose up --abort-on-container-exit --exit-code-from tester`
  - `docker compose cp tester:/app/reports ./reports` — extração do artifact
- Mostrar o step `actions/github-script@v7` — explicar que cria o comentário via API.

**Mensagem-chave:** o pipeline não é mágica. Cada passo é configurável e versionado. Quem mudar a tabela vai por PR.

### (6 min) Por que self-hosted? — Aba 4

- Abrir o job `mission-test` da última run verde no main.
- Mostrar duração (~8min total).
- Explicar o caminho que tomamos:
  1. **Tentamos GitHub-hosted no PR #1**: deploy-dev cancelava em 15min por "stuck in shutdown".
  2. **Diagnóstico via SSH na VM**: pymavlink + shared netns resolveu localmente em 1s.
  3. **Self-hosted runner**: única configuração robusta + cache local da imagem SITL.

**Mensagem-chave:** decisão de infra (self-hosted) veio de evidência (CI cancelando). Não foi escolha estética. ADR-001/006 documentam isso.

### (4 min) Discussão guiada

Perguntas pra fazer na sala (uma por vez, aguardar):

1. "Se vocês fossem reviewer e olhassem essa tabela, qual número chamaria atenção primeiro?"
   - Resposta esperada: `max_acceleration_m_s2`. Por que? É o único com unidade de força/segurança imediata.
2. "Por que `std_altitude_cruise_m` filtra altitude < 5m?"
   - Resposta: takeoff + landing geram transientes naturais; queremos avaliar voo estável.
3. "O que acontece se esse comentário do PR demorar 8min pra aparecer?"
   - Resposta: feedback loop ruim. Reviewer abandona o PR, volta depois. Discutir trade-off velocidade vs robustez.

## Erros comuns durante demo ao vivo

- **PR #2 ainda não mergeado:** plano B é mostrar o comentário direto no PR aberto, sem o histórico verde.
- **Runner offline:** mostrar `gh api repos/.../actions/runners` no terminal — debug ao vivo. Lição: "self-hosted falha, e é responsabilidade nossa restaurar".
- **Comentário do PR ausente:** verificar `github-script` step nos logs. Causa comum: `pull_request` event vs `push` event (script só roda em PR).

## Slides ↔ momento

| Bloco | Slides | Tempo |
|---|---|---|
| Comentário do PR | 20 | 5 min |
| extract_metrics.py | 13, 14 | 8 min |
| mission-test no ci.yml | 19 | 7 min |
| Pipeline + self-hosted | 16 | 6 min |
| Discussão | (sem slide) | 4 min |

Total: 30 min.

## Próximas aulas — onde os números viram política

- **Aula 09 (Hermano)**: discute princípios FIRST de testes que produzem essas métricas.
- **Aula 10 (Hermano)**: thresholds viram **gates obrigatórios** — `quality_gates.yaml` bloqueia merge se métrica regrediu.
