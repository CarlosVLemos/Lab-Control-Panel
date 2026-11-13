# RAG-001-REMOTE — tarefas de implementação do MVP

**Track:** CRITICAL por credenciais/limite financeiro. **Modo:** SINGLE_WRITER. **Contrato:** FROZEN MVP v2 — implementação Python offline autorizada em branch separada; chamadas pagas e merge não autorizados.

| Fase | Entrega | Evidência / gate |
| --- | --- | --- |
| 0. Contrato | Spec + manifesto + plano curto de testes; revisão Mefisto | PR #46, decisão humana FROZEN |
| 1. Runner offline | CLI `--dry-run`, pareamento, hash, retrieval mock, registro mínimo | T1–T4 + CI offline |
| 2. Adaptador seguro | OpenAI opcional, `max_retries=0`, limite de chamadas/custo, sanitação | T5–T7 + CI offline; sem chamadas reais |
| 3. Resultado auditável | JSONL e resumo Markdown/JSON, rubrica humana cega, limites explícitos | T8–T10, revisão independente |
| 4. Piloto | 6 × 2 gerações, embeddings contados; relatório observado | **Autorização financeira separada**, acesso/tarifa revalidados; operador inicia manualmente |

**Não implementar:** novo frontend, banco/endpoint/worker, filas, dashboard novo, dois avaliadores, LLM-as-judge, storage privado e agendador de retenção. O frontend já existente poderá importar relatórios numa fase futura.

**Fronteiras:** após FROZEN editar apenas `backend/app/evaluation/rag_remote*.py`, `backend/tests/test_rag_remote*.py`, `docs/evidence/rag-001-*`; mudanças no contrato de `rag.py` requerem CR. PR de runtime separada da PR #46. Sem merge automático.

**Handoff:** perfis Jarvis/Maquiavel/Mefisto são responsabilidades, não subagentes automaticamente executados. Nenhum teste de runtime, crédito API ou prompt real foi executado no estado atual.
