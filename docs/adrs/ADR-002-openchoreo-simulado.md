# ADR-002: OpenChoreo simulado via re-tag GHCR (vs. cluster real)

- **Data:** 2026-05-17
- **Status:** Aceita
- **Decisores:** José Romualdo, Hermano Peixoto

## Contexto

A spec original do demo (`docs/superpowers/specs/2026-05-17-px4-cicd-demo-design.md`)
considerou OpenChoreo como camada de deployment entre ambientes (`dev`,
`staging`, `prod`). OpenChoreo requer um cluster Kubernetes funcional com
gateway + control plane + namespaces por ambiente.

Subir esse cluster durante a Sprint 03 (com prazo apertado pra Aula 10) é
inviável: ~1 dia de setup + risco de instabilidade no demo presencial.

## Decisão

OpenChoreo entra como **conceito didático**, materializado em manifestos
versionados em `openchoreo/`, mas **a promoção entre ambientes é feita via
re-tag de imagens no GHCR** (vide `tools/promote_release.py` + `promote.yml`).

## Motivações

- **Mantém a lição central**: a mesma imagem (mesmo SHA) é promovida de
  ambiente em ambiente, sem rebuild. Isso é o coração do CD imutável,
  independente da camada que faz a promoção.
- **Setup viável**: re-tag GHCR é um `docker tag + docker push` de 2s. Não
  exige infra adicional.
- **Pedagogia honesta**: alunos veem manifestos OpenChoreo reais (`component.yaml`,
  `release.yaml`) como referência do que seria usado em produção. Aula 10
  mostra os manifestos como "isso é o que viria depois".
- **Reversibilidade**: trocar pra OpenChoreo real depois é só configurar
  cluster e mudar o workflow `promote.yml` pra usar `oc` ou similar. Os
  manifestos já estão lá.

## Riscos conhecidos

- **Aluno pode confundir** "promoção via re-tag" com "isso é OpenChoreo".
  Mitigação: aula 10 deixa explícito que OpenChoreo é a camada que faria
  isso de forma mais robusta em produção real (com rollback automático,
  observability, gateway de aprovação).

## Consequências

**Positivas:**
- Pipeline de promoção funciona em <30s end-to-end.
- Demo é reproduzível sem dependência de cluster externo.
- Manifestos OpenChoreo viram material didático versionado.

**Negativas:**
- Não exercitamos a operação real do OpenChoreo (RBAC, gateway, etc).
- Quem clonar o demo e quiser usar OpenChoreo real precisa adaptar o `promote.yml`.

## ADRs relacionadas

- ADR-004 (promoção entre ambientes via re-tag de imagem) — operacionaliza esta decisão.

## Trabalho futuro

Quando organizações que adotarem o demo quiserem OpenChoreo real:
1. Provisionar cluster k8s + OpenChoreo control plane.
2. Aplicar manifestos `openchoreo/*.yaml` no cluster.
3. Substituir steps `docker tag + push` em `promote.yml` por `oc deploy` ou
   chamada da API OpenChoreo.
