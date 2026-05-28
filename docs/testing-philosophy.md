# Filosofia de testes do demo

Documento de referência que acompanha PR #3 (Aula 09 — "Você escreve (bons)
testes de integração?"). Princípios que guiaram a estrutura de testes do repo.

## FIRST

Robert Martin, *Clean Code*. Testes devem ser:

| Sigla | Princípio | Como aplicamos |
|---|---|---|
| **F**ast | Rápido o suficiente pra rodar a cada save | Unit tests rodam em <1s. SITL tests isolados em job próprio. |
| **I**ndependent | Ordem de execução não importa | Cada teste roda missão completa; fixtures limpam estado. Sem variáveis compartilhadas mutáveis. |
| **R**epeatable | Mesmo input → mesmo resultado | Timeouts duros, sem `sleep()` arbitrário. Espera por estado, não por tempo. |
| **S**elf-validating | Pass/fail binário, sem inspeção manual | `pytest.fail()` com diagnóstico embutido. Mensagens explicam *qual invariante quebrou e por quê*. |
| **T**imely | Escritos junto com (ou antes do) código | TDD: cada lib (geometry, mission, extract_metrics) tem teste vermelho → verde → refactor. |

## Pirâmide vs Troféu

**Pirâmide clássica** (Martin Fowler, 2012): muitos unit, alguns integration, pouco e2e.

**Padrão Troféu** (Kent Dodds, 2018): poucos unit, *muitos integration*, alguns e2e, base de static analysis.

### Nosso compromisso

Pra firmware embarcado, **trofeu se aproxima mais da realidade**:

- Unit tests (`tests/unit/`) cobrem **funções puras**: geometria, conversão NED, redução estatística. ~40 testes, <1s total. 100% cobertura em `libs/`.
- Integration tests (`tests/sitl/`) são onde o valor está: drone simulado + MAVSDK + extração de telemetria. Cada teste dispara missão completa de ~90s.
- Static analysis: ruff + black + mypy strict + Sonar. Gates obrigatórios.
- E2E (HIL, voo real): fora do escopo do demo, citado na Aula 10 como "próximo nível".

A pirâmide tradicional não funciona em firmware porque a lógica pura é pouca (geometria, conversões). O valor real está na composição (PX4 + simulador + controle), que só integration test detecta.

## Antipatterns evitados no demo

### 1. `time.sleep()` arbitrário

```python
# RUIM: presume timing, vira flaky em CI lento
drone.arm()
time.sleep(5)  # esperar... talvez ficar armado?
drone.start_mission()
```

```python
# BOM: espera por estado observável, com timeout duro
await _arm_with_retry(drone, attempts=5, delay_s=3.0)  # retry com sinal claro
await drone.mission.start_mission()
```

Vide `tools/run_mission.py:_arm_with_retry` — refatorado no PR #2 após
descobrirmos que arm() retorna COMMAND_DENIED em SITL durante os primeiros
segundos.

### 2. Estado compartilhado entre testes

```python
# RUIM: testes acoplados pela ordem
DRONE = None  # global

def test_arm():
    global DRONE
    DRONE = create_system()
    DRONE.arm()

def test_takeoff():  # quebra se test_arm não rodou primeiro
    DRONE.takeoff()
```

```python
# BOM: cada teste recebe fixture fresca
def test_takeoff(mavsdk_system):  # fixture cria + cleanup
    asyncio.run(_perform_takeoff(mavsdk_system))
```

Vide `tests/sitl/conftest.py` — fixtures session/function-scoped com teardown
explícito.

### 3. Asserções sem diagnóstico

```python
# RUIM: quando falha, você não sabe por quê
assert max_accel < 15
```

```python
# BOM: mensagem explica a regra violada
assert max_accel < 15.0, (
    f"violação de invariante: aceleração máxima {max_accel:.2f} m/s² "
    f"excede limite mecânico de 15 m/s²"
)
```

Vide `tests/sitl/test_physical_invariants.py` — toda asserção tem mensagem
contextualizando a regra física que ela protege.

### 4. Misturar baseline com invariante

**Baseline threshold** (mudável): "missão dura entre 30 e 240s — fora disso é
provavelmente bug". É um sanity check, espera ajuste conforme demo evolui.

**Invariante físico** (imutável): "aceleração não passa de 15 m/s² —
*nunca* deveria passar, em qualquer missão". É lei física do hardware.

Separar os dois deixa claro o que é negociável e o que não é. Vide
`tests/sitl/test_mission_square.py` (baseline) vs
`tests/sitl/test_physical_invariants.py` (invariantes).

## Hierarquia de "qualidade de teste"

Do mais barato/raso ao mais caro/profundo:

1. **Compila + lint passa** — ruff, black, mypy. Trivial mas pega 30% dos bugs
   simples (typo, tipo errado).
2. **Unit verde** — função pura validada. Pega lógica errada em isolado.
3. **Integration verde** — composição funciona. Detecta bugs de interface,
   timing, concorrência, configuração.
4. **Baseline check** — sistema está "no padrão". Detecta regressões de
   performance que não quebram funcionalidade.
5. **Invariante físico** — sistema respeita leis do domínio. Detecta bugs
   sutis que escapam tudo acima (drone passou abaixo do solo? bateria
   despencou? geofence violado?).

Demo cobre 1-5. PR #4 (Aula 10) transforma 4 e 5 em **gates obrigatórios**
(bloqueio de merge).

## Frequência de execução

| Tipo | Quando roda | Tempo típico | Custo |
|---|---|---|---|
| Lint | A cada save (pre-commit) + CI | <5s | grátis |
| Unit | A cada save + CI | <1s | grátis |
| SITL (integration) | A cada PR + main | ~90s missão + setup ~5min total | 1× runner self-hosted |
| Invariantes físicos | A cada PR (junto com SITL) | reusa missão | mesmo custo do SITL |

Se rodar tudo a cada commit do dev seria caro demais (8min de CI por commit).
Por isso unit roda localmente no `pre-commit` e SITL só roda em push pro
PR. Trade-off feedback rápido × custo de recurso.

## Critérios pra "esse teste tem valor?"

Antes de adicionar um teste novo, perguntar:

1. **Que regressão real esse teste pegaria?** Se não souber dar um exemplo
   concreto, talvez seja teste decorativo.
2. **Vai falhar com falso positivo em mudanças não-relacionadas?** Teste muito acoplado a
   detalhes de implementação fica vermelho a cada refactor.
3. **Quando falhar, a mensagem ensina o que mudar?** Stack trace genérico
   força debugger; mensagem específica força fix imediato.
4. **Custo de manter > custo de rodar?** Teste que ninguém entende vira
   débito técnico.

Vide PR #3 — todos os testes adicionados (invariantes físicos, parametrização)
respondem essas 4 perguntas explicitamente no docstring.

## Referências

- Martin Fowler, *Test Pyramid* — <https://martinfowler.com/bliki/TestPyramid.html>
- Kent Dodds, *Testing Trophy* — <https://kentcdodds.com/blog/the-testing-trophy-and-testing-classifications>
- Robert Martin, *Clean Code*, cap. 9 (Testes).
- Martin Fowler, *Eradicating Non-Determinism in Tests* —
  <https://martinfowler.com/articles/nonDeterminism.html>
