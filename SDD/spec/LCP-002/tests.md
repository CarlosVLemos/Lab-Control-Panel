# LCP-002 — Plano de verificação independente (DRAFT v3)

**Owner:** Mefisto · **Contrato:** DRAFT v3
**Execução:** NOT_RUN — sem migrações/implementação autorizadas
**Ambiente-alvo:** PostgreSQL 16+ **real** em banco descartável, com papéis separados `lcp_app` / `lcp_aggregate_writer` / `lcp_migrator`.
**Regra:** nunca marcar PASS sem logs/comandos/commit/revisão examinados.

| ID | Verificação | Resultado exigido |
| --- | --- | --- |
| DB-01 | `alembic upgrade head` em banco PostgreSQL vazio | Esquema, funções, grants e FKs criados; revision registrada |
| DB-02 | Repetir `alembic upgrade head` | Idempotência; sem DDL no startup |
| DB-03 | Round-trip de projeto, dataset/cases, candidato e experimento, reconectando | IDs, ordem, snapshots e hashes LCP-001 preservados |
| DB-04 | Run, avaliação, PolicyVersion e decisão; fechar sessão e reconectar | Persistência real e FKs corretas |
| DB-05 | Reiniciar Compose sem `down -v` | Dados sobrevivem no volume |
| DB-06 | IDs inválidos, slug/key incorretos, versões/cases duplicados, FK órfã de projeto | PostgreSQL rejeita; rollback completo |
| DB-07 | SQL direto tenta status/verdict/workload inválidos, custo negativo/NaN/Infinity, tokens negativos, evidência `[null]`/`[""]`, métricas não-string/NaN | CHECK/validator rejeita, sem truncar Decimal |
| DB-08 | Tentar PASS sem evidência, com critical_failures>0, ou decisão PASS sem avaliações | Falha fechada na função/constraints |
| DB-09 | SQL INSERT run terminal/revision diferente de zero; SQL UPDATE de mesmo estado ou alterando started_at; duas transições CAS concorrentes | Inserção/atualização inválida falha; exatamente uma atualização com revision esperada tem sucesso |
| DB-10 | `lcp_app` tenta INSERT tardio em dataset_cases, experiment_candidates, policy_decision_evaluations; UPDATE/DELETE/TRUNCATE em aggregates | `permission denied` mesmo em segunda sessão após COMMIT; nenhum conjunto alterado |
| DB-11 | Testes existentes + `GET /health` | Sem regressão; documentar suite executada |
| DB-12 | `docker compose config -q` e GitHub Actions com PostgreSQL + `lcp_app` | Pipeline verde, banco real |
| DB-13 | `alembic downgrade base` e upgrade **somente** banco descartável | Rollback DDL documentado; perda de dados de teste reconhecida |
| DB-14 | Análise do diff contra contrato/allowed paths | Nenhum segredo, execução de código externo, mutation em domínio ou migrations automáticas |
| DB-15 | Função create_experiment recebe baseline de outro projeto/role errado, ausência de baseline ou de challenger, IDs repetidos; SQL de app tenta contornar função | FKs + validação atômica rejeitam; commit não deixa experimento parcial; ordinais challenger 0..N-1 |
| DB-16 | Run com case de outra versão, candidato não participante ou workload/projeto divergente | FKs compostas rejeitam inclusive via SQL direto |
| DB-17 | `Decimal('0.9500')`, `Decimal('1E-7')` em metrics; custo com >8 casas; NULL vs zero; NaN/Infinity | JSONB de strings preserva representação; custo numérico sem arredondamento; especiais falham |
| DB-18 | Política inexistente, subject inexistente, evaluation de outro projeto; `evaluation_ids` repetidos | FKs rejeitam inexistentes; repetidos válidos e reconstituídos na mesma ordem |
| DB-19 | Experimento com challenger IDs em ordem não alfabética; casos na ordem não lexical; origem, whitespace em identificadores; fingerprint | Tuplas exatamente preservadas; cases >=1 com ordinal contínuo 0..N-1; canonical_payload e hash conforme LCP-001 |

## Gates adicionais obrigatórios — consistência de agregados

- **AGG-A:** Após `lcp_create_dataset_version` e COMMIT, segunda conexão `lcp_app` não consegue acrescentar case, alterar a contagem ou substituir payload. A função falha para case vazio, IDs duplicados ou número/ordinal inválido; não deixa dataset_version órfã de cases.
- **AGG-B:** Após `lcp_create_experiment` e COMMIT, segunda conexão `lcp_app` não consegue acrescentar challenger ou mudar baseline. Inclui ao menos um challenger e preserva a ordem exata mesmo se IDs forem `z,a,m`.
- **AGG-C:** Após `lcp_create_policy_decision` e COMMIT, segunda conexão `lcp_app` não consegue acrescentar evaluation. IDs de avaliação duplicados na entrada devem retornar duplicados no mesmo ordinal.
- **SEC-A:** `lcp_app` não tem ownership, membership dos papéis privilegiados, DML/TRUNCATE nas tabelas agregadas nem CREATE em schemas confiáveis; EXECUTE só nas funções definidas. Funções SECURITY DEFINER têm search_path seguro, REVOKE PUBLIC e SQL estático.
- **STATE-A:** `lcp_app` não tem UPDATE direto em runs. A função CAS e o trigger rejeitam reabertura de terminal, overwrite started_at/finished_at e mudanças laterais de métricas em mesmo status.

## Comandos e evidências

Após aprovação/implementação: testes em banco de CI/Compose inequivocamente descartável; `cd backend && python -m pytest -q`; `docker compose config -q`; `alembic upgrade head` com URL de teste isolada. Registre logs, exit codes, SQLSTATE e commit. Não rodar `down -v` fora de um ambiente explicitamente descartável. Para testar adulteração de snapshot, use fixture controlada em banco de teste com papel administrador somente quando necessário, nunca mude triggers em ambiente real.

`passed` exige DB-01/03/04/06/07/08/09/10/11/12/15/16/17/18/19 e AGG-A/B/C, SEC-A, STATE-A. Se algum gate essencial não foi executado, declarar `blocked` ou `passed_with_restrictions` conforme criticidade; jamais PASS sem evidência. Mefisto escreve `validation-result.md` e `review.md` somente após inspeção independente.
