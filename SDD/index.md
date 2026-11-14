# SDD — Spec Index

| ID | Title | State | Issue | Contract | Review |
| --- | --- | --- | --- | --- | --- |
| LCP-002 | Persistência PostgreSQL e migrações | `done` — PR #31 merged; Issue #2 closed | [#2](https://github.com/CarlosVLemos/Lab-Control-Panel/issues/2) | [FROZEN MVP v4](spec/LCP-002/contract.md) · [CR-001](spec/LCP-002/CHANGE_REQUEST-001.md) | [Evidências](spec/LCP-002/validation-result.md) · [Revisão](spec/LCP-002/review.md) |

| RAG-001-REMOTE | Adaptador remoto com custo controlado (somente contrato) | `ready` — contrato MVP v2 FROZEN por decisão humana; runtime em branch separada | [#45](https://github.com/CarlosVLemos/Lab-Control-Panel/issues/45) | [FROZEN MVP v2](spec/RAG-001-REMOTE/contract.md) | [Plano de testes](spec/RAG-001-REMOTE/tests.md) |

Histórico LCP-002: contrato MVP v4 FROZEN, PR #31 integrada à main em 2026-11-11, Issue #2 fechada. RAG-001-REMOTE: contrato MVP v2 FROZEN por decisão humana em 2026-11-13 (PR #46, comentário #6853766192). Implementação Python offline autorizada em branch separada; nenhuma chamada paga nem merge autorizado.

## Novo marco — OBS

| ID | Título | Estado | Decisão | Contrato e testes |
| --- | --- | --- | --- | --- |
| LCP-OBS-001 | Importação e observabilidade de execução agêntica | **Etapa A testes PASS + CR-001 aprovada**, adaptador AgentTrace CR-002 FROZEN; Etapa B autorizada para desenvolvimento | [ADR-004](../docs/architecture/ADR-004-import-first-agent-observability.md) | [Spec](spec/LCP-OBS-001/spec.md) · [Contrato v1 + CR-002](spec/LCP-OBS-001/contract.md) · [Aprovações](spec/LCP-OBS-001/APPROVALS_2026-11-14.md) · [CR-002](spec/LCP-OBS-001/CHANGE_REQUEST-002.md) · [Tarefa Codex B](spec/LCP-OBS-001/CODEX_TASK_B.md) · [Etapas](spec/LCP-OBS-001/tasks.md) · [Testes NOT_RUN](spec/LCP-OBS-001/tests.md) · [Export prompt DRAFT](spec/LCP-OBS-001/LCP_EXPORT.md) |

**Nota factual de 14/11/2026:** PRs #31, #37, #39, #42, #44, #46 e #47 foram integradas à `main`. PR #41 segue aberta, sem merge. A implementação do runner RAG está na `main`; **o piloto pago não foi executado**. Texto histórico acima sobre PR #46/47 "branch separada" deve ser lido como registro do momento anterior à integração.
