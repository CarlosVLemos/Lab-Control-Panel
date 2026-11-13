# Independent Test Plan — RAG-001-REMOTE

**Owner:** Mefisto (papel de revisão). **Versão do contrato:** DRAFT v1. **Ambiente:** Python 3.12+, fakes locais; CI sem rede/provedor, credenciais ou cobrança.

| ID | Invariante | Verificação futura | Evidência |
| --- | --- | --- | --- |
| R-01 | Import e CLI `--dry-run` não constroem SDK nem fazem rede | Fake cliente que falha se chamado; `python -m pytest -q backend/tests/test_rag_remote.py` | 0 chamadas observadas |
| R-02 | Sem `--execute` + limites completos, CLI recusa execução | Parametrização de combinações faltantes/invalidas | Falha antes do cliente |
| R-03 | NO_CONTEXT nunca recebe documentos, doc IDs, fatos nem gabarito | Spy requests serializados contra corpus/gabarito | Ausência comprovada |
| R-04 | SEMANTIC_RAG só recebe top-k=3 do índice congelado | Vetores mock + spy; versões/ordem | IDs e hashes determinísticos |
| R-05 | Duas estratégias usam mesmas perguntas, modelo, prompt base e formato | Comparação de envelopes pareados | Diferença só na variável de contexto |
| R-06 | Reserva cobre apenas modos permitidos e pior caso, com multiplicadores/region/tier explicitamente fechados | Parametrizar input 271999/272000/272001; limites locais 8191/8192/8193; 2× entrada/cache, 1,5× saída, sobretaxa regional 10%, cache-write, tier/mode desconhecido, preços indisponíveis, usage ausente, budget esgotado | Zero envios em qualquer cenário não permitido; custo máximo coerente no cenário permitido |
| R-07 | SDK real configurado sem retry automático; timeout não duplica tentativa física | Construir adaptador SDK instrumentado/transport fake e inspecionar `max_retries=0` no cliente e nas chamadas de geração e embeddings; injetar timeout, 408/409/429/5xx e validar **exatamente 1 envio**, sem retry/with_options que restabeleça default | Estado INCONCLUSIVE, reserva total preservada, contagem = 1 |
| R-08 | Limites de 12 gerações e de embeddings incluem cada tentativa, nunca são ultrapassados | Contador fake em indexação e consultas | Contagens observadas ≤ limites |
| R-09 | Cache por hash/modelo/versão invalida mudança de documento | Fake vector de dimensão inválida, cache antigo e documento alterado | Invalidação/erro |
| R-10 | Serialização segura, null ≠ zero e erros sanitizados | Injetar `sk-test-sentinel` e segredo arbitrário em exception, HTTP headers, request, response e metadados; produzir JSONL, JSON, CSV, Markdown e CLI; varrer bytes completos e campo a campo; permitir apenas `error_code` allowlisted; verificar null/zero, custo separado, fake clock monotônico | Nenhum segredo em **qualquer** artefato ou stdout/stderr; `repr(exc)` não serializado |
| R-11 | `semantic_correctness` é NOT_EVALUATED sem revisão cega; métricas de retrieval separadas | Casos correct/incorrect/missing/adversarial | Nenhum vencedor sem evidência |
| R-12 | CI não usa OPENAI_API_KEY nem executa chamadas pagas | Job sem segredo, spy impossibilitando rede | Log da CI |
| R-13 | Recusa/refusal e saída JSON inválida/incompleta são tratadas como não pontuáveis | Respostas provider mockadas | Erros auditáveis, sem fallback sintético |
| R-14 | Seleção do piloto é a lista pré-registrada e imutável (6 casos, 2 braços) | Recalcular fingerprint do dataset e checksum da serialização canônica de `pilot-manifest.json`, verificar IDs ordenados, categorias, fontes, facts, adversarial, perguntas; adulterar um campo por vez | Divergência aborta antes de embeddings, cliente remoto ou geração |
| R-15 | Multiplicadores e modo/tier de execução não degradam silenciosamente o orçamento | Tabela local fixada de preços worst-case e provider fake retornando tier inesperado; observar reserva pré-chamada e tratamento após resposta | Tier inesperado => INCONCLUSIVE, nenhuma próxima chamada; preço/tier desconhecido antes => BLOCKED |
| R-16 | Inexistência de limite superior confiável de tokens obriga bloqueio | Mock de tokenizador aproximado, corpus longo e request sem garantia de limite | Zero requests e erro CONFIG_BLOCKED; não tratar aproximação como limite seguro |

**Comandos a executar somente após FROZEN e implementação:** `cd backend && python -m pytest -q tests/test_rag_remote.py tests/test_rag.py` e suíte completa CI do backend. **Estado atual:** NOT_RUN — runtime não implementado.

### Revisão não automatizada

- Verificar isoladamente o snapshot de preços e a disponibilidade do modelo no dia da execução.
- Revisão cega por caso do conteúdo textual, não apenas dos fatos auto-reportados.
- Verificar os seis casos pré-congelados pelo manifesto `pilot-manifest.json`, SHA-256 canônico `cee86695ba30718b6eef0ed378c04a24507ad3077d7801e9005d97eea51e0244`, corpus source blob SHA `fcbf1d0b9a46ee8aab7131a65cf5238295f84e5c`, fingerprint `af2f2af7a4ceddba16f7caff52b3b85ef30862fc12aaa716c3e0255b84d827f5`, IDs ordenados e campos relevantes. Nenhuma mutação após medir saídas.
- Inspeção manual de logs, privacidade, comandos, pin do SDK e orçamento do operador.
- Testar defesa de prompt injection vindo **de documentos**, não apenas de perguntas do usuário.

**Regra:** CI verde para fakes não significa autorização de cobrança nem performance real. Aprovação para piloto exige segundo consentimento explícito.

### Evidência atual da revisão de contrato

- Arquivos Markdown e manifesto JSON apenas; suíte do runtime permanece `NOT_RUN`, porque o adaptador ainda não foi implementado.
- Revisão de contrato pode checar manualmente a presença de exigências R-06, R-07, R-10, R-14, R-15 e R-16, mas isso **não** é evidência de que o código futuro já aplica os controles.
- Proibido pedir credencial ou rodar API paga para demonstrar conformidade de contrato.
