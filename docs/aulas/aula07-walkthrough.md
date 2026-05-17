# Aula 07 — Roteiro do walkthrough (Bloco 3)

Apoio ao instrutor para o walkthrough ao vivo do PR #1 dentro da aula 07
("Hello World, Continuous Deployment", 19/05/2026, Hermano Peixoto).

**Tempo alvo:** 40 min de walkthrough dentro da aula de 120 min.

## Pré-aula (instrutor)

- [ ] Confirmar que PR #1 está mergeado em `main` e CI está verde.
- [ ] Abrir 4 abas no navegador, na ordem:
  1. `https://github.com/josercf/inteli-px4-cicd-demo`
  2. `https://github.com/josercf/inteli-px4-cicd-demo/actions` (escolher uma run verde recente)
  3. `https://github.com/josercf/inteli-px4-cicd-demo/pkgs/container/px4-sitl`
  4. `http://20.206.111.75:9000/dashboard?id=inteli-px4-cicd-demo`
- [ ] Confirmar que SonarQube está acessível (`curl http://20.206.111.75:9000/api/system/status` → `UP`).
- [ ] Ter terminal aberto para `docker run --rm ghcr.io/josercf/px4-sitl:<sha>` (opcional, se quiser provar imutabilidade ao vivo).

## Roteiro de 40 min

### (5 min) Tour pelo repo — Aba 1

- Slide 15 da aula como apoio.
- Mostrar `README.md` — onde explica setup em <5 comandos.
- Abrir `.gitmodules` — provar que PX4 está pinado em `v1.16.2`.
- Abrir `libs/drone_modeling/dynamics.py` — função pequena, type-hinted, com docstring.
- Abrir `tests/unit/test_dynamics.py` — 4 testes parametrizados por classe.
- Abrir `docs/adrs/ADR-001-wrapper-com-submodulo.md` — mostrar que decisão de arquitetura tem rastro escrito.

**Mensagem-chave:** disciplina não custa caro. Estrutura clara desde o commit 1.

### (10 min) Pipeline em ação — Aba 2

- Slide 16 da aula como apoio.
- Mostrar uma run recente verde no Actions.
- Clicar em cada job em ordem:
  - **python-quality**: mostrar steps (checkout, setup-python, ruff, black, mypy, pytest). Apontar `coverage.xml` no upload-artifact.
  - **sonar-scan**: mostrar que dura ~40s e tem `continue-on-error: true` (apontar o badge "skipped" ou "failed allowed").
  - **sitl-build**: mostrar tempo (~12-20min cold ou ~2min warm com cache). Apontar `tags:` com `${{ github.sha }}`.
  - **deploy-dev**: mostrar que rodou pytest via docker compose. Mostrar logs do SITL anexados como artefato.

**Mensagem-chave:** todo job tem propósito, ordem importa, dependências entre jobs são explícitas.

### (8 min) `ci.yml` comentado — slides 17 e 18

- Não abrir o YAML cru no GitHub (muito ruído visual).
- Usar slides 17 e 18 que têm o YAML + anotações ao lado.
- Explicar pontos não-óbvios:
  - `submodules: false` em python-quality vs `recursive` em sitl-build — economia.
  - `cache: pip` reduz tempo de instalação.
  - `cache-from/cache-to` no docker buildx — magia que faz rebuild ser 2min em vez de 20.
  - `GITHUB_TOKEN` automático para GHCR — sem PAT custom.

**Mensagem-chave:** YAML não é mágica. Cada linha tem motivação.

### (5 min) GHCR — Aba 3 + slide 19

- Mostrar página do pacote `px4-sitl` no GHCR.
- Listar as tags publicadas — uma por commit no main, mais `:dev-<sha>` e `:buildcache`.
- Clicar em uma tag — mostrar layers, tamanho, data de publicação.
- Se quiser provar: terminal com `docker pull` e `docker run --rm` da imagem. Container sobe, PX4 inicializa, output do slide 19 aparece. **Esse momento é o "Hello World" literal.**

**Mensagem-chave:** o artefato existe, está rastreado, é deployável agora. CD entregou.

### (7 min) Sonar dashboard — Aba 4 + slide 20

- Mostrar o dashboard do projeto. Hoje deve ter:
  - Coverage ~100% (libs minimal).
  - 0 bugs, 0 vulnerabilities (libs trivial).
  - Quality Gate "Sonar Way" associado mas não é gate obrigatório do PR ainda.
- Clicar em "Code" → mostrar `dynamics.py` com indicadores de cobertura inline.
- Clicar em "Activity" → mostrar histórico de análises (uma por push na main).

**Mensagem-chave:** Sonar é o "raio-X contínuo" da saúde do código. Hoje informativo, na aula 10 vira polícia.

### (5 min) Discussão guiada

Perguntas pra fazer na sala (uma por vez, aguardar):

1. "Quem dispara esse pipeline? Em quais eventos?"
   - Resposta: push em main, PR em main. Configurado em `on:` do ci.yml.
2. "O que acontece com a imagem se o teste falhar?"
   - Resposta: depende. Se `python-quality` falhar, jobs seguintes nem rodam (no `needs:` chain). Se `deploy-dev` falhar, imagem já foi publicada mas marcamos como não-deployável.
3. "Onde mora a release de fato?"
   - Resposta: GHCR. O git mora no GitHub; o binário mora no GHCR. São coisas distintas, vivem em sistemas distintos.
4. "O que falta pra esse pipeline virar 'release de produção real'?"
   - Resposta: ambientes adicionais (staging, prod), aprovação manual, métricas de missão validadas, quality gates obrigatórios. **Próximas 3 aulas.**

## Erros comuns durante demo ao vivo

- **CI ainda rodando quando a aula começa:** plano B é abrir uma run anterior já verde.
- **GHCR mostra "Cannot pull image":** PR de aluno-fork sem permissão; confirmar que está olhando a run do repo `josercf/`.
- **Sonar fora do ar:** mostrar print salvo em `docs/aulas/screenshots/sonar-dashboard.png` (preparar antes).

## Slides ↔ momento

| Bloco | Slides | Tempo |
|---|---|---|
| Tour pelo repo | 15 | 5 min |
| Pipeline em ação | 16 | 10 min |
| ci.yml comentado | 17, 18 | 8 min |
| GHCR | 19 | 5 min |
| Sonar | 20 | 7 min |
| Discussão | (sem slide) | 5 min |

Total: 40 min.
