# RAG-001-REMOTE — testes mínimos do MVP

**Estado:** planejados / NOT_RUN (runtime não implementado). **Ambiente:** pytest, clients fakes e transporte HTTP mockado; CI totalmente offline. Revisão: Mefisto.

| Gate | Teste essencial | Aceite |
| --- | --- | --- |
| T1 OFFLINE | Importar CLI sem SDK/rede, rodar dry-run, simular ausência de credencial | **0 requisições** |
| T2 PAREAMENTO | Spy captura envelopes de seis casos nos dois braços | Mesma pergunta/modelo/configuração; só contexto muda; NO_CONTEXT sem corpus/gabarito |
| T3 RECUPERAÇÃO | Embeddings falsos determinísticos, top-k=3, corpus pré-indexado uma vez | IDs previsíveis e recall@3 separado de geração |
| T4 HASH | Recalcular fingerprint e JSON canônico do manifesto, mutar ID, ordem, categoria, pergunta, fato | Drift bloqueia **antes** de cliente remoto |
| T5 ORÇAMENTO | Custo pior caso por `Decimal`, limites 8191/8192/8193 e 271999/272000/272001, região 10%, 2× entrada/1,5× saída, cache, tier desconhecido, preços/usage ausentes | Modos não permitidos ou sem limite superior => **0 envios**; sem número inventado |
| T6 RETRIES | Adaptador OpenAI configurado com `max_retries=0` em geração/embeddings/`with_options`; timeout e 408/409/429/5xx via HTTP mock | **Exatamente 1 envio físico**; INCONCLUSIVE, reserva mantida |
| T7 SEGREDOS | Inserir `sk-test-sentinel` em headers, exceptions, requests e response; serializar erro, JSONL, relatório JSON/Markdown e CLI | Nenhum byte da sentinela em arquivos/stdout/stderr; `error_code` allowlisted |
| T8 RESULTADO | Provider fake retorna sucesso, saída inválida, recusa, informação parcial, usage ausente | JSONL/relatório distinguem `null` de 0; não declaram vencedor; não descartam falhas |
| T9 RUBRICA | Avaliação humana de 0/1/2 e classificação de abstenção, negativa e recusa; casos sem citação | Correção factual não depende de citar, revisão humana marcada separadamente |
| T10 CI | Suíte completa + prova de CLI sem credencial | CI verde, sem segredo nem chamadas pagas |

**Comandos após implementação:** `cd backend && python -m pytest -q tests/test_rag_remote.py tests/test_rag.py` e testes normais da CI. Usar transporte fake para o SDK sem fazer chamada paga. PR de contrato é **somente documentação**, logo runtime continua NOT_RUN.

**Evidência de execução real:** requer aprovação financeira posterior; snapshot de preço/tier/região; acesso válido ao modelo; comando explícito; relatório sanitizado; revisão humana cega. Se qualquer condição falhar: BLOCKED, não PASS.
