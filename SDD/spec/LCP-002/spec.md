# LCP-002 — Persistência PostgreSQL e migrações

**Status:** draft · **Risco:** CRITICAL
**Issue:** https://github.com/CarlosVLemos/Lab-Control-Panel/issues/2
**Branch:** `feat/lcp-002-postgresql-persistence`
**Owners:** Jarvis (coordenação), Maquiavel (único writer/implementação), Mefisto (revisão independente)
**Modo:** SINGLE_WRITER
**Aprovação humana:** PENDING
**Contrato:** `contract.md` — **DRAFT v3**, NÃO FROZEN
**Revisão precedente:** `NEEDS_REVISION` pelo Codex; pontos corrigidos no planejamento, mas ainda não validados em banco.

## Dependências e limites

LCP-001 / PR #26 está integrado à `main` no commit `770ade0`; a branch LCP-002 contém os contratos Pydantic. Ler `AGENTS.md`, `SDD/rules.md`, `docs/PROJECT_SPEC.md`, `docs/ARCHITECTURE.md`, `backend/app/domain/`, `tests.md` e `contract.md`.

A liberação de Maquiavel **não ocorreu**: nenhuma migração/implementação deve começar enquanto a v3 não for revisada, aprovada explicitamente pelo usuário e marcada FROZEN por Jarvis. Somente após a aprovação humana, executar T-01..T-04.

## Objetivo e resultado mensurável

Persistir Projects, versões de datasets com cases, candidatos, experimentos, runs, avaliações e decisões, mantendo estabilidade de fingerprint, pertença de projeto e imutabilidade de conjuntos depois do commit. PostgreSQL e Alembic são a fonte persistente, não memória da API.

**Entregas:** DDL versionada, FKs compostas, funções de criação atômica de aggregates com ACL, snapshots imutáveis, CAS de runs, UoW/repositórios, Compose PostgreSQL e testes reais com papel de aplicação/CI.

## Regras centrais da v3

1. Fronteiras transacionais: funções SECURITY DEFINER criam dataset+cases, experiment+participantes, decision+evaluation links num único agregado; `lcp_app` não tem DML direto nesses conjuntos.
2. `experiment_candidates.ordinal` preserva tupla ordenada de challengers, exclui baseline (ordinal NULL). DatasetVersion tem >=1 caso e ordinais 0..N-1.
3. `candidate_versions.project_id` tem FK direta; FKs compostas protegem run/case/baseline/projeto/workload; FK diferida de baseline permanece.
4. Run inicia `QUEUED, revision=0` e só muda por transição CAS, sem alteração lateral de métricas ou timestamps.
5. JSONB Decimal em strings; custo NUMERIC sem escala fixa porém finito; arrays evidência sem valores vazios/null.
6. `PolicyDecision.evaluation_ids` mantém duplicatas como na LCP-001, com PK(decision_id,ordinal). `policy_versions` não tem fingerprint na LCP-002.
7. Proveniência e hashes têm garantias limitadas: origem declarada, evidências externas opacas, privilégios de DB não substituem assinatura criptográfica.

## Critérios de aceite

DB-01..DB-19 + AGG-A/B/C + SEC-A/STATE-A em `tests.md`, incluindo testes de segunda sessão com `lcp_app`, migrações PostgreSQL reais, persistência pós-restart, validação independente e ausência de regressões em `/health`.

## Fora de escopo

Fila/worker RQ/Redis, API CRUD pública, frontend, execução de código de terceiros, deploy, autenticação multi-tenant, promoção/release, alteração de domínio LCP-001 sem Change Request, modificações em README, dados reais e merge automático.

## Trade-offs e gate

A fronteira única de escrita evita triggers de contagem por cada associação, mas exige funções seguras e teste de privilégios reais. `SECURITY DEFINER` sem search_path/ACL correto é um risco. Nenhum CI de documentação substitui teste PostgreSQL. Se Mefisto achar novo bloqueio, permanecer em DRAFT e abrir uma revisão dirigida, não introduzir novas abstrações por especulação.

**Próximo passo:** revisão final curta da v3 pelo Codex, registro do parecer, aprovação humana explícita e freeze documentado. Somente então Maquiavel implementa.
