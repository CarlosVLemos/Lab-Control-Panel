# LCP Kanban — auditoria de rastreabilidade em 2026-11-15

**Papel:** Mefisto, auditor técnico independente
**Repositório:** [`CarlosVLemos/Lab-Control-Panel`](https://github.com/CarlosVLemos/Lab-Control-Panel)
**GitHub Project:** [Project #5 — Lab Control Panel](https://github.com/users/CarlosVLemos/projects/5)
**Referência auditada:** [`origin/main` em `9b09e694b5a9e61a3dff67a89cfab8fffa281af5`](https://github.com/CarlosVLemos/Lab-Control-Panel/tree/9b09e694b5a9e61a3dff67a89cfab8fffa281af5)
**CI de referência:** [GitHub Actions run 43766631648](https://github.com/CarlosVLemos/Lab-Control-Panel/actions/runs/43766631648), `completed/success` no mesmo SHA.

> **Nota pós-auditoria — 2026-11-15:** a primeira rodada de saneamento criou o Status `Canceled` e moveu exclusivamente #3, #8, #11, #13, #14, #18, #20, #21, #22, #23, #24 e #25. As divergências documentais listadas na seção 6 motivaram e foram corrigidas na branch documental desta rodada, com o histórico preservado.

## 1. Resumo executivo

Foram examinadas as **36 issues** existentes no repositório: os **25 cartões** atuais do Project #5 e as **11 issues ausentes do quadro**. Também foram inspecionados código, testes versionados, documentação, SDD, PRs integradas e resultados disponíveis do GitHub Actions.

| Classificação técnica | Total |
| --- | ---: |
| `IMPLEMENTED` | 14 |
| `PARTIALLY_IMPLEMENTED` | 6 |
| `NOT_IMPLEMENTED` | 0 |
| `SUPERSEDED` | 4 |
| `CANCELED` | 12 |
| `UNVERIFIED` | 0 |
| **Total** | **36** |

O denominador de escopo não cancelado é **24 issues**: 14 implementadas, 6 parcialmente implementadas e 4 substituídas. Não é apresentada porcentagem única de “conclusão”, porque uma issue substituída pode atender parte da necessidade original sem cumprir os critérios originais, e uma issue cancelada não deve ser contada como entrega.

O MVP efetivo é tecnicamente defensável como um **laboratório experimental local** com: contratos de domínio; persistência PostgreSQL; comparação Response sintética; importadores e visualizações de evidências CODE/SWE-bench/AgentTrace; fundação RAG offline; adaptador remoto protegido e não executado; e CI cobrindo backend, frontend, Compose e Playwright. Ele **não** é a plataforma original completa de execução, policy/release gate, canary/rollback, runner seguro de código, OpenTelemetry nativo ou serviço multi-tenant.

## 2. Metodologia e critérios

1. `origin/main` foi atualizado antes da inspeção. Nenhum teste foi executado localmente nesta auditoria; resultados são atribuídos à CI ou aos registros históricos que os produziram.
2. O fechamento de uma issue e o merge de uma PR foram tratados como metadados, não como prova automática de aceite.
3. Código existente foi separado de: código coberto por testes versionados; testes comprovadamente executados pela CI; dados externos importados; e execução real da funcionalidade descrita.
4. As 36 issues não possuem comentários próprios; decisões e evidências complementares foram encontradas nos corpos das issues, PRs, SDD e documentos de validação.
5. Classificações:
   - `IMPLEMENTED`: critérios relevantes comprovados na `main`.
   - `PARTIALLY_IMPLEMENTED`: entrega objetiva, mas critérios originais pendentes.
   - `NOT_IMPLEMENTED`: escopo vigente sem entrega e sem decisão de cancelamento/substituição.
   - `SUPERSEDED`: solução original trocada por outra arquitetura; o atendimento da necessidade é explicitado.
   - `CANCELED`: descarte deliberado, sem obrigação no MVP congelado.
   - `UNVERIFIED`: evidência insuficiente para decidir.

## 3. Matriz completa de rastreabilidade

| Issue | Tarefa | Status GitHub | Status Kanban | Classificação técnica | Critérios atendidos | Critérios pendentes | Evidências |
| --- | --- | --- | --- | --- | --- | --- | --- |
| [#1](https://github.com/CarlosVLemos/Lab-Control-Panel/issues/1) | Contratos de domínio e ADRs | Closed/completed | Done | `IMPLEMENTED` | Entidades, invariantes, estados e ADRs | Nenhum do aceite da issue | `backend/app/domain/models.py`; `backend/tests/test_domain_contracts.py`; ADR-001/002/003; [PR #26](https://github.com/CarlosVLemos/Lab-Control-Panel/pull/26) |
| [#2](https://github.com/CarlosVLemos/Lab-Control-Panel/issues/2) | PostgreSQL e migrações | Closed/completed | Done | `IMPLEMENTED` | Sete tabelas, Alembic, snapshots, transações, CAS, Compose/CI | Limitações aceitas do contrato não são bloqueantes | `backend/alembic/versions/0001_initial_persistence.py`; `backend/app/repositories/persistence.py`; `backend/tests/test_postgresql_persistence.py`; `SDD/spec/LCP-002/`; [PR #31](https://github.com/CarlosVLemos/Lab-Control-Panel/pull/31) |
| [#3](https://github.com/CarlosVLemos/Lab-Control-Panel/issues/3) | Worker RQ/filas | Closed/not planned | Ready | `CANCELED` | Fluxo síncrono funciona sem fila | Worker, RQ, jobs e retries não existem | Nota de descontinuação na issue; `docs/ARCHITECTURE.md`; ausência de Redis/RQ na `main` |
| [#4](https://github.com/CarlosVLemos/Lab-Control-Panel/issues/4) | Datasets versionados | Closed/completed | Done | `IMPLEMENTED` | Casos, versão, hash determinístico e snapshots | Nenhum do recorte aprovado | `DatasetVersion`; `content_fingerprint`; testes de domínio/persistência; PRs [#26](https://github.com/CarlosVLemos/Lab-Control-Panel/pull/26)/[#31](https://github.com/CarlosVLemos/Lab-Control-Panel/pull/31) |
| [#5](https://github.com/CarlosVLemos/Lab-Control-Panel/issues/5) | Candidatos e fingerprints | Closed/completed | Done | `IMPLEMENTED` | Modelo/config/Spec/commit, fingerprint e referência por runs | Nenhum do recorte aprovado | `CandidateVersion`; `ExecutionRun.candidate_id`; testes de domínio/persistência; PRs #26/#31 |
| [#6](https://github.com/CarlosVLemos/Lab-Control-Panel/issues/6) | Adapter Response mock + LLM | Closed/not planned | Backlog | `PARTIALLY_IMPLEMENTED` | Mock determinístico, falha explícita e resultados por caso | Adapter LLM, tokens/latência/provider reais | `backend/app/workloads/response.py`; `backend/app/evaluation/response.py`; `test_mvp_response_core.py`; [PR #35](https://github.com/CarlosVLemos/Lab-Control-Panel/pull/35) |
| [#7](https://github.com/CarlosVLemos/Lab-Control-Panel/issues/7) | Avaliador Response | Closed/completed | Done | `IMPLEMENTED` | Ground truth, métricas por caso e fail-closed | Nenhum no escopo sintético declarado | `evaluate_exact_label`, `build_response_report`; `test_adapter_errors_and_missing_outputs_fail_closed`; PRs #35/[#37](https://github.com/CarlosVLemos/Lab-Control-Panel/pull/37) |
| [#8](https://github.com/CarlosVLemos/Lab-Control-Panel/issues/8) | Policy Engine | Closed/not planned | Backlog | `CANCELED` | Somente contratos `Verdict`/`PolicyDecision` | Engine, políticas versionadas e promoção | Issue e `PROJECT_SPEC.md` registram retirada; `docs/ARCHITECTURE.md` confirma ausência |
| [#9](https://github.com/CarlosVLemos/Lab-Control-Panel/issues/9) | Experiment Lab | Closed/not planned | Backlog | `PARTIALLY_IMPLEMENTED` | Mesmo dataset, baseline/candidato e qualidade por caso | Tempo/custo real, múltiplas execuções e inferência experimental | Demo Response em `demo_experiments.py`; Vue; PR #37 |
| [#10](https://github.com/CarlosVLemos/Lab-Control-Panel/issues/10) | Eventos/artefatos/redaction | Closed/not planned | Backlog | `SUPERSEDED` | Inspeção de evidências importadas e sanitização específica | Instrumentação automática genérica, comandos/timestamps/redaction de runs do LCP | ADR-004; `observation*.ts`; [PR #51](https://github.com/CarlosVLemos/Lab-Control-Panel/pull/51). Necessidade de inspeção atendida parcialmente, captura original abandonada |
| [#11](https://github.com/CarlosVLemos/Lab-Control-Panel/issues/11) | Code runner com allowlist | Closed/not planned | Backlog | `CANCELED` | Nenhum runner; importadores deliberadamente não executam conteúdo | Todo o aceite original | Issue; ADR-003 histórico; `code_artifacts.py` é import-only |
| [#12](https://github.com/CarlosVLemos/Lab-Control-Panel/issues/12) | Avaliadores Code | Closed/not planned | Backlog | `SUPERSEDED` | Importa JUnit/diff, compara identidades e falha fechado | Reexecução pytest, runner e avaliação automática de segurança | `backend/app/evaluation/code_artifacts.py`; `test_code_artifacts.py`; [PR #39](https://github.com/CarlosVLemos/Lab-Control-Panel/pull/39). Comparação preservada; execução abandonada |
| [#13](https://github.com/CarlosVLemos/Lab-Control-Panel/issues/13) | Release Controller | Closed/not planned | Backlog | `CANCELED` | Apenas modelos de decisão genéricos | State machine e audit trail de release | Issue; `docs/ARCHITECTURE.md`; ausência de controller |
| [#14](https://github.com/CarlosVLemos/Lab-Control-Panel/issues/14) | Canary/rollback lógico | Closed/not planned | Backlog | `CANCELED` | Nenhum | Roteamento, canary, abort e rollback | Issue; ausência de implementação; laboratório kind não é equivalente |
| [#15](https://github.com/CarlosVLemos/Lab-Control-Panel/issues/15) | Dashboard runs/release | Closed/not planned | Backlog | `SUPERSEDED` | Comparações, evidências, traces e estados de UI | Release/canary/rollback | `App.vue`; componentes Experiment/CODE/Observability; PRs #37/#42/#51. Dashboard original foi trocado por laboratório de análise |
| [#16](https://github.com/CarlosVLemos/Lab-Control-Panel/issues/16) | CI, Compose e E2E | Closed/not planned | Backlog | `PARTIALLY_IMPLEMENTED` | Compose, pytest/PostgreSQL, Vitest/build, Playwright e restart/persistência | E2E de rollback lógico inexistente | `.github/workflows/ci.yml`; `docker-compose.yml`; `frontend/e2e/demo.spec.ts`; CI 43766631648 |
| [#17](https://github.com/CarlosVLemos/Lab-Control-Panel/issues/17) | Demo/README/portfólio | Closed/not planned | Backlog | `PARTIALLY_IMPLEMENTED` | README reproduzível e limites sintético/importado explícitos | Vídeo e demonstração de canary/rollback; relatório externo de portfólio | `README.md`; [PR #54](https://github.com/CarlosVLemos/Lab-Control-Panel/pull/54) |
| [#18](https://github.com/CarlosVLemos/Lab-Control-Panel/issues/18) | Adapter Task | Closed/not planned | Backlog | `CANCELED` | Nenhum adapter de ferramentas | Estado inicial/final, efeitos e idempotência | Issue; README declara análise, não execução autônoma |
| [#19](https://github.com/CarlosVLemos/Lab-Control-Panel/issues/19) | OpenTelemetry/traces | Closed/not planned | Backlog | `SUPERSEDED` | Importação AgentTrace, métricas, filtros e replay local | Instrumentação nativa OTel, vínculo run/trace e APM | ADR-004; `frontend/src/domain/observation*.ts`; `ObservabilityView.vue`; PR #51. Necessidade de observação atendida por importação |
| [#20](https://github.com/CarlosVLemos/Lab-Control-Panel/issues/20) | Repetições estatísticas | Closed/not planned | Backlog | `CANCELED` | Nenhum protocolo estatístico executado | Repetições, distribuição e intervalos | Issue; resultados atuais explicitamente não inferem causalidade |
| [#21](https://github.com/CarlosVLemos/Lab-Control-Panel/issues/21) | LLM-as-judge | Closed/not planned | Backlog | `CANCELED` | Nenhum | Juiz versionado/calibrado | Issue; avaliações atuais são determinísticas |
| [#22](https://github.com/CarlosVLemos/Lab-Control-Panel/issues/22) | GitHub Code Gate | Closed/not planned | Backlog | `CANCELED` | CI normal, sem gate de produto | Checks de PolicyDecision e publicação no PR | Issue; `.github/workflows/ci.yml` não implementa Code Gate |
| [#23](https://github.com/CarlosVLemos/Lab-Control-Panel/issues/23) | Threat model do runner | Closed/not planned | Backlog | `CANCELED` | Limites históricos em ADR-003 | Threat model e testes de isolamento concretos | Cancelado junto com #11; ADR não prova hardening implementado |
| [#24](https://github.com/CarlosVLemos/Lab-Control-Panel/issues/24) | Kubernetes + Argo Rollouts | Closed/not planned | Backlog | `CANCELED` | Existe laboratório frontend kind/Kustomize separado | Policy integration, Argo, rollout e rollback | `k8s/kind/`; [PR #55](https://github.com/CarlosVLemos/Lab-Control-Panel/pull/55). Não equivale ao aceite da issue |
| [#25](https://github.com/CarlosVLemos/Lab-Control-Panel/issues/25) | Auth/RBAC/quotas | Closed/not planned | Backlog | `CANCELED` | Nenhum | Todo o aceite original | Issue; README/Compose são locais e sem autenticação |
| [#27](https://github.com/CarlosVLemos/Lab-Control-Panel/issues/27) | Governança SDD/agentes | Closed/completed | Ausente | `IMPLEMENTED` | Fonte normativa, perfis, templates e testes de integridade | Nenhum do aceite | `AGENTS.md`; `SDD/rules.md`; `.codex/agents/`; `.github/agents/`; `test_agent_governance.py`; [PR #28](https://github.com/CarlosVLemos/Lab-Control-Panel/pull/28) |
| [#29](https://github.com/CarlosVLemos/Lab-Control-Panel/issues/29) | Workflow de coding agents | Closed/completed | Ausente | `IMPLEMENTED` | Trilhas de risco, skills, gates, template e testes | Piloto futuro não é requisito funcional da main | `.agents/skills/`; `.github/pull_request_template.md`; `test_ai_coding_workflow.py`; [PR #30](https://github.com/CarlosVLemos/Lab-Control-Panel/pull/30) |
| [#32](https://github.com/CarlosVLemos/Lab-Control-Panel/issues/32) | Interface Vue Response | Closed/completed | Ausente | `IMPLEMENTED` | Vue/TS, estados, fonte substituível, testes/build; depois integrada à API | Nenhum do escopo original da UI | `App.vue` (classificação sintética); `ExperimentComparisonView.vue` (SWE-bench); `report-source.ts`; testes frontend; [PR #34](https://github.com/CarlosVLemos/Lab-Control-Panel/pull/34) e #37 |
| [#33](https://github.com/CarlosVLemos/Lab-Control-Panel/issues/33) | Núcleo Response | Closed/completed | Ausente | `IMPLEMENTED` | Seis casos, dois classificadores, determinismo, schema e falha fechada | Nenhum | `response_fixture.py`; `response.py`; `test_mvp_response_core.py`; PR #35 |
| [#36](https://github.com/CarlosVLemos/Lab-Control-Panel/issues/36) | Demo integrada | Closed/completed | Ausente | `IMPLEMENTED` | Vue→API→PostgreSQL, restart/persistência, erro sem fallback, CI/E2E | Não é produção; corrida inicial pode responder 409, risco aceito | `demo_experiments.py`; `api/demo.py`; Compose; CI; PR #37 |
| [#38](https://github.com/CarlosVLemos/Lab-Control-Panel/issues/38) | Real Evaluation v1a | Closed/completed | Ausente | `IMPLEMENTED` | Importador offline, JUnit/diff/hash, comparabilidade e UI | Não reexecuta JUnit nem atesta origem; isso é limite declarado, não critério omitido | `code_artifacts.py`; testes; `code-001-import.json`; PRs #39/[#42](https://github.com/CarlosVLemos/Lab-Control-Panel/pull/42) |
| [#40](https://github.com/CarlosVLemos/Lab-Control-Panel/issues/40) | Experimento agente com/sem Spec | Open | Ausente | `PARTIALLY_IMPLEMENTED` | Protocolo, fixture e preparação; existe comparação CODE-001 importada | Dois braços comprovados com mesmo agente/modelo/base e condições; telemetria e execução independente | [PR #41](https://github.com/CarlosVLemos/Lab-Control-Panel/pull/41) declara preparação/BLOCKED; `code-001-import.json` registra identidade do agente/modelo como desconhecida |
| [#43](https://github.com/CarlosVLemos/Lab-Control-Panel/issues/43) | Experimento RAG real | Open | Ausente | `PARTIALLY_IMPLEMENTED` | Corpus 12 docs, 36 casos, avaliação offline, runner e controles | Piloto pago 12/216 chamadas, resultados, telemetria real e revisão humana | `rag.py`; `rag_remote.py`; testes offline; docs/evidence; PRs [#44](https://github.com/CarlosVLemos/Lab-Control-Panel/pull/44)/[#47](https://github.com/CarlosVLemos/Lab-Control-Panel/pull/47); execução real `NOT_RUN` |
| [#45](https://github.com/CarlosVLemos/Lab-Control-Panel/issues/45) | Adapter remoto controlado | Closed/completed | Ausente | `IMPLEMENTED` | Contrato FROZEN, dry-run default, cliente injetável, budget/quota, artefatos e testes offline | Piloto real pertence a #43 e foi expressamente excluído | `SDD/spec/RAG-001-REMOTE/`; `rag_remote.py`; `test_rag_remote.py`; PRs [#46](https://github.com/CarlosVLemos/Lab-Control-Panel/pull/46)/#47 |
| [#49](https://github.com/CarlosVLemos/Lab-Control-Panel/issues/49) | Importador SWE-bench | Closed/completed | Ausente | `IMPLEMENTED` | Par mesma issue, modelos distintos, hashes, resultado atribuído à fonte e falhas negativas | Autenticidade da origem não é atestada, por desenho | `swebench_verified.py`; `test_swebench_verified_import.py`; `docs/EXP-001.md`; [PR #50](https://github.com/CarlosVLemos/Lab-Control-Panel/pull/50) |
| [#52](https://github.com/CarlosVLemos/Lab-Control-Panel/issues/52) | Dependências frontend | Closed/completed | Ausente | `IMPLEMENTED` | Upgrades deliberados, lockfile, audit reportado 0/0, Vitest/build/Playwright CI | Monitorar política de postinstall do esbuild | `frontend/package*.json`; workflow CI; [PR #53](https://github.com/CarlosVLemos/Lab-Control-Panel/pull/53); Actions 43647423234 |

## 4. Evidências por área

### 4.1 Contratos, persistência e concorrência

- `backend/app/domain/models.py` implementa contratos congelados, transições de run, fingerprints e regras fail-closed.
- `backend/app/db/schema.py` e a migração Alembic definem sete tabelas. `Repositories.transition_run` usa revisão esperada/compare-and-swap; `test_concurrent_compare_and_swap` cobre conflito concorrente.
- `backend/tests/test_postgresql_persistence.py` depende de PostgreSQL real. A CI provisiona PostgreSQL 16, executa pytest, migração, POST, restart da API e GET byte a byte.
- Limite: a concorrência da primeira criação da demo pode produzir `409` explícito; não há job queue.

### 4.2 Response e demo

- A implementação executa seis casos sintéticos, com baseline 2/6 e candidato 6/6; não há LLM.
- Falha de adapter produz saída indisponível e `passed=false`; a UI não substitui erro HTTP por fixture, salvo modo offline explicitamente configurado.
- [PR #37](https://github.com/CarlosVLemos/Lab-Control-Panel/pull/37) registra 44 testes backend, frontend/build, smoke Compose e dois E2E no SHA da entrega; a CI atual repete as categorias de verificação.

### 4.3 CODE-001

- `code_artifacts.py` lê manifestos/JUnit/diffs locais e rejeita XML perigoso, path traversal, symlink e evidência incompatível; não executa o patch ou os testes importados.
- `code-001-import.json` é evidência externa: ambos os braços reportam 9/9, mas agente/modelo, tokens, custo e duração são desconhecidos. `COMPARABLE` significa compatibilidade estrutural, não vencedor.
- A preparação da #40 foi integrada, mas a própria [PR #41](https://github.com/CarlosVLemos/Lab-Control-Panel/pull/41) registra que nenhum par de agentes foi executado naquele protocolo.

### 4.4 SWE-bench e AgentTrace

- O importador SWE-bench e seus testes são código validado; os resultados e custos exibidos são declarações da fonte externa.
- As duas trajetórias incorporadas têm `resolved=true`, mas `submission` vazio; nenhum patch é reconstruído.
- A UI AgentTrace analisa 12 traces externos, com métricas, filtros, spans e diagnósticos determinísticos. Hashes provam integridade dos bytes locais, não autoria/autenticidade; a revisão exata do dataset AgentTrace não foi registrada.
- A [PR #51](https://github.com/CarlosVLemos/Lab-Control-Panel/pull/51) registra CI com Vitest/build e Playwright 6/6; isso valida o software de importação/apresentação, não as execuções externas.

### 4.5 RAG offline e remoto

- `rag.py` contém 12 políticas fictícias e 36 casos; testes cobrem retrieval/evaluation determinísticos com fakes. Correção semântica de texto gerado permanece `NOT_EVALUATED`.
- `rag_remote.py` implementa dry-run sem rede, integridade, limite de chamadas, orçamento conservador, snapshot de preço e relatórios; testes usam fakes.
- Nenhuma chamada real de embeddings/generation, disponibilidade de modelo, tarifa efetiva ou resultado do piloto foi comprovada. A barreira de software da #45 está entregue; o experimento da #43 permanece parcial.

### 4.6 Segurança, governança, CI/CD e infraestrutura

- SDD, perfis, skills e testes estruturais de governança existem e são executados pela suíte backend.
- A CI atual executa pytest/PostgreSQL, Compose/restart, Playwright, Vitest e build. Ela não implementa Policy Engine, Code Gate ou deploy.
- A PR #53 registra `npm audit` e `npm audit --omit=dev` com zero vulnerabilidades naquele lockfile, além de CI verde. Esta auditoria não reexecutou `npm audit`.
- O laboratório kind/Kustomize serve somente o frontend estático offline. Não contém Argo Rollouts, backend, TLS, autoscaling ou policy integration.

## 5. Lacunas técnicas e sobreposições

### Requisitos integralmente atendidos

Contratos/ADRs (#1), persistência (#2), datasets/candidatos (#4/#5), avaliador Response (#7), governança (#27/#29), UI/núcleo/demo (#32/#33/#36), importador CODE (#38), adapter RAG protegido (#45), SWE-bench (#49) e dependências frontend (#52).

### Requisitos parciais

- #6: mock sim, LLM/telemetria não.
- #9: comparação sintética sim, medições reais/repetições não.
- #16: CI/Compose/E2E sim, rollback lógico não.
- #17: README/demo sim, vídeo canary/rollback não.
- #40: preparação e fixture sim, experimento controlado comprovado não.
- #43: infraestrutura offline/remota sim, piloto real não.

### Funcionalidades existentes fora do Kanban

- Nove issues concluídas ausentes: #27, #29, #32, #33, #36, #38, #45, #49 e #52.
- Duas issues abertas/futuras ausentes: #40 e #43.
- EXP-002/OBS-002 (PR #51) e o laboratório kind (PR #55) não têm cartões próprios; não devem ser atribuídos retroativamente a #19 ou #24 como cumprimento integral.

### Duplicação/sobreposição

- #1/#2/#4/#5 compartilham modelos e persistência, mas têm aceites distinguíveis.
- #6/#7/#9/#33/#36 representam camadas do mesmo fluxo Response.
- #10/#12/#19/#38 e PR #51 convergem em evidência importada; diferem de captura/execução nativa.
- #11/#12/#23 formavam o runner Code e sua segurança; foram substituídos parcialmente pelo desenho import-only.
- #13–#17 misturam release, UI e entrega; somente UI/CI/README sobreviveram.
- #43 é o experimento pago; #45 é apenas o adapter/control plane anterior ao piloto.

### Testes sem execução real da capacidade externa

- CODE-001: parser/UI testados; JUnit externo não reexecutado pelo LCP.
- SWE-bench/AgentTrace: importação/UI testadas; trajetórias/traces não foram produzidos pelo LCP.
- RAG remoto: controles offline testados; provider/modelo/preço/piloto não executados.
- OTel, worker, runner Code, policy/release e canary não têm implementação a testar.

## 6. Divergências documentais

1. `SDD/index.md` afirma que a PR #41 está aberta; ela foi integrada no commit `ba63ee6`.
2. O mesmo índice descreve RAG runtime em branch separada/sem merge, embora PRs #46/#47 estejam na `main`.
3. `SDD/spec/RAG-001-REMOTE/tests.md` ainda diz “runtime não implementado / NOT_RUN”; código/testes offline e CI existem. Apenas a execução paga permanece `NOT_RUN`.
4. `docs/evidence/rag-001-remote-runner.md` chama a PR #47 de “not merged”; está integrada.
5. `SDD/index.md` e `docs/ARCHITECTURE.md` tratam LCP-OBS-001 Etapa D como pendente, mas a UI de observabilidade e PR #51 estão na `main`.
6. ADR-001 ainda decide por worker separado e Redis/RQ; #3 foi cancelada e o MVP atual é síncrono.
7. ADR-003 descreve um runner controlado como decisão do MVP; #11/#23 foram canceladas e o produto adotou import-only.
8. `PROJECT_SPEC.md` preserva corretamente a visão original, mas seus critérios não devem ser apresentados como cobertura efetiva do MVP reduzido.

## 7. Recomendações para reorganização do Kanban

Nenhum cartão foi alterado nesta auditoria.

1. **Permanecer em Done:** #1, #2, #4, #5 e #7.
2. **Adicionar como Done, se o quadro representar o estado completo:** #27, #29, #32, #33, #36, #38, #45, #49 e #52.
3. **Criar uma opção explícita Canceled e mover:** #3, #8, #11, #13, #14, #18, #20, #21, #22, #23, #24 e #25.
4. **Representar como Partial/Reduced scope, não Done integral:** #6, #9, #16 e #17.
5. **Representar como Superseded:** #10, #12, #15 e #19, vinculando ADR-004/PRs substitutas e declarando quais objetivos originais foram abandonados.
6. **Adicionar ao Backlog/Future:** #40 e #43, ambas P2; não fechá-las com base na preparação existente.
7. **Criar cartões próprios somente se houver valor de governança:** EXP-002/OBS-002 e laboratório kind. Não usar #19/#24 como substitutos integrais.
8. Atualizar `SDD/index.md`, `docs/ARCHITECTURE.md`, `docs/evidence/rag-001-remote-runner.md` e os estados históricos de testes RAG/OBS, preservando datas e distinguindo histórico de estado atual.

## 8. Conclusão sobre a cobertura efetiva do MVP

O LCP entregue é menor e mais seguro que a visão inicial: removeu execução de código/agents, filas, release automation e produção multi-tenant; em troca, consolidou um laboratório verificável de avaliação sintética e análise de evidências importadas. Essa simplificação preserva o valor de portfólio em contratos, persistência, fail-closed, rastreabilidade e apresentação honesta de dados, mas **não preserva** o objetivo original de executar workloads variados e controlar releases progressivos.

Das 24 issues não canceladas, 14 estão integralmente implementadas, 6 estão parciais e 4 foram substituídas por soluções import-first. As 12 restantes foram deliberadamente canceladas. O posicionamento tecnicamente defensável é: **plataforma experimental local de comparação e observabilidade por evidências**, não sistema de orquestração, avaliação e release de agentes em produção.
