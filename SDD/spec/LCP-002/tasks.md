# LCP-002 — Tarefas e ownership

**Execution mode:** SINGLE_WRITER
**Risk track:** CRITICAL
**Contract state:** DRAFT v2 — implementação bloqueada
**Dependência:** LCP-001 / PR #26 integrado à `main` em `770ade0`; branch sincronizada. **Bloqueio restante:** aprovação humana da v2.

## Ownership e ordem

| ID | Responsável principal | Trabalho | Dependência | Evidência |
| --- | --- | --- | --- | --- |
| P-01 | Jarvis | Validar dependência, coletar aprovação, fixar versão do contrato e registrar Spec no índice | PR #26 | Aprovação rastreável |
| T-01 | Maquiavel | Configuração PostgreSQL/Compose, SQLAlchemy, sessões e Alembic sem `create_all` | P-01 | Migração em banco vazio |
| T-02 | Maquiavel | Tabelas, FKs compostas, triggers diferidos, snapshot canônico/Decimal e mapeamento Pydantic | T-01 | Testes de round-trip/constraints |
| T-03 | Maquiavel | Repositórios transacionais, política/evidências referenciais e transições CAS de runs | T-02 | Persistência, conflitos, rollback |
| T-04 | Maquiavel | Testes de integração DB-01..DB-19, CI PostgreSQL, exemplo seguro de configuração | T-03 | CI e logs reproduzíveis |
| V-01 | Mefisto | Inspeção independente do diff, migrations, segurança, observabilidade e regressões | T-04 | `validation-result.md` e `review.md` |
| C-01 | Jarvis | Atualizar índice e preparar handoff para revisão humana; não fazer merge | V-01 | PR e resumo de riscos |

**Aviso:** esta v2 adiciona gatilhos e `policy_versions` mínimos; são parte do contrato de persistência, não autorização para implementar o Policy Engine.

**Van Gogh:** sem tarefa nesta fase (sem frontend, sem segundo writer).

## Allowed paths (somente após freeze)

- `backend/app/db/**`, `backend/app/repositories/**`, `backend/app/services/**`
- `backend/alembic/**`, `backend/alembic.ini`
- `backend/requirements.txt`, `backend/requirements-dev.txt`
- `backend/tests/**`, `backend/app/main.py` (somente wiring mínimo/health)
- `backend/Dockerfile`, `docker-compose.yml`, `.env.example`
- `.github/workflows/ci.yml`
- `SDD/spec/LCP-002/**`, `SDD/index.md`

## Protected/out of scope

- `backend/app/domain/**` — contratos da LCP-001 só mudam mediante Change Request.
- `README.md`, `frontend/**`, `.codex/**`, `.agents/**`, `AGENTS.md`, `SDD/rules.md` — não alterar.
- `.env`, segredos, dados reais, workflows de deploy, código de terceiros; não executar `docker compose down -v` contra volume não descartável.

## Handoff de implementação

Maquiavel entrega lista dos arquivos, decisões, comandos efetivamente executados com resultados, riscos e referências de PR. Mefisto não confia apenas nesse resumo: inspeciona commit e produz evidência independente. Se faltarem permissões/ferramentas, marcar NOT_RUN ou BLOCKED, sem resultados simulados.

## Change Request

Mudança de esquema acordado, tipo de ID, domínio, auth, API, migration potencialmente destrutiva ou allowed paths: **parar**. Documentar motivo, impacto e plano de testes; Jarvis devolve contrato para DRAFT e requer novo gate humano.
