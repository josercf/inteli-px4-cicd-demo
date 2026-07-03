# ADR-006: SonarQube self-hosted (vs. SonarCloud)

- **Data:** 2026-05-17
- **Status:** Aceita
- **Decisores:** José Romualdo (instrutor mantenedor da infra)

## Contexto

PR #1 (Aula 07) introduziu análise estática via SonarQube. Duas opções:

1. **SonarCloud** — gratuito para repos públicos, hospedado pela SonarSource.
2. **SonarQube self-hosted** — instância gerenciada pelo instrutor numa VM Azure.

## Decisão

**Self-hosted** (VM `srv-sonar-01` / `20.206.111.75`), com SonarQube Community
Build (latest) + PostgreSQL local na mesma VM.

## Motivações

- **Controle total**: instrutor escolhe regras, perfis, quality gates,
  permissões. SonarCloud limita customização.
- **Aprendizado de infra**: alunos veem na aula que o Sonar é só um
  serviço — não mágica. Onde mora, como se autentica, como escalar.
- **Sem rate limit gratuito**: SonarCloud free tem limites de análises por
  dia em repos privados. Self-hosted não tem.
- **Custo zero adicional**: instrutor já tem VM Azure pra outros projetos.
- **Pedagogia da Aula 10**: gate obrigatório atravessando rede privada vs.
  SaaS reforça a discussão sobre dependências externas em pipelines.

## Riscos conhecidos

- **VM cai durante aula**: pipeline trava no step `sonar-scan`. Mitigação:
  ADR cita SonarCloud como plano B; alunos podem trocar `SONAR_HOST_URL`
  pra `sonarcloud.io` se a VM falhar.
- **Backup e upgrade**: instrutor responsável por manter. Mitigação:
  documentação em README + snapshots de VM Azure.
- **Custo Azure**: ~$50/mês com a VM. Pequeno para o valor do demo.

## Consequências

**Positivas:**
- Customização total do Quality Gate (Sonar Way default, mas instrutor pode
  ajustar regras pra firmware embarcado).
- Material didático rico (instrutor mostra a UI completa, projetos, regras).

**Negativas:**
- Instrutor é SPOF da disponibilidade do Sonar.
- Setup inicial mais pesado (1h pra provisionar + configurar).

## ADRs relacionadas

- ADR-005 (thresholds dos quality gates) — Sonar é uma das fontes de gates.

## Setup hoje

- **URL**: `http://20.206.111.75:9000`
- **Projeto**: `inteli-px4-cicd-demo` (visibility: public)
- **Credenciais aluno**: arquivo local do instrutor (não versionado)
- **Credenciais admin**: arquivo local do instrutor + persistido em
  `/home/azureuser/sonar-secrets/admin.env` na VM (modo 600)
- **Token de análise**: secret `SONAR_TOKEN` no GitHub repo
