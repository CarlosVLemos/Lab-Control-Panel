# Handoff Codex — LCP-002 (contrato DRAFT v3)

Repositório: `CarlosVLemos/Lab-Control-Panel`
Branch: `feat/lcp-002-postgresql-persistence`
Issue: https://github.com/CarlosVLemos/Lab-Control-Panel/issues/2
Dependência LCP-001: resolvida (`770ade0`)
**Status:** DRAFT v3 / aprovação PENDING / implementação BLOCKED

## Agora: revisão final — não implementar

Jarvis lê `AGENTS.md`, `SDD/rules.md`, a Skill `.agents/skills/lcp-implement-issue/SKILL.md`, os modelos da LCP-001 e todos os documentos em `SDD/spec/LCP-002/`.

Concentre a revisão **somente** em invariantes observáveis:
- Após COMMIT, `lcp_app` consegue alterar casos/participantes/evaluation links? As funções transacionais + REVOKE impedem?
- `Experiment.candidate_ids` e `PolicyDecision.evaluation_ids` reconstruídos na ordem e com repetições previstas pela LCP-001?
- O papel SECURITY DEFINER foi projetado com privilégios mínimos, search_path seguro e sem janela de EXECUTE PUBLIC?
- Run nasceu QUEUED/revision 0, `started_at` imutável, e CAS é a única escrita de UPDATE pelo app?
- DB-07/09/10/15/17/18/19 e AGG-A/B/C, SEC-A, STATE-A têm testes realistas e reproduzíveis?

**Entregar `READY_TO_FREEZE` ou `NEEDS_REVISION`**, com bloqueios concretos e trade-offs. Não inventar testes executados, não tocar `backend/**`, não instalar pacotes, não executar migrações, não fazer merge e **não marcar FROZEN** por conta própria.

## Depois da aprovação humana explícita

Somente quando `contract.md` trouxer `FROZEN` e referência de aprovação, Maquiavel executa a Skill de implementação em SINGLE_WRITER, respeitando `tasks.md` e o contrato v3. Mefisto inspeciona código e outputs com `lcp-review-change`, sem alegar delegação que não ocorreu. Um PR revisável com evidências é o resultado, não merge automático.

**Stop conditions:** falta de aprovação; contrato divergente da LCP-001; necessidade de alterar `backend/app/domain/**`; comandos destrutivos ou banco real; privilégio do runtime fora do contrato; scope drift.
