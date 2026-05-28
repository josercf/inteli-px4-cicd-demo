# Aula 09 — Roteiro do walkthrough (Bloco 3)

Apoio ao instrutor para o walkthrough ao vivo do PR #3 dentro da aula 09
("Você escreve (bons) testes de integração?", 26/05/2026, Hermano Peixoto).

**Tempo alvo:** 25min de walkthrough dentro do Bloco 3 (aula de 120min total).

## Pré-aula (instrutor)

- [ ] PR #3 mergeado em `main`. CI verde no último run.
- [ ] Abrir 5 abas no navegador:
  1. PR #3 mergeado: `https://github.com/josercf/inteli-px4-cicd-demo/pull/3`
  2. `tests/sitl/conftest.py` no GitHub (mostra fixtures)
  3. `tests/sitl/test_physical_invariants.py` no GitHub (mostra parametrização)
  4. `docs/testing-philosophy.md` no GitHub (documento de referência)
  5. Um exemplo de teste falhando com mensagem informativa (pode ser print salvo
     ou um run intencionalmente quebrado pra demo)

## Roteiro de 25 min

### (3 min) Recap visual: o problema do PR #2

- Abrir o blame de `tests/sitl/test_mission_square.py` antes do PR #3.
- Mostrar duplicação: cada teste fazia setup MAVSDK inline.
- Provocar: "Se adicionarmos 3 testes novos amanhã, o que acontece?"
- Resposta esperada: triplicar a duplicação, refactor vira urgente.

**Mensagem-chave:** suite de teste é código de produção. Mesma higiene.

### (7 min) `conftest.py` — explicar fixtures — Aba 2

- Mostrar a estrutura: scope=session (imutável) vs scope=function (fresh).
- Apontar `mavsdk_system` com `yield` + cleanup `land()`.
- Apontar `run_mission` factory: 1 fixture vira N testes.
- Apontar `latest_ulog_path` com `pytest.skip` se vazio (não `assert False`).

**Mensagem-chave:** fixture bem feita elimina 80% da repetição. Boundary clara entre "setup que sempre roda" e "teste específico".

### (7 min) `test_physical_invariants.py` — parametrização — Aba 3

- Mostrar `MISSIONS = [pytest.param(...)]` — single source of truth.
- Mostrar `@pytest.mark.parametrize("mission_telemetry", MISSIONS, indirect=True)`.
- Apontar a mensagem de cada `assert` — explica regra física + valor real.
- Demonstrar: adicionar 2ª missão = adicionar 1 linha em MISSIONS, todos os
  invariantes passam a rodar contra ela.

**Mensagem-chave:** parametrização certa multiplica cobertura sem multiplicar código.

### (5 min) `testing-philosophy.md` — Aba 4

- Abrir o doc no GitHub e fazer scroll pelas seções.
- Apontar a tabela FIRST e como cada item se conecta com `conftest.py`.
- Mostrar a seção "antipatterns": bad vs good code — o material do quiz da aula
  veio daí.
- **Conexão importante:** "esse doc é nosso checklist de PR review".

**Mensagem-chave:** convenções documentadas no repo > convenções orais. Próximo dev encontra contexto sem perguntar.

### (3 min) Discussão guiada

Perguntas pra fazer na sala (uma por vez):

1. "Vocês usariam `mavsdk_system` ou criariam System() direto no teste?"
   - Resposta esperada: fixture. Cleanup garantido. Trocar versão MAVSDK
     vira 1-line change em conftest, não N alterações.
2. "Se 1 invariante falha em 1 missão de 5, qual a primeira coisa que vocês
   olhariam?"
   - Resposta: log do PX4 dessa missão específica, não os 4 que passaram. Isolamento ajuda a debugar.
3. "Como detectar que um teste novo do colega *não* tem valor (3 critérios)?"
   - Resposta: não responde "que regressão pega?", quebra a cada refactor não-relacionado, ou mensagem é genérica. Seção "Critérios pra 'esse teste tem valor?'" do doc.

## Erros comuns durante demo ao vivo

- **PR #3 não mergeado:** mostrar o PR aberto + diff. Funciona, só é mais ruído visual.
- **Fixture async vs sync confunde:** `mavsdk_system` é `async`, `run_mission` é `def`. Reason: subprocess.run não precisa async; MAVSDK precisa. Vale pausar 30s pra explicar.
- **Aluno pergunta "scope=class faz sentido aqui?":** vale, mas demo prefere session/function por simplicidade. Convidar pra ler doc do pytest após aula.

## Slides ↔ momento

| Bloco | Slides | Tempo |
|---|---|---|
| Recap problema PR #2 | 5 | 3 min |
| conftest.py | 15 | 7 min |
| invariantes + parametrize | 16 | 7 min |
| testing-philosophy.md | 17 | 5 min |
| Discussão | (sem slide) | 3 min |

Total: 25 min.

## Conexão com aulas adjacentes

- **Aula 08 (José)**: produziu as métricas que esses testes validam.
- **Aula 10 (Hermano)**: transforma esses testes em **gates obrigatórios** —
  PR não merge se teste vermelho. Conexão direta com `quality_gates.yaml` que
  vem no PR #4.
