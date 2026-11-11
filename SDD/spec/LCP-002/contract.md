# LCP-002 — Contrato técnico de persistência

**State:** DRAFT · **Version:** 3 (parecer Codex/Jarvis `NEEDS_REVISION`)
**Risco:** CRITICAL · **Execution mode:** SINGLE_WRITER
**Human approval:** PENDING · **Approval reference:** PENDING
**Dependência:** LCP-001 integrada à `main` no commit `770ade0851d6ab077bb7fb6ef72fa1328b8c7fec`.
**Status de implementação:** BLOCKED — não programar nem executar migrações antes de aprovação humana explícita.

> Versão proposta para uma última revisão. Este arquivo especifica garantias observáveis pelo papel real de aplicação; o proprietário do banco/migrações permanece privilegiado. Não confundir CI verde de documentação com testes PostgreSQL executados.

## 1. Fronteiras e tipos

- Stack: PostgreSQL >=16, SQLAlchemy 2.x, psycopg 3 e Alembic; FastAPI/Pydantic no domínio sem acoplamento ao ORM. `backend/app/domain/**` (LCP-001) permanece protegido.
- IDs de domínio são `TEXT` (nunca trocar por UUID); para textos obrigatórios, `NOT NULL` e `CHECK(length(btrim(value))>0)`. O mapper usa o mesmo `str.strip()` do `Identifier` Pydantic **antes de persistir**; PostgreSQL `btrim` cobre espaços ASCII comuns, **não** promete equivalência com toda a normalização Unicode de Python. Testar ambos os limites, inclusive SQL direto.
- `projects.slug` e `datasets.key` usam a expressão `^[a-z][a-z0-9]*(?:-[a-z0-9]+)*$`. `datasets.key` é o nome lógico não vazio de um dataset **dentro do projeto**: UNIQUE(project_id,key).
- `candidate_versions`: UNIQUE(project_id,model_id,version); `dataset_versions`: UNIQUE(dataset_id,version); `dataset_cases`: UNIQUE(dataset_version_id,case_id).
- SQL `TEXT + CHECK IN`: Workload `RESPONSE/TASK/CODE`; RunStatus `QUEUED/RUNNING/COMPLETED/FAILED/CANCELLED`; Verdict `PASS/FAIL/INCONCLUSIVE/MANUAL_REVIEW`; participant role `BASELINE/CHALLENGER`; origin_kind `SYSTEM/USER/CI/IMPORT`.
- `created_at TIMESTAMPTZ NOT NULL DEFAULT now()`, origem `origin_kind` e `origin_ref TEXT NOT NULL` não vazio nas entidades auditáveis (versões, experimentos, runs, avaliações e decisões). Guardar UTC e timezone-aware na aplicação; `origin_ref` é uma origem **declarada**, não autenticação.
- Custo `cost_usd_estimated NUMERIC` sem escala fixa: `CHECK(cost_usd_estimated IS NULL OR (cost_usd_estimated >= 0 AND cost_usd_estimated::text NOT IN ('NaN','Infinity','-Infinity')))`. PostgreSQL aceita valores especiais em NUMERIC; somente `>=0` **não** rejeita `NaN`. `NULL` = não medido; `0` = zero conhecido. Armazenar custo como `Decimal`, sem converter para `float`; round-trip numérico exato, sem promessa de preservar notação textual/exponente para custos. Valores fora do limite de NUMERIC devem falhar explicitamente.
- Tokens e duração: `BIGINT`, `CHECK(value>=0)` quando não nulo.
- `EvaluationResult.metrics: dict[str, Decimal]`: JSONB `{"accuracy":"0.9500","loss":"1E-7"}`, com valores **strings** `str(Decimal)`, never float. Converter de volta com `Decimal(value)`; rejeitar entradas não decimais, NaN/Infinity, tipos JSON diferentes de string e perda de precisão. Função de validação imutável SQL `lcp_valid_decimal_metrics(jsonb)` para CHECK em `evaluation_results.metrics`; validar também no mapper Python.
- Arrays `artifact_refs`, `evidence_refs`, `tags` são JSONB contendo exclusivamente strings não vazias; a função SQL imutável `lcp_valid_identifier_array(jsonb)` confirma tipo array, tipo string de cada elemento e não-vazio após trim. Arrays vazios só quando o Pydantic os permite; `PASS` requer ao menos uma evidência. Strings `null`, vazias e whitespace-only são inválidas, inclusive sob SQL direto. **Não** persistir `candidate_ids` nem `evaluation_ids` em JSONB: suas ordens vêm das relações com `ordinal`.
- `spec_sha256` opcional e fingerprints obrigatórios: regex `^[0-9a-f]{64}$`; `source_commit` opcional: `^[0-9a-f]{7,40}$`. SHA-256 é detecção de divergência, não prova criptográfica de autoria.

## 2. Esquema e constraints

Alembic cria o esquema (sem `Base.metadata.create_all()` nem migration no startup). FKs compostas são a proteção para pertença ao mesmo projeto/experimento. Relações históricas usam `ON DELETE RESTRICT`.

| Tabela | Colunas principais | Garantia essencial |
| --- | --- | --- |
| `projects` | id, slug, name, created_at | PK id, UNIQUE slug, regex e não-vazio |
| `datasets` | id, project_id, key, created_at | FK project, UNIQUE(project_id,key), UNIQUE(id,project_id) |
| `dataset_versions` | id, dataset_id, project_id, version, fingerprint, canonical_payload TEXT, origin_kind/ref, created_at | FK(dataset_id,project_id), UNIQUE(dataset_id,version), UNIQUE(id,project_id), snapshot fechado via função |
| `dataset_cases` | dataset_version_id, case_id, ordinal, input JSONB, expected JSONB, tags JSONB | PK(dataset_version_id,case_id), UNIQUE(dataset_version_id,ordinal), ordinal >=0; conjunto fechado na criação |
| `candidate_versions` | id, project_id, model_id, version, workload, config JSONB, spec_sha256?, source_commit?, fingerprint, canonical_payload TEXT, origin_kind/ref, created_at | FK(project_id)->projects, UNIQUE(project_id,model_id,version), UNIQUE(id,project_id), UNIQUE(id,project_id,workload), append-only |
| `experiments` | id, project_id, dataset_version_id, workload, baseline_candidate_id, baseline_role='BASELINE', hypothesis, origin_kind/ref, created_at | FK(dataset_version_id,project_id), FK(baseline_candidate_id,project_id,workload), UNIQUE(id,project_id,workload), UNIQUE(id,project_id,dataset_version_id) |
| `experiment_candidates` | experiment_id, project_id, workload, candidate_id, role, ordinal NULLABLE | PK(experiment_id,candidate_id); FK(experiment_id,project_id,workload), FK(candidate_id,project_id,workload); UNIQUE(experiment_id,candidate_id,role) **NOT DEFERRABLE**; UNIQUE(experiment_id,ordinal); UNIQUE parcial(experiment_id) WHERE role='BASELINE' |
| `execution_runs` | id, experiment_id, project_id, dataset_version_id, test_case_id, candidate_id, workload, status, started_at?, finished_at?, trace_id?, artifact_refs JSONB, usage?, revision, origin_kind/ref, created_at | FK(experiment_id,project_id,dataset_version_id), FK(dataset_version_id,test_case_id), FK(experiment_id,candidate_id), FK(candidate_id,project_id,workload), UNIQUE(id,project_id), índices (experiment_id,status), (candidate_id,status) |
| `evaluation_results` | id, run_id, project_id, evaluator_id, verdict, evidence_refs JSONB, critical_failures, metrics JSONB, origin_kind/ref, created_at | FK(run_id,project_id), UNIQUE(id,project_id), CHECK enum/evidence/metrics; append-only |
| `policy_versions` | id, project_id, version, config JSONB, origin_kind/ref, created_at | FK project, UNIQUE(project_id,version), UNIQUE(id,project_id); versão de referência **sem fingerprint nesta issue**, sem Policy Engine |
| `policy_decisions` | id, project_id, policy_version_id, subject_id, verdict, evidence_refs JSONB, reason, critical_failures, origin_kind/ref, created_at | FK(policy_version_id,project_id), FK(subject_id,project_id)->candidate_versions, UNIQUE(id,project_id), CHECK PASS/evidências; conjunto fechado via função |
| `policy_decision_evaluations` | decision_id, evaluation_id, project_id, ordinal | **PK(decision_id,ordinal)**; FK(decision_id,project_id)->policy_decisions; FK(evaluation_id,project_id)->evaluation_results; `ordinal>=0`; **sem UNIQUE(decision_id,evaluation_id)** |

**Ordem e compatibilidade:** `experiment_candidates.ordinal IS NULL` apenas para `BASELINE`, e `ordinal>=0` para `CHALLENGER` (CHECK de exclusividade). Challengers têm ordinais 0..N-1, sem lacunas, persistidos na ordem de `Experiment.candidate_ids`. O baseline não aparece no retorno da tupla. Para `policy_decision_evaluations`, `ordinal` é 0..N-1 e repetições de `evaluation_id` são **permitidas** porque o contrato Pydantic LCP-001 permite; a aplicação reconstrói `PolicyDecision.evaluation_ids` com repetições, sem ordenação alfabética. `dataset_cases` tem ordinal 0..N-1 e >=1 caso.

**Integridade de baseline:** adicionar a FK `(experiments.id,baseline_candidate_id,baseline_role)` -> `experiment_candidates(experiment_id,candidate_id,role)` como `DEFERRABLE INITIALLY DEFERRED`. Criar as tabelas antes de adicionar a FK de retorno para resolver o ciclo DDL. A `UNIQUE(experiment_id,candidate_id,role)` referenciada permanece não-diferível. A FK composta impede baseline ausente ou inscrito como challenger no commit.

**Referências externas:** `evidence_refs` e `artifact_refs` ainda são IDs opacos **sem FK para storage de artefatos**. A persistência valida forma, não existência nem autenticidade. Um `PolicyDecision.PASS` **não** autoriza automaticamente release/promoção.

## 3. Fronteira única de escrita e imutabilidade

**Escolha para v3: operações transacionais por agregado + ACL. Não criar um trigger diferido por cada linha de associação.**

- Papéis distintos `lcp_migrator` (DDL/ownership), `lcp_aggregate_writer` (NOLOGIN, proprietário das funções com apenas os privilégios mínimos de DML) e `lcp_app` (LOGIN, sem ownership/membership do migrator/writer). O runtime `lcp_app` **não** recebe INSERT/UPDATE/DELETE/TRUNCATE em `dataset_versions`, `dataset_cases`, `experiments`, `experiment_candidates`, `policy_decisions` nem `policy_decision_evaluations`. Em tabelas de snapshot `candidate_versions`, `policy_versions` e `evaluation_results`, INSERT normal permitido mas UPDATE/DELETE/TRUNCATE negados; triggers append-only cobrem alterações mesmo por papéis escritores.
- Criar funções de banco, `SECURITY DEFINER`, com owner `lcp_aggregate_writer` e `EXECUTE` **somente** para `lcp_app`. Revogar `PUBLIC EXECUTE` no mesmo transaction block da criação. Fixar `SET search_path = pg_catalog, lcp_private, pg_temp`, qualificar tabelas, não usar SQL dinâmico nem dar CREATE em schemas de confiança ao runtime. O dono dessas funções **não** pode desabilitar triggers, possuir as tabelas ou aplicar migrations. Não confiar apenas em `SET ROLE`/convenção de aplicação.
- Interfaces canônicas (argumentos de texto/JSON são validados como contratos Pydantic pelo mapper e como estrutura SQL obrigatória pela função):
  - `lcp_create_dataset_version(project_id TEXT, snapshot TEXT, fingerprint TEXT, origin_kind TEXT, origin_ref TEXT) RETURNS TEXT`: a função extrai `DatasetVersion.id/dataset_id/version/cases` do snapshot; insere versão e **todos** os cases em uma transação do chamador; rejeita array vazio, IDs duplicados e ordinais não contíguos. Não existe parâmetro para acrescentar case a versão pré-existente.
  - `lcp_create_experiment(project_id TEXT, snapshot JSONB, workload TEXT, origin_kind TEXT, origin_ref TEXT) RETURNS TEXT`: extrai `Experiment` validado, insere cabeçalho, baseline (`role=BASELINE,ordinal=NULL`) e challengers na ordem original (`role=CHALLENGER,ordinal=0..N-1`). Exige ao menos um challenger, IDs distintos e projeto/workload coincidentes; FK diferida do baseline valida no COMMIT. Não permite adicionar candidato a experimento existente.
  - `lcp_create_policy_decision(project_id TEXT, snapshot JSONB, origin_kind TEXT, origin_ref TEXT) RETURNS TEXT`: insere decisão e **todas** as referências a avaliações ordenadas em um único agregado; preserva IDs repetidos; verifica FKs do mesmo projeto; `PASS` exige evidência válida, falhas críticas zero e >=1 avaliação. Não permite acrescentar vínculo a decisão preexistente.
  - `lcp_transition_run(run_id TEXT, expected_status TEXT, expected_revision INTEGER, target_status TEXT, changes JSONB) RETURNS INTEGER`: valida estado, allowed fields e transição com compare-and-swap, atualiza status/revision e retorna nova revisão ou conflito explícito.
- A função SQL é **atômica como uma única operação de escrita** dentro da transação PostgreSQL do chamador; não faz COMMIT autônomo. A aplicação confirma/rollback a transação; outra sessão não consegue acrescentar elementos depois que a versão/experimento/decisão foi criada porque perdeu permissão de INSERT direto e as funções somente criam novos agregados com IDs únicos.
- Permissões para `lcp_app` incluem somente SELECT das tabelas necessárias, INSERT de registros pontuais permitidos (`projects/datasets/candidate_versions/execution_runs/evaluation_results/policy_versions`), EXECUTE das funções acima e nenhuma permissão TRUNCATE ou de ownership. UPDATE de `execution_runs` só pelo `lcp_transition_run`; migração pode exercer privilégios administrativos exclusivamente em ambiente de migração. `lcp_app` não tem CREATE em `public`/`lcp_private`, não pode criar objetos ou reconfigurar triggers/ACL.
- Triggers simples bloqueiam UPDATE/DELETE de tabelas append-only inclusive quando invocados pelo escritor proprietário da função; os inserts iniciais são permitidos. Para agregados, a **completude** é garantida por função de criação + bloqueio de DML direto, e não só por bloquear UPDATE/DELETE. Constraints de FK/CHECK continuam protegendo contra erros internos da função.
- Sob superusuário, migração privilegiada ou alteração de DDL não há garantia criptográfica WORM. Informar o limite e testar usando o papel **real** `lcp_app` em duas conexões.

## 4. Contratos da LCP-001 e fingerprints

- O `canonical_payload TEXT` do dataset armazena a representação completa reconstruível de `DatasetVersion.model_dump(mode='json',exclude={'fingerprint'})` (inclui `id`; cases ordenados); o **hash** é calculado exclusivamente sobre `{'dataset_id': model.dataset_id,'version': model.version,'cases':[case.model_dump(mode='json')...]}`. **Não** incluir `DatasetVersion.id` no hash, como manda a LCP-001.
- O snapshot de `CandidateVersion` armazena `CandidateVersion.model_dump(mode='json',exclude={'fingerprint'})`, incluindo `id`, `version`, `workload`, `model_id`, `config`, `spec_sha256` e `source_commit`. O hash é `content_fingerprint` sobre esse dump completo **sem** `fingerprint`.
- Serialização do snapshot: `json.dumps(payload,ensure_ascii=False,sort_keys=True,separators=(',',':'),allow_nan=False)`, UTF-8. `canonical_payload TEXT` e projeções JSONB/colunas são conferidos na leitura. JSONB não define a serialização do fingerprint; as **ordens dos arrays** são preservadas por `ordinal` e pelo snapshot.
- `get_dataset_version` / `get_candidate_version` reconstroem o Pydantic **sem** metadados exclusivos da persistência (`project_id`, `revision`, `origin_*`, `created_at`, `workload` de experimento); recalculam o fingerprint pela implementação da LCP-001 e verificam igualdade com o armazenado e com as projeções relacionais. Divergência = `SnapshotIntegrityError`. Nunca normalizar hash silenciosamente.
- `policy_versions` é somente uma linha imutável com `id/project_id/version/config` auditáveis; **nenhum fingerprint nesta issue**. Uma versão de política com hash verificável exigirá algoritmo e extensão de domínio próprios, em issue posterior.
- Identificadores recebidos são normalizados via Pydantic `Identifier` antes da escrita. Banco rejeita IDs vazios, com CHECK ASCII básico; não prometer que `btrim` detecta exatamente o mesmo conjunto Unicode de `str.strip()`. Rejeitar payloads não canônicos e registrar erro tipado; testes de strings contendo espaços ASCII e NBSP nas fronteiras adequadas.

## 5. ExecutionRun: estados, permissões e concorrência

- `execution_runs` sempre nasce com `status='QUEUED'`, `revision=0`, `started_at=NULL`, `finished_at=NULL`; além de DEFAULT, trigger `BEFORE INSERT` rejeita qualquer estado/revision inicial incompatível. Importação histórica de runs fora do escopo.
- CHECK SQL:
  - `QUEUED`: started_at IS NULL e finished_at IS NULL
  - `RUNNING`: started_at IS NOT NULL e finished_at IS NULL
  - `COMPLETED`: started_at IS NOT NULL e finished_at IS NOT NULL
  - `FAILED`/`CANCELLED`: finished_at IS NOT NULL; started_at pode ser NULL se finalizado antes de iniciar
  - Se ambos não NULL: finished_at >= started_at
  - Revision INTEGER >=0; usage não-negativo/finito; artifact_refs array de IDs válidos.
- Transições permitidas (LCP-001): `QUEUED -> RUNNING | FAILED | CANCELLED`; `RUNNING -> COMPLETED | FAILED | CANCELLED`; estados terminais não reabrem. Sem atualizações de mesmo estado, nem mesmo para métricas: o MVP registra usage/artefatos ao mudar status; telemetria incremental é uma evolução futura.
- `started_at` só pode ser definida ao entrar em RUNNING, e **não pode ser substituída depois**; `finished_at` só é preenchida na transição terminal, exatamente uma vez. Campos de identidade/FK, `created_at` e `origin_*` nunca mudam. Campos `usage`, `trace_id` e `artifact_refs` só mudam durante uma transição válida (não por UPDATE lateral).
- `lcp_transition_run` executa um único `UPDATE ... WHERE id=:id AND status=:expected_status AND revision=:expected_revision`; em sucesso, revision incrementa exatamente 1; em `rowcount=0`, retorna erro tipado `ConcurrencyConflict` (não sobrescreve resultados). Trigger de UPDATE valida o grafo de estados, imutabilidade e incremento, inclusive SQL direto realizado por papel privilegiado. Papel runtime não recebe UPDATE direto para não contornar CAS.
- Repositório transacional via SQLAlchemy/UoW, sem sessão global. `get_*` reconstrói Pydantic; conflitos de FK/UNIQUE/concorrência mapeados para exceções tipadas. Persistência não habilita promoção nem altera automaticamente vereditos.

## 6. Avaliações, evidências e decisões

- `evaluation_results.critical_failures` e `policy_decisions.critical_failures`: INTEGER NOT NULL CHECK >=0. `PASS` exige critical_failures=0, `jsonb_array_length(evidence_refs)>0` e todos os IDs de evidência válidos (via `lcp_valid_identifier_array`). `FAIL/INCONCLUSIVE/MANUAL_REVIEW` não passam a PASS.
- `PolicyDecision.PASS` também requer pelo menos um registro em `policy_decision_evaluations`. A função `lcp_create_policy_decision` realiza a validação **antes de inserir o agregado**; sem INSERT direto pelo runtime, não é necessário trigger diferido para contagem. A integridade de FK garante que cada avaliação existe no mesmo projeto.
- `policy_decisions.subject_id` referencia exclusivamente `CandidateVersion` no MVP; a mesma avaliação de baseline pode constar em decisão do challenger se o projeto coincidir. Isso **não prova** que a avaliação pertence ao mesmo experimento; tal relevância é decisão futura do Policy Engine.
- `PolicyDecision.evaluation_ids` pode conter IDs repetidos na LCP-001. A tabela de associação usa `PK(decision_id,ordinal)`, não `PK(decision_id,evaluation_id)`. Reconstituir pela ordem dos ordinais, preservando duplicatas; validar tamanho >=1 somente para PASS. Nenhuma adição após o agregado fechado.
- As `evidence_refs`/artefatos são **opacos**; formato/registro não implica existência/autenticidade. Nenhum release é liberado por essa etapa.

## 7. Migrações, testes e limites de escopo

- Migration Alembic cria papéis/privileges quando as permissões do ambiente permitirem; documentar bootstrap de roles quando a CI/Compose os prover externamente. O teste real **deve** conectar como `lcp_app`, não como owner/superusuário, e demonstrar `permission denied` em INSERT tardio, UPDATE e TRUNCATE. Provisionar grants/revokes sob migração, não via runtime.
- `alembic upgrade head` no banco descartável e segunda execução idempotente; rollback `downgrade` **apenas** em banco de teste, com advertência de perda de dados. Docker Compose com PostgreSQL healthcheck/volume nomeado sem `down -v` não autorizado.
- Suite pytest/CI em PostgreSQL real cobrindo DB-01..DB-19 do plano atualizado, regressão `/health`, triggers, FKs, papel de aplicação, concorrência, ordem e Decimal. Mocks/SQLite não substituem estas provas.
- Não implementar worker/Redis/RQ, UI, endpoints públicos, Policy Engine, geração/execução de código hostil, deploy real, migração de dados de produção nem alteração de `README.md`. `Allowed paths` definidos em `tasks.md`.

## 8. Gate de aprovação

**DRAFT v3 — PENDING.** O veredito anterior foi `NEEDS_REVISION`. Este arquivo endereça os pontos levantados, **mas ainda não foi revisto nem aprovado**. Jarvis só marca `FROZEN` após revisão independente final, aprovação humana explícita e registro da referência no contrato/índice. Alterações depois do freeze exigem Change Request.
