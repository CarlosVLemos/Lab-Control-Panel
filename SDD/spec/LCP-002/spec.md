# LCP-002 — Persistência PostgreSQL e migrações

**Status:** draft
**Risco:** CRITICAL
**Issue:** https://github.com/CarlosVLemos/Lab-Control-Panel/issues/2
**Branch:** `feat/lcp-002-postgresql-persistence`
**Owner:** Jarvis (coordenação) · Maquiavel (implementação) · Mefisto (QA)
**Modo:** SINGLE_WRITER
**Aprovação humana:** PENDING
**Contrato:** `contract.md` — DRAFT v2 (não FROZEN)

## Objetivo

Persistir as entidades da LCP-001 em PostgreSQL com Alembic, manter integridade de projeto/dataset/candidato/experimento, registrar proveniência e garantir execução/decisão recuperáveis após reconexão. Domínio Pydantic independente de SQLAlchemy/FastAPI.

## Dependências e gates

1. **Dependência atendida:** PR #26 / LCP-001 foi integrado à `main` (commit `770ade0`), e a branch foi sincronizada. Verificar novamente os modelos de `backend/app/domain/` antes de implementar.
2. Revisar `contract.md` v2, `tasks.md` e `tests.md`. O contrato define explicitamente FKs compostas, inscrição do baseline, status/timestamps, hashes canônicos, Decimal, append-only e referências auditáveis.
3. Aprovação humana **explícita** da v2, após validar dependências: Jarvis registra a referência em `contract.md`, marca `FROZEN` e atualiza `SDD/index.md`.
4. Somente então liberar Maquiavel para T-01..T-04; Mefisto valida o diff e o banco de teste reais; humano aprova o merge.

O Codex **não deve implementar enquanto DRAFT/PENDING**, nem criar banco/migração/serviço por conta própria nesta fase.

## Entregas

- SQLAlchemy 2 e Alembic, modelos/migração PostgreSQL, repositórios/UoW transacionais.
- FKs compostas/constraints/triggers e integridade auditável sem supor que JSONB ou Pydantic `frozen` bastem.
- Snapshots de DatasetVersion, CandidateVersion e PolicyVersion append-only; verificações de fingerprint da LCP-001; ordem estável de cases/IDs.
- Transições CAS de runs; avaliação e decisão persistidas com vínculos e contexto do projeto.
- Compose dev com PostgreSQL persistente, CI com testes PostgreSQL reais.
- Evidência de DB-01..DB-19 e relatório de Mefisto.

## Não fazer

Worker RQ/Redis, avaliações de agentes, LLM-as-judge, frontend, APIs novas, deploy, autorização de produção, execução de código gerado por modelos, migrações com dados reais, merge automático ou alteração de `README.md`.

## Aceite

- Alembic sobe banco vazio e é idempotente; dados sobrevivem à reconexão e ao restart seguro.
- Constraints rejeitam identidades inválidas, órfãos, candidatos/cases fora do experimento, baseline ausente e PASS indevido.
- Custos e métricas mantêm `Decimal` exato; fingerprint e ordem são reproduzidos.
- Repositório/trigger protegem imutabilidade; status de run tem transições e concorrência corretas.
- CI com PostgreSQL real passa e API `/health` continua válida.
- Mefisto apresenta evidências, limites e riscos; sem promover evidência não verificável como segura.

## Riscos reconhecidos

- Mais FKs compostas e triggers tornam a migração inicial mais trabalhosa; o benefício é rejeitar operações inválidas até quando SQL direto tenta escapar de checagens da aplicação.
- `policy_versions` é um registro mínimo de referência, não o Policy Engine completo.
- `evidence_refs` ainda são opacas, sem storage/FK de artefato; o sistema de release futuro não pode inferir que o artefato existe.
- Fingerprint não equivale a assinatura; papel administrativo do PostgreSQL pode alterar triggers.
- Se algum detalhe da LCP-001 integrada divergir do contrato v2, permanecer em DRAFT e solicitar Change Request antes de programar.
