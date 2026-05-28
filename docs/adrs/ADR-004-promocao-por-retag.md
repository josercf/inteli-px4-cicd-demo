# ADR-004: Promoção entre ambientes via re-tag de imagem (vs. rebuild)

- **Data:** 2026-05-17
- **Status:** Aceita
- **Decisores:** José Romualdo, Hermano Peixoto

## Contexto

Pipeline produz uma imagem PX4 SITL em cada commit, com tag `dev-<sha>` no
GHCR. Pra promover essa imagem pros ambientes `staging` e `prod`, há duas
abordagens:

1. **Rebuild por ambiente** — cada ambiente compila do mesmo commit, gerando
   binários distintos. Lento e arriscado (build não-determinístico).
2. **Re-tag de imagem** — mesma imagem (mesmo SHA) ganha tags adicionais
   (`staging-<sha>`, `prod-<sha>`) sem recompilação. Idêntico byte-a-byte.

## Decisão

**Re-tag.** Implementado em `tools/promote_release.py` + `.github/workflows/promote.yml`.

## Motivações

- **Imutabilidade**: a imagem que passou em testes é a mesma que vai a prod.
  Sem espaço pra "compilou diferente em outro momento".
- **Velocidade**: re-tag é `docker tag + docker push` (~5s). Rebuild é
  ~10min mesmo com cache.
- **Rastreabilidade**: 3 tags apontando pro mesmo SHA mostram o histórico
  da promoção. Forensics fica direto.
- **Padrão da indústria**: Spinnaker, Argo Rollouts, OpenChoreo (vide
  ADR-002) — todos seguem o mesmo princípio.

## Riscos conhecidos

- **Sem dependências por ambiente**: se algum ambiente precisar de build
  diferente (ex.: `prod` com `--strip-debug`), re-tag não cobre. Mitigação:
  matar essa categoria de dependência cedo (configs vêm via env, não via
  build flag).
- **Confusão de tag**: 3 tags apontando pro mesmo SHA pode confundir quem
  busca por nome de tag. Mitigação: convenção `<ambiente>-<sha7>` deixa o
  ambiente legível.

## Consequências

**Positivas:**
- Promoção em <30s, sem custo de runner.
- Auditoria fica trivial: comparar SHAs entre tags.
- Rollback é re-tag inverso: `prod-old-sha` ↔ `prod-current-sha`.

**Negativas:**
- Não há "build per env" pra configurações que dependem de tempo de
  compilação. Forçamos config via env runtime.

## ADRs relacionadas

- ADR-002 (OpenChoreo simulado) — contexto pra a estratégia de promoção.
