# LCP-002 — Plano de verificação independente (revisão v2)

**Owner:** Mefisto
**Contrato:** DRAFT v2
**Estado:** NOT_RUN — planejamento; implementação bloqueada
**Alvo:** PostgreSQL isolado/descartável em Docker e CI; Python 3.12+
**Regra:** saída real e commit identificado; `NOT_RUN`/`BLOCKED` nunca equivalem a PASS.

| ID | Verificação | Resultado exigido |
| --- | --- | --- |
| DB-01 | `alembic upgrade head` em banco vazio | Todas as tabelas/constraints/triggers aparecem; revision registrada |
| DB-02 | Segundo `alembic upgrade head` | Idempotente; sem DDL fora de Alembic |
| DB-03 | Round-trip Project, DatasetVersion com cases ordenados, CandidateVersion, Experiment | IDs textuais, payload e fingerprints preservados após nova sessão |
| DB-04 | Run, EvaluationResult, PolicyDecision; reconectar/reiniciar aplicação | Dados persistidos e associados corretamente |
| DB-05 | Reiniciar containers **sem** `down -v` | Volume PostgreSQL mantém linhas |
| DB-06 | Slug/key/version/case duplicados e IDs/slug/regex inválidos | UNIQUE/CHECK/FK recusam inserts |
| DB-07 | Workload/status/verdict inválidos; custos/tokens/duração negativos | CHECKs rejeitam sem arredondamento de Decimal |
| DB-08 | PASS sem evidências, com falhas críticas, ou PolicyDecision PASS sem evaluation join | Banco rejeita ao commit; zero promoção |
| DB-09 | Status inválido via SQL direto + duas transições concorrentes com revision igual | Trigger rejeita salto; CAS atualiza exatamente uma vez |
| DB-10 | UPDATE/DELETE de snapshots/cases/policy/evals/decisions por papel de aplicação | Triggers/ACL recusam; leitura acusa payload ou hash divergente em fixture de teste controlada |
| DB-11 | Suite backend anterior e `/health` | Sem regressão |
| DB-12 | `docker compose config -q` + CI pull request | Workflow com PostgreSQL real e pytest passando |
| DB-13 | `alembic downgrade base` e upgrade **somente** em banco descartável | Reversão DDL documentada; perda de dados de teste reconhecida |
| DB-14 | Diff completo | Sem segredos, migrations automáticas, runner de código externo, scope drift |
| DB-15 | Experiment baseline fora do projeto; challenger workload distinto; baseline ausente/role errado; sem challenger | FK composta/constraint trigger diferida rejeita **inserts SQL diretos** |
| DB-16 | Run ligado a case de outra versão, candidato não associado ou projeto/workload divergentes | FKs compostas rejeitam **inserts SQL diretos** |
| DB-17 | `metrics` com `Decimal('0.9500')`, `Decimal('1E-7')`; custo com >8 casas; `None` vs zero | Valores e escala round-trip, JSONB strings e NUMERIC sem truncamento |
| DB-18 | PolicyVersion inexistente, subject inexistente, evaluation de outro projeto, join inconsistente | FK composta rejeita e transação volta |
| DB-19 | Proveniência obrigatória, origem não vazia, ordenação de candidate/evaluation IDs e cases | Reconstituição determinística com hashes iguais |

## Testes de execução e segurança

Implementar testes executáveis em `backend/tests/` usando credenciais **exclusivamente** de banco de testes; fixtures isoladas e transações reversíveis. Testes de triggers precisam de PostgreSQL real (não substituí-los por SQLite/mocks). Não desabilitar triggers em banco de trabalho/produção para simular adulteração; para `SnapshotIntegrityError`, usar fixture controlada que injeta payload inconsistente na camada de leitura ou banco de teste separado.

Começar com testes focados e expandir à suíte backend; guardar comandos exatos, variáveis não sensíveis, SQLSTATE, stacktrace resumido, exit code e commit testado. Validar shutdown/startup sem apagar volumes e usar `down -v` somente quando o volume for comprovadamente descartável.

**Gates obrigatórios para `passed`:** DB-01/03/04/06/08/09/10/11/12/15/16/17/18. Os demais devem ser executados quando aplicáveis ou explicitamente justificados. Vereditos: `passed`, `failed`, `blocked`, `passed_with_restrictions`.

Após aprovação e implementação, Mefisto registra evidências em `validation-result.md` e veredito independente em `review.md`. Esta revisão de plano **não equivale a execução de testes**.
