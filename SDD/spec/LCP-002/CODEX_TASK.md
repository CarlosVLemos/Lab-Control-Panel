# Handoff Codex — LCP-002 (contrato v2)

**Branch:** `feat/lcp-002-postgresql-persistence`
**Issue:** https://github.com/CarlosVLemos/Lab-Control-Panel/issues/2
**Dependência:** https://github.com/CarlosVLemos/Lab-Control-Panel/pull/26
**Status:** DRAFT v2 / PENDING (PR #26 integrado; não executar implementação até aprovação)

## Instrução para Jarvis

Confirme que o PR #26 foi integrado na `main` em `770ade0` e que os modelos Pydantic estão nesta branch.  Leia `AGENTS.md`, `SDD/rules.md`, `.agents/skills/lcp-implement-issue/SKILL.md`, `docs/PROJECT_SPEC.md`, `docs/ARCHITECTURE.md` e todos os arquivos `SDD/spec/LCP-002/`. Use o checklist abaixo.

- Dependência integrada? Branch contém os contratos Pydantic exatos? **Se não, pare.**
- Contrato v2 aprovado pelo humano e marcado `FROZEN`, com referência? **Se não, somente revise e reporte; não implemente.**
- Sem conflitos entre esquema, domínios e tests.md? Se houver, proponha Change Request, sem alterar contrato silenciosamente.

## Instrução para Maquiavel (somente depois do freeze)

Execute `SINGLE_WRITER`; implemente apenas os paths permitidos em `tasks.md`. Respeite FKs compostas, baseline como participante, atomicidade, triggers append-only, checks completos de status/timestamp, Decimal/JSONB string, snapshot canônico e constraints de política. Migrações SQL somente em banco isolado/descartável; não atualizar `backend/app/domain/**` nem `README.md`.

Implemente testes executáveis DB-01..DB-19, documente comandos/exit codes/resultados reais e prepare PR de implementação contra a branch de planejamento aprovada (ou decisão explícita de Jarvis sobre a base). Nunca force alterações em `main`.

## Instrução para Mefisto

Use `.agents/skills/lcp-review-change/SKILL.md` e `tests.md`; revise independentemente diff, FKs, trigger deferral, precisão, proveniência, falhas de concorrência e logs. Registre evidência em `validation-result.md` e veredito em `review.md`. Evidência ausente = `NOT_RUN`/`blocked`, não `PASS`.

**Stop conditions:** regressão/ausência dos contratos LCP-001; contrato não FROZEN; alteração de limites de segurança; migração destrutiva não autorizada; dados reais; scope drift; SQL externo não confiável.
