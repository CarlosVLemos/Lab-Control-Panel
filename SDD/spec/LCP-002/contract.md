# LCP-002 — Contrato MVP v4

**Status:** FROZEN · **Escopo:** MVP demonstrável · **Risco:** CRITICAL por envolver migrações
**Modo:** SINGLE_WRITER (Maquiavel)
**Aprovação humana:** orientação de 2026-11-11 e [CR-001](CHANGE_REQUEST-001.md)
**Dependência:** LCP-001 integrada à main (commit `770ade0`).
**Não** alterar `backend/app/domain/**`.

## 1. Tecnologia e persistência

- Python 3.12+, FastAPI, PostgreSQL 16+, SQLAlchemy 2.x, psycopg 3 e Alembic. Migração explícita `alembic upgrade head`, nunca `create_all()` ou DDL no startup.
- **Somente sete tabelas:** `projects`, `dataset_versions`, `candidate_versions`, `experiments`, `execution_runs`, `evaluation_results`, `policy_decisions`. Não criar `datasets`, tabelas de associação, `policy_versions` ou funções SECURITY DEFINER.
- IDs são `TEXT`, não UUID. `projects.slug` UNIQUE; versão de dataset UNIQUE(project_id,dataset_id,version); candidato UNIQUE(project_id,model_id,version). Campos obrigatórios NOT NULL; CHECK simples para enums/status/veredito, duração/tokens/custo não-negativos (custo deve ser finito). Tipos de tempo `TIMESTAMPTZ`; `created_at` no DB. 
- FKs diretas: project_id -> projects quando aplicável; experiment -> dataset_version e baseline_candidate; run -> experiment e candidate; evaluation -> run; decision.subject_id -> candidate. `policy_version_id` permanece TEXT opaco nesta Issue, sem Policy Engine. Não alegar validação referencial que não existe.
- JSONB armazena **arrays na ordem original**: `dataset_versions.cases`, `experiments.candidate_ids` e `policy_decisions.evaluation_ids`. O conjunto de casos precisa ser não vazio; challengers não vazios, sem baseline/duplicações; IDs de avaliação **podem repetir** conforme LCP-001. O repositório valida referências antes do commit.
- Snapshots de DatasetVersion e CandidateVersion contêm payload reconstruível e fingerprint SHA-256. Validar Pydantic e recalcular o fingerprint **antes de inserir** e **após ler**. DatasetVersion hash exclui `id` e usa cases na ordem original; CandidateVersion hash inclui `id` e exclui só o campo computado. Usar exatamente `content_fingerprint` da LCP-001, não `jsonb::text`. Divergência causa `SnapshotIntegrityError`.
- `EvaluationResult.metrics` JSONB de **strings** Decimal (`"0.9500"`, `"1E-7"`), nunca floats; custo USD `NUMERIC` sem arredondamento e diferente de NULL. Rejeitar NaN/Infinity/JSONB não representável com erro tipado; valores Pydantic JSON extremos fora da capacidade do PostgreSQL não fazem parte da garantia MVP.

## 2. Operações na aplicação

- Repositórios SQLAlchemy com Unit of Work/sessões explícitas; transações atômicas/rollback, sem sessão global e sem API pública CRUD nova nesta tarefa.
- Criar projeto, dataset version, candidate version, experiment, run, evaluation e decision; ler após encerrar/reabrir conexão. Repositórios **não** expõem UPDATE/DELETE para snapshots, experimentos e decisões.
- `create_experiment` valida no mesmo contexto transacional que dataset, baseline e challengers existem, pertencem ao projeto e têm workload compatível. `candidate_ids` preserva a ordem. `create_run` valida candidate e case pertencentes ao experimento. **Essas guardas não protegem de SQL direto**, apenas do caminho de aplicação.
- `create_run` inicia `QUEUED`, revision=0 e tempos NULL. SQL CHECK garante combinações válidas de status/timestamps. `transition_run` usa `assert_run_transition` da LCP-001 e **um UPDATE condicional** por id/status/revision; 0 linhas = `ConcurrencyConflict`; não sobrescrever started_at nem reabrir terminal. IDs/FKs imutáveis na lógica de serviço.
- Evaluation/Decision usam modelos Pydantic existentes: PASS exige evidências não vazias e critical_failures=0; decision PASS exige IDs de avaliações referenciadas. Validar IDs/pertencimento ao projeto no repositório; evidências externas são IDs opacos, **não prova de armazenamento nem autorização de release**.
- Política de confiança: banco gerenciado pela aplicação em dev/demo, sem atores com acesso SQL direto. Não prometer append-only via DB triggers, auditoria assinada ou segurança multi-tenant.

## 3. Infra e aceite

- Docker Compose: API + PostgreSQL, healthcheck e volume persistente; sem credenciais reais em repositório, `.env.example` somente exemplo. Dockerfile com usuário não-root e .dockerignore.
- CI: pytest com **PostgreSQL real**, migração de banco vazio, testes de sessão nova, fingerprint, constraints, CAS, PASS e regressão de `/health`. Evidências observadas (não inventadas).
- Kubernetes, worker RQ/Redis, Vue, Response runner e Policy Engine são **outras Issues**, organizadas em `docs/MVP_DEMO_PLAN.md`. Não iniciar essas implementações aqui.

**Definition of Done:** testes M-01..M-10 do `tests.md` efetivamente executados, commits na branch, revisão técnica Mefisto sobre código e PR para aprovação humana. **Sem merge automático**.
