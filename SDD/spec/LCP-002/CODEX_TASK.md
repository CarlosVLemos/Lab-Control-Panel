# EXECUTAR AGORA — Codex / Maquiavel — LCP-002

**Branch:** `feat/lcp-002-postgresql-persistence`
**Issue:** https://github.com/CarlosVLemos/Lab-Control-Panel/issues/2
**Contrato:** [MVP v4 FROZEN](contract.md), aprovado em [CR-001](CHANGE_REQUEST-001.md) por orientação do usuário em 2026-11-11.
**Modo:** SINGLE_WRITER

1. Inspecione `git status`, branch, `AGENTS.md`, `SDD/rules.md`, `.agents/skills/lcp-implement-issue/SKILL.md`, LCP-001 em `backend/app/domain/`, `contract.md`, `tasks.md` e `tests.md`.
2. **Implemente agora** T-01..T-04 com a menor solução que cumpra contrato e testes. Sete tabelas, JSONB ordenado, Alembic, SQLAlchemy/UoW, Compose PostgreSQL, fingerprint/Decimal/CAS e pytest real.
3. Não implementar funções SECURITY DEFINER, triggers avançados, K8s, workers, UI, Policy Engine completo ou infraestrutura sem valor à LCP-002. Não alterar domínio Pydantic existente.
4. Rode testes em banco isolado. Corrija defeitos reais e registre comandos/resultados/limitações; se Docker indisponível, deixe testes CI executáveis e marque bloqueios sem inventar resultados.
5. Produza `validation-result.md` e handoff revisável; solicite Mefisto se subagentes reais estiverem disponíveis. **Não faça merge** nem feche Issue.
6. Conte o tempo gasto em implementação, testes, revisão e correções, quando possível, para comparar produtividade com/sem agentes.

**Stop:** dados não descartáveis, segredo, mudança de API pública/contrato de domínio, execução de código hostil ou redesign substancial. Não iniciar outra rodada especulativa de parecer.
