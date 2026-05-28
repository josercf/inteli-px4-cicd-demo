# ADR-008: Aprovação manual entre mission-test e quality-gates

- **Data:** 2026-05-28
- **Status:** Aceita
- **Decisores:** José Romualdo, Hermano Peixoto

## Contexto

PR #4 (Aula 10) estabeleceu quality-gates como veredito automático: pipeline
falha sozinho se algum threshold for violado. Funciona bem em produção mas
tem dois problemas no contexto da aula:

1. **Pedagógico**: o resumo de métricas (comentário do `mission-test` no PR)
   passa direto, e a turma não tem um ponto explícito pra parar, olhar
   números e discutir. O gate automático "engole" a discussão.
2. **Auditoria**: gates objetivos são bons, mas o instrutor quer registrar
   que olhou o resumo antes do enforcement — equivalente a um sanity check
   humano antes do robô bater o martelo.

## Decisão

Adicionar job `manual-approval` no pipeline, entre `mission-test` e
`quality-gates`, ligado ao environment `quality-review` do GitHub. O
environment tem dois **required reviewers**: `josercf` e `hermanopoj`
(qualquer um aprova). Em PR, `quality-gates` só roda após aprovação. Em
push direto pra main, o job é skipped e `quality-gates` segue executando
(via `if: needs.manual-approval.result == 'skipped'`).

## Motivações

- **Pausa pedagógica explícita**: durante a aula a turma vê o pipeline
  travar, lê o comentário de métricas, e o instrutor aprova ao vivo
  explicando o critério. Vira momento de aula, não detalhe perdido.
- **Sem custo extra fora de aula**: timeout de 60min — se ninguém aprovar,
  o job falha e o PR fica destravado pra refazer. Push pra main não exige
  aprovação (main é post-merge, ponto sem discussão).
- **Reutiliza environment do GitHub**: feature nativa, sem dependência
  externa. Required reviewers é mecanismo padrão.

## Riscos conhecidos

- **Aprovação esquecida fora de aula**: PR fica pendurado até timeout.
  Mitigação: 2 reviewers configurados (qualquer um destrava); timeout
  de 60min impede ocupação indefinida de runner.
- **Required reviewers viram bottleneck**: se nem josercf nem hermanopoj
  estiverem disponíveis, PR fica travado. Mitigação aceitável no escopo
  didático — em produção real, listar mais reviewers ou usar team.
- **Aluno tenta aprovar próprio PR**: `prevent_self_review: false` permite
  que o autor (se reviewer) aprove. Não é problema didaticamente — a
  intenção é demonstrar o mecanismo, não enforçar 4-eyes review.

## Consequências

**Positivas:**
- Aula 10 ganha um beat narrativo claro: "robôs olharam, agora humano olha,
  depois o veredito automático final."
- Pipeline fica auditável — quem aprovou + timestamp no log do job.
- Demonstra para os alunos uma feature de pipelines reais (manual approvals)
  que aparece em deploys de produção.

**Negativas:**
- Latência adicional no merge — qualquer PR fora de aula precisa de alguém
  aprovando manualmente.
- Mais um job na chain — leva o failure-fast a +1 etapa de espera.
- `quality-gates` agora tem `needs: [mission-test, manual-approval]` com
  expressão `if:` complexa pra lidar com os dois cenários (PR vs push).

## ADRs relacionadas

- ADR-005 (Thresholds dos quality gates) — define o que será aprovado.
