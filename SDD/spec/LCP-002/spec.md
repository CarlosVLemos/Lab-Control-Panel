# LCP-002 — Persistência mínima que funciona

**Estado:** ready para implementação · **Contrato:** FROZEN MVP v4 ([CR-001](CHANGE_REQUEST-001.md))
**Branch:** `feat/lcp-002-postgresql-persistence` · **Issue:** #2
**Responsável:** Maquiavel · **Validador:** Mefisto · **Modo:** SINGLE_WRITER

Implementar a primeira camada persistente do Lab Control Panel, com 7 tabelas, Alembic, repositórios SQLAlchemy, PostgreSQL via Compose e testes reais. É a base para uma demonstração futura de comparação Response entre baseline e candidato.

O recorte completo é `contract.md`; aceitação é `tests.md`; prioridades do produto estão em `docs/MVP_DEMO_PLAN.md`. Sem triggers avançados, funções SECURITY DEFINER, Kubernetes, worker ou UI nesta Issue. A LCP-001 já está integrada.

Não realizar nova rodada de revisão teórica: **começar a implementar e deixar que testes reais mostrem os problemas**. Ajustes menores para atender ao contrato podem ser feitos no PR; mudança de risco/escopo exige CR. Sem deploy ou merge automático.
