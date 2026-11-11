# MVP — Motor determinístico de comparação

**Issue:** #33 · **Branch:** `feat/lcp-mvp-response-core`
**Owner:** Maquiavel · **Track:** STANDARD · **Modo:** SINGLE_WRITER
**Status:** implementação autorizada, aguardando Codex

## Instrução para Codex

Leia `AGENTS.md`, `SDD/rules.md` e [Issue #33](https://github.com/CarlosVLemos/Lab-Control-Panel/issues/33) completa. **Implemente código e testes**, sem reabrir discussão teórica sobre schema, migrations ou segurança enterprise.

**Pode editar:** `backend/app/workloads/**`, `backend/app/evaluation/**`, `backend/app/demo/**`, `backend/tests/test_mvp_response*.py`, este arquivo. **Não** alterar SQLAlchemy, Alembic, repositórios, domínio Pydantic, FastAPI main, CI, Compose, frontend ou SDD.

## Recorte do MVP

Fixture versionada com >=5 inputs sintéticos e ground truth; duas implementações determinísticas de classificação de intenção; avaliador de igualdade exata da etiqueta; relatório JSON do contrato da Issue #33. Os números de resumo precisam ser derivados das saídas de cada case. Sem chamadas de LLM, rede, banco, worker ou provedor externo.

Adote funções pequenas e tipos explícitos. Resultados e erros devem ser serializáveis, e erro/ausência de saída nunca vira aprovação. Preserve IDs e a ordem dos casos. Não adicionar frameworks.

## Verificação

`cd backend && python -m pytest -q backend/tests/test_mvp_response_core.py` pode precisar de ajuste relativo ao diretório: documentar o comando efetivamente usado. Rodar testes próprios sem PostgreSQL e, se o ambiente permitir, a suíte anterior, sem afirmar PASS para checks não executados.

## Handoff

Publicar PR Draft contra main com fixtures, exemplos de relatório JSON, testes reais e limitações. Sem merge. Não depende da LCP-002 para o núcleo puro; integração API/DB será tarefa posterior.
