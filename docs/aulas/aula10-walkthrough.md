# Aula 10 — Roteiro do walkthrough (Bloco 3)

Apoio ao instrutor para os 30min do Bloco 3 da aula 10 ("Esteira de CI como
guardiã da qualidade", 28/05/2026, Hermano Peixoto).

## Pré-aula

- [ ] PR #4 mergeado em `main`. CI verde + comentário de quality-gates visível.
- [ ] Abrir 5 abas:
  1. `https://github.com/josercf/inteli-px4-cicd-demo/pull/4` (mergeado, com comments)
  2. `quality_gates.yaml` no GitHub
  3. `tools/quality_gates.py` no GitHub
  4. Aba Actions do último run mostrando os 5 jobs sequenciais
  5. Settings → Environments do repo (mostrar staging/prod com approval)

## Roteiro 30 min

### (5 min) Antes vs depois — slides 10 + 11

- Slide 10 (paralelo vs sequencial): explicar trade-off.
- Slide 11 (pipeline ANTES vs DEPOIS): mostrar visualmente os 5 jobs em cadeia.
- Apontar `continue-on-error: true → false` no Sonar.

**Mensagem-chave:** o pipeline não mudou ferramentas. Mudou política. Mesmas peças, ordem e enforcement diferentes.

### (7 min) quality_gates.yaml — aba 2 + slide 13

- Mostrar o arquivo aberto no GitHub.
- Apontar cada seção (coverage, mission_metrics, sonar).
- Provocar: "Por que 15 m/s²? Por que 80% coverage?"
- Resposta: alinhamento com invariantes (PR #3) + pragmatismo.
- Mostrar `git log quality_gates.yaml` (CLI ou via GitHub UI) — quem mudou e quando.

**Mensagem-chave:** YAML versionado > config oral. Mudança passa por PR.

### (8 min) tools/quality_gates.py — aba 3 + slide 14

- Abrir `evaluate()` no GitHub.
- 3 fontes: coverage.xml, metrics.json, Sonar API.
- Explicar exit code != 0 = pipeline falha = merge bloqueado.
- Falar de testes unit (11) que cobrem o módulo.

**Mensagem-chave:** Cada gate é uma função pequena, testada, com fail explícito. Não há "mágica".

### (5 min) Comentário no PR — aba 1 + slide 16

- Abrir o PR #4 mergeado.
- Scroll pra um comentário de quality-gates verde.
- Provocar: "E se esse fosse vermelho?"
- Resposta: botão Merge desabilitado, reviewer não pode forçar.
- Mostrar Settings → Branches → branch protection rules (se configurado).

**Mensagem-chave:** Decisão automática + auditável > decisão humana opaca.

### (5 min) Environments e approval — aba 5 + slide 19

- Settings → Environments.
- Mostrar `staging` e `prod` com required reviewers.
- Explicar `promote.yml` — fluxo dispatch manual com approval.

**Mensagem-chave:** Gate técnico (quality_gates.py) + gate humano (environment approval). Defesa em camadas.

## Discussão guiada

1. "Quem deveria aprovar a promoção pra prod? Por quê?"
2. "Se o quality-gate falha em PR aberto há 1 mês, time deveria revisar threshold ou consertar regressão?"
3. "Vocês adicionariam um 6º gate na suite atual? Qual e por quê?"

## Slides ↔ momento

| Bloco | Slides | Tempo |
|---|---|---|
| Antes vs depois | 10, 11 | 5 min |
| quality_gates.yaml | 13 | 7 min |
| tools/quality_gates.py | 14 | 8 min |
| Comentário PR + branch protection | 16 | 5 min |
| Environments + approval | 19 | 5 min |

Total: 30 min.

## Fechamento da Sprint 03

Após a Aula 10, os grupos têm:
- Pipeline imutável (PR #1)
- Métricas no PR (PR #2)
- Bons testes (PR #3)
- Quality gates obrigatórios (PR #4)

Esse é o piso do CD pra firmware crítico. Próxima sprint (04) adiciona
performance + IaC.
