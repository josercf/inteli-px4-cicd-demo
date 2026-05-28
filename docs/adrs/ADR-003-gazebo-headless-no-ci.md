# ADR-003: Gazebo headless no CI (vs. com render)

- **Data:** 2026-05-17
- **Status:** Aceita (parcialmente suplantada por ADR-007)
- **Decisores:** José Romualdo, Hermano Peixoto
- **Veja também:** ADR-007 (jmavsim no PR #2, Gazebo postponed)

## Contexto

A spec original previa rodar Gazebo Garden (`gz_x500`) no SITL pra ter
física rica em missões. Como Gazebo tem opção `--render-engine ogre`, surge
a pergunta: rodar com render gráfico ou headless?

## Decisão

**Headless sempre no CI.** Variável de ambiente `HEADLESS=1` é setada no
Dockerfile.sitl; runner GitHub-hosted nem tem GPU/X11 acessível.

## Motivações

- **CI não tem GPU**: GitHub Actions runners free não fornecem aceleração
  gráfica. Render forçaria software rendering ultra-lento (Llvmpipe, ~5x
  mais devagar).
- **Não há valor pedagógico no CI**: ninguém está vendo o drone voar durante
  o pipeline. O ULog é a saída — render é display para humano.
- **Dev local pode ativar render**: criamos `docker-compose.gui.yml` (postponed
  com Gazebo) que monta X11 do host pra ver o drone voando em laptops com display.
- **Custo de runner**: render multiplica tempo de build/run por ~3-5x. Pra CI
  rápido, headless é critico.

## Consequências

**Positivas:**
- CI fecha em ~8min (vs. ~30min com render).
- Sem dependência de GPU no runner.

**Negativas:**
- Demonstrações em sala não mostram o drone voando ao vivo durante CI.
  Mitigação: walkthroughs ao vivo abrem `docker compose -f docker-compose.gui.yml`
  no laptop do instrutor, fora do CI.

## Status atualizado

PR #2 (ADR-007) decidiu **adiar Gazebo** pra PR futuro — usamos `jmavsim` por
ora. Esta ADR-003 permanece relevante: quando Gazebo voltar ao demo, será
**headless** no CI.

## ADRs relacionadas

- ADR-007 (jmavsim no PR #2, Gazebo postponed)
