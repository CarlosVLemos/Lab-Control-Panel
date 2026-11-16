# Arquitetura — estado atual e visão futura

## Implementado na main (15/11/2026)
- Vue 3 / TypeScript / Vite: demonstração Response e visualização estática do CODE-001.
- FastAPI: `GET /health`, `POST /api/demo/experiments` e `GET /api/demo/experiments/{id}`.
- PostgreSQL 16 e Alembic: sete tabelas, usadas pelo fluxo Response sintético.
- Módulos offline CODE-001/RAG-001 e adaptador RAG remoto offline-first com testes offline. Não houve piloto pago real.
- Observabilidade por importação local de LCP Evidence e AgentTrace, com métricas, timeline, filtros e replay visual.
- Laboratório Kubernetes frontend-only com kind/Kustomize; não contém backend, Argo Rollouts, canary ou rollback.

```text
[Vue dashboard] → [FastAPI demo] → [PostgreSQL]
       └───── [CODE-001 fixture estática]
[CLI CODE-001] → artefatos locais
[CLI RAG-001] → offline / remoto opt-in (não executado remotamente)
[Arquivo local AgentTrace/LCP Evidence] → [Vue observabilidade]
[kind/Kustomize] → [frontend estático offline]
```

## Estado atual — 2026-11-15

**LCP-OBS-001** foi integrado: `arquivo local → parser seguro → eventos normalizados → métricas → timeline/gráfico/replay Vue`. A implementação não faz upload, não cria endpoint/tabela e não executa o conteúdo importado. Ver [ADR-004](architecture/ADR-004-import-first-agent-observability.md) e PR #51.

O adaptador RAG remoto foi integrado pelas PRs #46/#47, mas o modo pago não foi executado. Seus testes usam clients fakes e transporte mockado; não comprovam compatibilidade, preço, entitlement ou resultados de um provider real.

## Visão histórica fora do MVP
O diagrama original inclui worker Redis/RQ, Workloads Response/Task/Code, Evaluation Engine, Policy Engine, Code Gate e Release Controller. **Worker, runner de código, Policy Engine e Release Controller não integram o MVP final.** Não usar o diagrama como evidência de capacidades existentes. OpenTelemetry nativo, Langfuse, Argo Rollouts, canary e produção são possibilidades futuras; o laboratório kind existente não implementa essas capacidades.
