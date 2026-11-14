# Lab Control Panel — Escopo V0.1

## Objetivo

Executar workloads de IA sob condições documentadas; avaliar resultados com evidências e políticas versionadas; comparar baseline e candidato; controlar liberação progressiva de versões com rollback lógico.

## Workloads

- **Response:** avaliações de conversas, classificação, extração e RAG.
- **Task:** avaliação de execução de ferramentas e estado final; adaptador simples no MVP.
- **Code:** repositório fixture, aplicação de mudanças, comandos permitidos, testes e diff.

## Componentes

Control API, Execution Engine (worker), Evaluation Engine, Experiment Lab, Policy Engine, Release Controller, Code Gate e UI de observabilidade.

## Stack

- Backend: Python, FastAPI, Pydantic, SQLAlchemy, Alembic.
- Dados/jobs: PostgreSQL, Redis, RQ.
- Frontend: Vue 3, TypeScript, Vite.
- Testes/CI: pytest, GitHub Actions.
- Ambiente: Docker Compose; OpenTelemetry opcional no MVP.
- Futuro: Langfuse, Kubernetes, Argo Rollouts, integração GitHub Checks.

## Regras inegociáveis

1. `INCONCLUSIVE` não aprova releases.
2. Falha crítica de segurança bloqueia promoção.
3. Resultado de LLM-as-judge não substitui testes determinísticos.
4. Dataset, Spec, candidato, código, política e condições devem ter versão/fingerprint.
5. Traces registram eventos observáveis, não raciocínio privado do LLM.
6. O runner do MVP executa somente fixtures controladas, sem segredos e com comandos permitidos.
7. Rollback do MVP é lógico no roteador simulado; não reverte dados reais.

## Critérios de aceite do MVP

- Avaliar baseline e candidato no mesmo dataset de respostas.
- Capturar tokens/custo, latência e evidências por execução.
- Comparar tarefa de código com e sem Spec, registrando diff, comandos e testes.
- Gate rejeita regressão crítica e bloqueia com evidência ausente.
- Canary sintético distribui tráfego entre stable/candidate; falha provoca rollback lógico auditado.
- API, worker e dashboard são reproduzíveis; pipeline de CI executa testes.

## Fora do MVP

Agentes autônomos genéricos, execução de código de terceiros, deploy em Kubernetes, produção multi-tenant, autorização financeira e publicação automática de código.

## Recorte de portfólio aprovado em 14/11/2026 — LCP-OBS-001

O escopo V0.1 acima é um **documento de visão original**, não uma alegação de implementação de seus componentes. A prioridade corrente é **observabilidade de execuções agênticas importadas**, independente de modelo/provedor, sem executar agentes ou avaliar respostas com outro LLM.

**Fatia planejada:** upload *local no browser* de arquivo declarativo LCP Evidence v1 + um adaptador externo validado; timeline de eventos/ferramentas/erros, métricas reportadas de duração e tokens, gráfico acumulado em degraus, replay event-based e indicação de dados ausentes. Não enviar trace ao backend nem exigir PostgreSQL novo. Ver [ADR-004](architecture/ADR-004-import-first-agent-observability.md) e [Spec DRAFT](../SDD/spec/LCP-OBS-001/spec.md).

**Não incluído neste marco:** worker Redis/RQ, release gates, canary/rollback, task runner, geração por GPU, chamadas de API pagas, OTLP universal, agentes avaliadores, gravação de mouse, upload servidor e live monitoring. As funcionalidades existentes de Response e Code Evaluation continuam preservadas.

**Execução dos testes:** operador controla instalações, downloads, venv, builds e testes ao fim de cada etapa; Codex prepara código/testes e pode usar Git/GitHub CLI e shell de inspeção. Documentos de planejamento não aprovam implementação por si só.
