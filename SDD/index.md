# SDD — Spec Index

| ID | Title | State | Issue | Contract | Review |
| --- | --- | --- | --- | --- | --- |
| LCP-002 | Persistência PostgreSQL e migrações | `done` — PR #31 merged; Issue #2 closed | [#2](https://github.com/CarlosVLemos/Lab-Control-Panel/issues/2) | [FROZEN MVP v4](spec/LCP-002/contract.md) · [CR-001](spec/LCP-002/CHANGE_REQUEST-001.md) | [Evidências](spec/LCP-002/validation-result.md) · [Revisão](spec/LCP-002/review.md) |

| RAG-001-REMOTE | Adaptador remoto com custo controlado | `done` — contrato e runtime offline-first integrados pelas PRs #46/#47; piloto pago NOT_RUN | [#45](https://github.com/CarlosVLemos/Lab-Control-Panel/issues/45) | [FROZEN MVP v2](spec/RAG-001-REMOTE/contract.md) | [Testes e limites](spec/RAG-001-REMOTE/tests.md) |

## Registro histórico — decisões anteriores à integração final

Na posição registrada em 13/11/2026, o contrato LCP-002 MVP v4 estava FROZEN, a PR #31 integrada e a issue #2 fechada. Para RAG-001-REMOTE, o contrato MVP v2 havia sido congelado por decisão humana na PR #46 (comentário #6853766192), com implementação Python offline autorizada em branch separada; chamadas pagas e merge ainda não estavam autorizados naquele momento.

## Novo marco — OBS

| ID | Título | Estado | Decisão | Contrato e testes |
| --- | --- | --- | --- | --- |
| LCP-OBS-001 | Importação e observabilidade de execução agêntica | **Integrada à `main`** — parser, AgentTrace, métricas e UI; PR #51 validada por CI | [ADR-004](../docs/architecture/ADR-004-import-first-agent-observability.md) | [Spec](spec/LCP-OBS-001/spec.md) · [Contrato v1 + CR-002](spec/LCP-OBS-001/contract.md) · [Aprovações](spec/LCP-OBS-001/APPROVALS_2026-11-14.md) · [CR-002](spec/LCP-OBS-001/CHANGE_REQUEST-002.md) · [Tarefa Codex B](spec/LCP-OBS-001/CODEX_TASK_B.md) · [Contrato C histórico](spec/LCP-OBS-001/METRICS_CONTRACT_C_DRAFT.md) · [Tarefa Codex C](spec/LCP-OBS-001/CODEX_TASK_C.md) · [Proposta UI D histórica](spec/LCP-OBS-001/UI_CONTRACT_D_DRAFT.md) · [Tarefa Codex D](spec/LCP-OBS-001/CODEX_TASK_D.md) · [Etapas](spec/LCP-OBS-001/tasks.md) · [Testes](spec/LCP-OBS-001/tests.md) |

### Posição histórica em 14/11/2026 — não representa o estado atual

Naquele momento, as PRs #31, #37, #39, #42, #44, #46 e #47 já estavam integradas à `main`; a PR #41 ainda estava aberta e sem merge. A implementação do runner RAG já estava na `main`, mas **o piloto pago não havia sido executado**.

## Estado atual — 2026-11-15

- A PR #41 foi integrada à `main`; ela entrega preparação/protocolo, não comprova as duas execuções reais da issue #40.
- As PRs #46 e #47 foram integradas. O adaptador RAG remoto e seus testes offline existem; chamadas reais, disponibilidade do modelo, tarifas efetivas e piloto da issue #43 permanecem `NOT_RUN`.
- A observabilidade por importação local, incluindo a interface da Etapa D, foi integrada pela PR #51 e validada na CI. Os relatos locais e estados DRAFT/NOT_RUN acima permanecem como histórico dos gates anteriores.
- Worker RQ, runner de código, Policy Engine e Release Controller não integram o MVP final.
- A PR #55 adiciona somente um laboratório Kubernetes frontend-only com kind/Kustomize; não implementa Argo Rollouts, canary ou rollback.
