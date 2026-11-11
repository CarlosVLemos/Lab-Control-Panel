# LCP-002 — Contrato técnico de persistência

**State:** DRAFT · **Version:** 2 (revisão após análise do Codex)
**Risco:** CRITICAL · **Execution mode:** SINGLE_WRITER
**Human approval:** PENDING · **Approval reference:** PENDING
**Dependência:** PR #26 / LCP-001 integrado à `main` em `770ade0851d6ab077bb7fb6ef72fa1328b8c7fec`; esta branch sincronizada com essa base.

> Este é um contrato proposto, não uma autorização para implementar. Os tipos e constraints abaixo só serão considerados FROZEN após a aprovação humana. Se o código da LCP-001 integrada mudar, revalidar o mapeamento.

## 1. Tipos, identidade e serialização

- PostgreSQL >=16, SQLAlchemy 2.x, psycopg 3 e Alembic. SQLAlchemy só em infraestrutura; modelos Pydantic LCP-001 permanecem o contrato de domínio. Não editar `backend/app/domain/**` sem Change Request.
- Todos os IDs de domínio são `TEXT PRIMARY KEY` (ou `TEXT NOT NULL` para FKs), com `CHECK(length(btrim(id))>0)`. **Não converter IDs em UUID**; casos de teste têm IDs textuais dentro de cada versão de dataset.
- `projects.slug`: `CHECK(slug ~ '^[a-z][a-z0-9]*(?:-[a-z0-9]+)*$')`. `datasets.key` = identificador lógico do dataset **dentro de um projeto**, com a mesma sintaxe kebab-case; UNIQUE(project_id,key), nunca vazio. Não é nome de arquivo nem versão.
- `version` e demais referências textuais obrigatórias: `length(btrim(value)) > 0`.
- `candidate_versions`: UNIQUE(project_id,model_id,version), **não** UNIQUE(project_id,version). A mesma etiqueta `v1` pode existir em modelos distintos; dentro de um mesmo projeto/modelo, cada versão identifica um único snapshot. UNIQUE(dataset_id,version) para datasets; UNIQUE(dataset_version_id,case_id) para casos.
- Enums SQL exatos:
  - workload: `RESPONSE`, `TASK`, `CODE`
  - run status: `QUEUED`, `RUNNING`, `COMPLETED`, `FAILED`, `CANCELLED`
  - evaluation/policy verdict: `PASS`, `FAIL`, `INCONCLUSIVE`, `MANUAL_REVIEW`
  - member role: `BASELINE`, `CHALLENGER`
  Armazenar `TEXT` + `CHECK IN (...)`, não enums PostgreSQL customizados nesta etapa.
- Timestamps: `TIMESTAMPTZ` UTC, timezone-aware no Python. `created_at TIMESTAMPTZ NOT NULL DEFAULT now()`; origem: `origin_kind` (`SYSTEM`, `USER`, `CI`, `IMPORT`) e `origin_ref TEXT NOT NULL` não vazio nas escritas auditáveis; `created_at` é imutável. Não fabricar `origin_ref` como se fosse uma identidade autenticada; identificar job/request/fixture real.
- Custos: `cost_usd_estimated NUMERIC` **sem scale definido**, convertendo para `Decimal` sem arredondar, e `CHECK(cost_usd_estimated >= 0)` quando não nulo. `NULL` = desconhecido, `0` = medido zero. Tokens e duração: `BIGINT`, `CHECK >= 0` quando não nulos.
- `EvaluationResult.metrics: dict[str, Decimal]` em JSONB como **objeto de strings decimais**, nunca números binários/float. Exemplo `{"accuracy":"0.9500","loss":"1E-7"}`; codificar `str(Decimal)` e decodificar com `Decimal(str_value)`, preservando escala textual quando relevante. Rejeitar NaN/Infinity e valores que não sejam strings decimais. `artifact_refs`, `evaluation_ids`, `evidence_refs`, `tags`, `candidate_ids` têm representação JSON array de strings com ordem estável, sem números ou `null`.
- Para snapshots, persistir `canonical_payload TEXT NOT NULL` (JSON UTF-8 com `sort_keys=True`, separadores `(',', ':')`, `ensure_ascii=False`, `allow_nan=False`) e campos indexáveis em tabelas/JSONB. Os fingerprints de LCP-001 são calculados **pelo algoritmo Pydantic original** `content_fingerprint` usando seus respectivos payloads, e não por `jsonb::text`. Na leitura: recomputar, comparar hash, e conferir equivalência entre snapshot canônico e colunas/casos relacionais. A ordem de casos é preservada via `ordinal` único, iniciando em zero.
- SHA-256: `CHECK(hash ~ '^[0-9a-f]{64}$')` para fingerprints e `spec_sha256` opcional. `source_commit` opcional: `CHECK(source_commit ~ '^[0-9a-f]{7,40}$')`. Fingerprint é verificação de integridade, **não** prova de origem nem assinatura.

## 2. Esquema e relacionamentos mínimos

Tabelas são criadas exclusivamente por migração Alembic, sem `Base.metadata.create_all()` na inicialização. Toda FK tem política `ON DELETE RESTRICT` para histórico referenciado, salvo justificativa explícita posterior.

| Tabela | Campos principais | Integridade adicional |
| --- | --- | --- |
| `projects` | id, slug, name, created_at | PK; UNIQUE(slug); regex slug; não vazio |
| `datasets` | id, project_id, key, created_at | FK project; UNIQUE(project_id,key); UNIQUE(id,project_id) |
| `dataset_versions` | id, dataset_id, project_id, version, fingerprint, canonical_payload, created_at, origin_kind/ref | FK(dataset_id,project_id) -> datasets(id,project_id); UNIQUE(dataset_id,version); UNIQUE(id,project_id) |
| `dataset_cases` | dataset_version_id, case_id, ordinal, input JSONB, expected JSONB, tags JSONB | PK(dataset_version_id,case_id); UNIQUE(dataset_version_id,ordinal); `ordinal>=0`; `case_id` não vazio |
| `candidate_versions` | id, project_id, model_id, version, workload, config JSONB, spec_sha256?, source_commit?, fingerprint, canonical_payload, created_at, origin_kind/ref | UNIQUE(project_id,model_id,version); UNIQUE(id,project_id); UNIQUE(id,project_id,workload) |
| `experiments` | id, project_id, dataset_version_id, workload, baseline_candidate_id, baseline_role constant `BASELINE`, hypothesis, created_at, origin_kind/ref | FK(dataset_version_id,project_id) -> dataset_versions(id,project_id); FK(baseline_candidate_id,project_id,workload) -> candidate_versions; UNIQUE(id,project_id,workload); UNIQUE(id,project_id,dataset_version_id) |
| `experiment_candidates` | experiment_id, project_id, workload, candidate_id, role | PK(experiment_id,candidate_id); FK(experiment_id,project_id,workload) -> experiments; FK(candidate_id,project_id,workload) -> candidate_versions; UNIQUE(experiment_id,candidate_id,role); UNIQUE parcial(experiment_id) WHERE role='BASELINE' |
| `execution_runs` | id, experiment_id, project_id, dataset_version_id, test_case_id, candidate_id, workload, status, started_at?, finished_at?, trace_id?, artifact_refs JSONB, tokens/custo/duração?, revision, created_at, origin_kind/ref | FK(experiment_id,project_id,dataset_version_id) -> experiments; FK(dataset_version_id,test_case_id) -> dataset_cases; FK(experiment_id,candidate_id) -> experiment_candidates; FK(candidate_id,project_id,workload) -> candidate_versions; UNIQUE(id,project_id); índices (experiment_id,status), (candidate_id,status) |
| `evaluation_results` | id, run_id, project_id, evaluator_id, verdict, evidence_refs JSONB, critical_failures, metrics JSONB, created_at, origin_kind/ref | FK(run_id,project_id) -> execution_runs; UNIQUE(id,project_id); CHECK fail-closed |
| `policy_versions` | id, project_id, version, config JSONB, fingerprint, created_at, origin_kind/ref | FK project; UNIQUE(project_id,version); UNIQUE(id,project_id). Snapshot mínimo de versão de política para FK; **a lógica Policy Engine é futura** |
| `policy_decisions` | id, project_id, policy_version_id, subject_id, verdict, evidence_refs JSONB, reason, critical_failures, created_at, origin_kind/ref | FK(policy_version_id,project_id) -> policy_versions; FK(subject_id,project_id) -> candidate_versions; UNIQUE(id,project_id); CHECK fail-closed |
| `policy_decision_evaluations` | decision_id, evaluation_id, project_id, ordinal | PK(decision_id,evaluation_id); FK(decision_id,project_id) -> policy_decisions; FK(evaluation_id,project_id) -> evaluation_results; UNIQUE(decision_id,ordinal) |

`policy_decisions.subject_id` representa **somente CandidateVersion no MVP**. Uma avaliação do baseline pode servir de evidência para uma decisão sobre o challenger; por isso o join exige **mesmo projeto**, não mesmo candidato. Reconstituir `evaluation_ids` no domínio pela ordem `ordinal`, sem campo duplicado JSONB para IDs. `policy_version_id` referencia o registro mínimo `policy_versions`, sem antecipar a avaliação de políticas.

**Evidências externas:** `evidence_refs` e `artifact_refs` ainda são identificadores opacos de artefatos futuros e **não possuem FK** nesta issue. A camada de persistência valida formato/não-vazio e guarda proveniência declarada, mas **não consegue provar que o artefato existe**. Nenhum Release Controller pode tratar essa existência como verificada até uma Issue posterior implementar armazenamento/validação de evidências.

## 3. Garantias de pertencimento e atomicidade

Fazer as garantias de projeto/caso/candidato com FKs compostas declaradas na seção 2, não apenas `SELECT` de aplicação:

1. `experiment.project_id` coincide com a versão do dataset, projeto e workload do baseline; o par/campo composto é obrigatório.
2. `experiment_candidates` vincula candidatos do mesmo projeto/workload do experimento; inclui baseline como `BASELINE` e no mínimo um `CHALLENGER` distinto.
3. **Baseline presente:** adicionar FK composta `(experiments.id, baseline_candidate_id, baseline_role)` -> `experiment_candidates(experiment_id,candidate_id,role)`, `DEFERRABLE INITIALLY DEFERRED`. `baseline_role TEXT NOT NULL DEFAULT 'BASELINE' CHECK(baseline_role='BASELINE')`. O ciclo de FKs é resolvido **numa única transação**.
4. **Ao menos um challenger:** constraint trigger diferida (`DEFERRABLE INITIALLY DEFERRED`) verifica no commit que cada experimento tem >=1 `CHALLENGER`; execução apenas para inserts de experimentos e membros. Como experimentos/membros são append-only, a cardinalidade não diminui depois.
5. `execution_runs` carrega `dataset_version_id` e `project_id` redundantes, protegidos por FKs compostas; `test_case_id` é o ID textual do TestCase na versão, não PK global. A FK em `(experiment_id,candidate_id)` impede executar candidato não participante. A FK `(candidate_id,project_id,workload)` impede executar workload divergente.
6. Criar experimento + baseline + challengers **atomicamente**; criar run só após checagem de transição e identidade; falha de qualquer FK/trigger faz rollback integral. Race conditions devem ser testadas com duas sessões PostgreSQL reais.

Não adicionar triggers para simular regras abstratas além das invariantes acima. Testes de inserção SQL direta devem provar que uma associação de outro projeto, caso de outra versão ou baseline não inscrito falham de fato.

## 4. Status, vereditos e transações

### ExecutionRun

SQL CHECK obrigatório (além do `status IN (...)`):

- `QUEUED`: `started_at IS NULL AND finished_at IS NULL`.
- `RUNNING`: `started_at IS NOT NULL AND finished_at IS NULL`.
- `COMPLETED`: `started_at IS NOT NULL AND finished_at IS NOT NULL`.
- `FAILED` e `CANCELLED`: `finished_at IS NOT NULL`; `started_at` pode ser nulo se falhou/cancelou antes de iniciar.
- Sempre que ambos não nulos: `finished_at >= started_at`.
- `revision INTEGER NOT NULL DEFAULT 0 CHECK(revision>=0)`; tokens, custo, duração não negativos; `artifact_refs` JSON array.

No serviço, `transition_run(run_id,expected_status,target_status,expected_revision,timestamps)` valida `assert_run_transition` de LCP-001, faz **um** UPDATE condicional com `WHERE id=:id AND status=:expected_status AND revision=:expected_revision`, incrementa revision e exige `rowcount=1`. `0` = `ConcurrencyConflict` explícito. Um trigger PostgreSQL compara `OLD.status`/`NEW.status` para rejeitar transições fora do grafo, revisões que não incrementam e alterações indevidas dos campos de identidade. Estado terminal não reabre. Testes cobrem SQL direto e duas sessões concorrentes.

### EvaluationResult / PolicyDecision

- `critical_failures INTEGER NOT NULL CHECK(critical_failures>=0)`.
- `PASS` exige `critical_failures=0` e pelo menos uma evidência (`jsonb_typeof(evidence_refs)='array'` e `jsonb_array_length(evidence_refs)>0`).
- `PolicyDecision.PASS` também exige ao menos uma associação `policy_decision_evaluations`. Um constraint trigger diferido verifica a contagem ao commit.
- `FAIL`, `INCONCLUSIVE` e `MANUAL_REVIEW` permanecem estados distintos; a persistência não transforma qualquer um em `PASS`.
- `PolicyDecision` e avaliações são criadas em transação; IDs de avaliações só apontam para avaliações reais do mesmo projeto. `PolicyDecision` e join `policy_decision_evaluations` são append-only. Se PASS referenciar evidência externa não verificável, a **persistência** registra a declaração, mas **não autoriza promoção automática**.

## 5. Append-only e auditoria

- Adicionar triggers PostgreSQL de bloqueio `UPDATE/DELETE` para `dataset_versions`, `dataset_cases`, `candidate_versions`, `experiments`, `experiment_candidates`, `policy_versions`, `evaluation_results`, `policy_decisions` e `policy_decision_evaluations`. `created_at`, `origin_kind/ref` são escritos na criação e não editados; `ON DELETE RESTRICT` protege referências.
- Os repositórios não expõem `update/delete` dessas tabelas. Contas normais da aplicação **não podem desabilitar triggers nem aplicar migrations**; separar papel de migração e papel de aplicação.
- Superusuários e operadores privilegiados podem modificar triggers/dados: esta é uma garantia de append-only sob papéis de aplicação, **não WORM criptográfico**. Evidência de origem exige mecanismo assinado em futuro escopo.
- `get_dataset_version` reconstrói cases por `ordinal` e verifica payload canônico, colunas e fingerprint calculado como a LCP-001; `get_candidate_version` faz verificação análoga. Divergência = `SnapshotIntegrityError`, nunca correção silenciosa.
- `created_at`, `origin_kind/ref` são obrigatórios ao criar avaliação, decisão e snapshots. `origin_ref` identifica origem registrada, não prova autenticidade de usuário. Falhas e conflitos são exceções tipadas; rollback garante que decisões parciais não persistam.

## 6. Migração, ambiente e limites

- Alembic é a única via para DDL; segunda execução de `upgrade head` deve ser idempotente. Migração cria constraints, triggers, índices e privilégios necessários. Sem auto-migration no startup da API.
- Docker Compose de desenvolvimento sobe PostgreSQL com healthcheck e volume nomeado; **não executar `down -v` em volume não descartável**. Configuração via `DATABASE_URL` e variáveis de exemplo, sem segredos reais versionados.
- CI usa PostgreSQL real descartável. Testar constraint trigger diferida (incluindo rollback), FKs compostas, snapshots, precisão Decimal, concorrência CAS e `/health`. Testes destructive somente no banco descartável.
- `downgrade` só em ambiente de teste criado para esse fim; a migração é **destrutiva** para os dados que forem removidos. Não prometer rollback de dados em produção sem backup.
- Fora do escopo: endpoints públicos, Redis/RQ, frontend, deploy, código de terceiros, liberação de modelos e avaliação LLM. `README.md` permanece compacto; paths permitidos em `tasks.md`.

## 7. Aprovação

**DRAFT v2 — aprovação humana PENDING.** Não iniciar implementação nem alterar `backend/app/domain/**` enquanto esta branch não estiver alinhada ao contrato Pydantic integrado e o usuário não aprovar este contrato explicitamente. **Dependência de integração: atendida; aprovação: pendente.** Mudanças posteriores exigem Change Request documentada.
