# ADR-005: Thresholds dos quality gates e processo de revisão

- **Data:** 2026-05-18
- **Status:** Aceita
- **Decisores:** José Romualdo, Hermano Peixoto

## Contexto

PR #4 (Aula 10) transforma métricas do PR em **gates obrigatórios** —
pipeline falha se qualquer threshold for violado. Os valores precisam:

1. Detectar regressões reais.
2. Não ser tão apertados que toda mudança legítima é bloqueada (gates
   "barulhentos" viram piadas internas que ninguém respeita).
3. Ter processo claro de revisão (quem decide mudar e por quê).

## Decisão

Valores iniciais (PR #4) em `quality_gates.yaml`:

| Gate | Threshold | Justificativa |
|---|---|---|
| `coverage.min_line_coverage` | 0.80 | Pragmático: 80% pega bugs sem forçar testes inúteis. |
| `mission_metrics.max_acceleration_m_s2` | 15.0 | Limite mecânico nominal do x500 (vide test_physical_invariants). |
| `mission_metrics.max_mission_duration_s` | 180 | Baseline ~85s + folga 2x pra ruído de SITL. |
| `mission_metrics.min_altitude_stability_m` | 0.5 | Std máximo aceitável em cruzeiro. |
| `mission_metrics.max_battery_drop_per_minute_pct` | 8.0 | Consumo nominal x500. |
| `sonar.require_quality_gate_passed` | `true` | Quality Gate Sonar Way no projeto. |

Esses valores são **versionados** no repo. Alteração:
- Reduzir threshold (mais frouxo): PR comum, com justificativa no commit.
- Apertar threshold: idem, mas reviewer deve garantir que pipeline atual
  ainda passa.
- **Mudar fundamentalmente** (ex.: trocar `max` por `p99`, ou adicionar/remover
  gate): requer nova ADR.

## Motivações

- **Versionado**: arquivo no repo > config oral. Decisões ficam rastreáveis
  via `git log quality_gates.yaml`.
- **Conservador inicial**: melhor passar mais que falsificar. Vamos apertar
  com dados, não com ansiedade.
- **Separação baseline × invariante** (vide `docs/testing-philosophy.md`):
  quality gates aqui são baseline (mudável). Invariantes físicos (em
  `tests/sitl/test_physical_invariants.py`) são imutáveis.

## Riscos conhecidos

- **Valor cravado errado**: threshold pode ser muito frouxo (não pega
  regressão) ou muito apertado (bloqueia mudança legítima). Mitigação:
  revisar a cada sprint, ajustar com dados de runs reais.
- **Gate ignorado**: se ficar quebrando muito, time vai querer disable.
  Mitigação: cada gate fica acompanhado de justificativa no YAML;
  remoção exige ADR.

## Consequências

**Positivas:**
- Pipeline tem critério objetivo de "pronto pra merge".
- Mudanças nos critérios passam por revisão (são código).

**Negativas:**
- Mudança de threshold precisa de PR — overhead pra ajustes finos.

## Processo de revisão (proposto)

Final de cada sprint, revisar `quality_gates.yaml` com base em:
1. Histórico de gates quebrados (falsos positivos? regressões reais?).
2. Mudanças no hardware/missão.
3. Evolução do baseline (média histórica das métricas no main).

## ADRs relacionadas

- ADR-006 (Sonar self-hosted) — ferramenta que entrega `sonar.require_quality_gate_passed`.
- ADR-007 (jmavsim no PR #2) — afeta valores de baseline.
