# Arquitetura — estado atual e visão futura

## Implementado na main (14/11/2026)
- Vue 3 / TypeScript / Vite: demonstração Response e visualização estática do CODE-001.
- FastAPI: `GET /health`, `POST /api/demo/experiments` e `GET /api/demo/experiments/{id}`.
- PostgreSQL 16 e Alembic: sete tabelas, usadas pelo fluxo Response sintético.
- Módulos offline CODE-001/RAG-001, e piloto RAG remoto offline-first. Não houve piloto pago real.

```text
[Vue dashboard] → [FastAPI demo] → [PostgreSQL]
       └───── [CODE-001 fixture estática]
[CLI CODE-001] → artefatos locais
[CLI RAG-001] → offline / remoto opt-in (não executado remotamente)
```

## Próximo recorte aprovado (decisão de produto, implementação pendente)
**LCP-OBS-001**: `arquivo local → parser seguro → eventos normalizados → métricas → timeline/gráfico/replay Vue`. Sem upload, endpoint novo, tabela nova ou execução de trace. Ver [ADR-004](architecture/ADR-004-import-first-agent-observability.md).

## Visão histórica fora do MVP
O diagrama original inclui worker Redis/RQ, Workloads Response/Task/Code, Evaluation Engine, Policy Engine, Code Gate e Release Controller. **Essas peças não estão implementadas como pipeline integral.** Não usar o diagrama como evidência de capacidades existentes. OpenTelemetry completo, Langfuse, Kubernetes, canary e produção são possibilidades futuras, não dependências para LCP-OBS-001.
