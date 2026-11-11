# ADR-002 — Avaliação por evidências e decisão fail-closed

**Status:** Accepted · **Escopo:** MVP

## Contexto

Um score único ou um LLM avaliando a própria resposta não fornece garantias suficientes para aprovar código ou uma versão em serviço. Métricas ausentes podem parecer zero ou sucesso quando não são.

## Decisão

- Separar EvaluationResult (observação por avaliador) de PolicyDecision (regra aplicada).
- Vereditos: PASS, FAIL, INCONCLUSIVE, MANUAL_REVIEW.
- PASS exige ao menos uma evidência e uma avaliação vinculada; falhas críticas impedem PASS.
- Um processo não pode promover automaticamente INCONCLUSIVE ou MANUAL_REVIEW.
- Registrar versão da política, IDs das avaliações, origem das evidências e justificativa.

## Consequências

Menos falsos positivos e decisões auditáveis, ao custo de mais casos inconclusivos. As condições completas de promoção e seus limiares serão implementadas pelo Policy Engine (LCP-008), não pelos modelos de dados.
