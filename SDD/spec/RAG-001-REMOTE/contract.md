# Contract v1 — RAG-001-REMOTE

**Estado:** DRAFT — NÃO FROZEN. **Aprovado por:** PENDING. **Evidência da aprovação:** PENDING. Qualquer alteração relevante após o freeze requer Change Request.

## Invariantes de comparação

- Fonte da verdade: `backend/app/evaluation/rag.py` versionado; corpus, perguntas, fatos e rubrica com fingerprint calculado e persistido. Fingerprint offline de referência da PR #44: `af2f2af7a4ceddba16f7caff52b3b85ef30862fc12aaa716c3e0255b84d827f5`; **verificar novamente** o hash no SHA da implementação; o hash somente identifica entradas, não prova procedência assinada.
- Condições `NO_CONTEXT` e `SEMANTIC_RAG` executam as **mesmas perguntas** com o mesmo modelo, versão/snapshot quando disponível, system prompt base, esforço de raciocínio, esquema de saída e limite de tokens. O único tratamento variável é a disponibilização de contexto recuperado. A ordem de execução deve ser determinística ou randomizada com seed pré-registrada e registrada, evitando efeito de ordem sem inventar capacidade de fixar sampling seed na API.
- Não incluir perguntas de teste, expected_answer, expected_facts, expected_sources, rubrica, resultados anteriores ou dados da outra condição nos prompts. `NO_CONTEXT` recebe apenas prompt base e pergunta; não recebe texto, ID nem metadados do corpus.
- `SEMANTIC_RAG` busca top-k=3 via embeddings (mesmo modelo/versão do índice e da consulta) e recebe exclusivamente `doc_id`, versão e texto dos documentos encontrados, explicitamente delimitados como conteúdo não confiável; contexto não é instrução do sistema. Nenhum tool call externo/busca web é habilitado no gerador.
- Prompt deve pedir abstenção quando não houver fundamento suficiente; mesma instrução para ambos. Saída estruturada sugerida pela Responses API `text.format=json_schema` estrito: objeto `{answer:string, abstained:boolean, citations:string[]}`; nenhum ID de fato oculto é fornecido. Confirmar suporte real do modelo antes de congelar o schema.
- Modelo inicial proposto: `gpt-6-luna` via Responses, `reasoning.effort=none` (suportado na documentação), `max_output_tokens=1024` (inclui tokens de raciocínio), `store=false`, processing `Standard`, sem temperature/seed caso não suportados. Nenhum fallback silencioso de modelo, esforço ou tier; abortar com `BLOCKED` se parâmetros indisponíveis. Registrar modelo efetivamente retornado e service tier real.
- Embeddings: `text-embedding-3-small`, input de documentos e consultas; indexação em memória, cosseno, sem vetor persistido fora do cache explicitamente autorizado. Cache indexado por hash do conteúdo UTF-8, doc_id/versão, modelo e dimensões; conteúdo alterado invalida cache. O custo de indexação é contabilizado separadamente do custo de embedding de consultas.

## Interface e isolamento

- Interfaces Python injetáveis `EmbeddingClient.embed_batch(texts)` e `GenerationClient.generate(request)`; SDK importado apenas no adaptador opcional.
- CLI por padrão `--dry-run` offline, sem import/criação de cliente real. Execução real somente com combinação `--execute`, `--max-usd`, `--max-generation-calls` e `--max-embedding-requests`; exigir aprovação operacional separada, incluindo valor nominal do orçamento.
- Chave **somente** de variável de ambiente local, nunca commit, logs, relatório, argumentos de linha de comando ou resultados. Não persistir corpo de request contendo segredos; políticas são fictícias, mas metadados de prompt precisam de controle.
- Somente uma execução por vez na primeira versão. Sem paralelismo e sem retries automáticos na geração/embeddings; um timeout com estado de cobrança incerto deve interromper a execução e marcar `INCONCLUSIVE`, reservando seu custo máximo possível.

## Orçamento e precificação

- O teto é um **limite conservador de custo estimado no executor**, não hard cap da fatura do provedor. Antes de cada requisição, reservar custo máximo conservador: (limite superior de tokens de entrada × tarifa normal de entrada + `max_output_tokens` × tarifa normal de saída), mais overhead/margem explicitamente documentados; para embeddings, reservar por quantidade máxima estimada de tokens de todos os textos do lote. Contar todos os requests (inclusive indexação/consulta), não apenas as 12 gerações. Em insuficiência de reserva: **bloquear antes do envio**.
- Uso prévio da conta, outras aplicações, surcharges, timeouts e cobrança após falha podem exceder o executor; não alegar limite financeiro global. Guardar reserva para tentativas sem usage, não reinterpretar como custo real 0. Nenhuma repetição/retentativa que ultrapasse limites autorizados.
- Fonte tarifária (verificada 2026-11-13): https://developers.openai.com/api/docs/models/gpt-6-luna — Standard **US$0.10/M** entrada, **US$0.01/M** entrada em cache, **US$0.125/M** escrita de cache quando aplicável, **US$0.50/M** saída; https://developers.openai.com/api/docs/models/text-embedding-3-small — **US$0.02/M** tokens de entrada. Não pressupor descontos de cache na reserva; contemplar cobrança por escrita de cache e eventuais multiplicadores/tier quando aplicáveis, sempre com snapshot explícito da modalidade. Revalidar preços/tier no dia do piloto; snapshot tarifário com UTC/data e URL. Considerar taxas adicionais e modo regional se aplicáveis.
- Tokens de saída incluem reasoning tokens; respeitar `max_output_tokens` e tratar `incomplete`/refusal como não pontuável. Se não houver contagem confiável de input pré-envio, implementar estimativa conservadora comprovada nos testes ou fail-closed; não assumir quantidade de tokens proporcional ao número de palavras como limite rígido.

## Contrato de registros

Cada tentativa, inclusive falha, produz JSONL validado e versão de schema. Campos mínimos: `experiment_id`, `dataset_sha256`, `code_sha`, `arm`, `case_id`, `attempt`, `prompt_sha256`, `retrieval_config`, `retrieved_docs[{id,version,sha256}]`, `provider/model_requested/model_reported`, `reasoning_effort`, `max_output_tokens`, `response_id` (quando houver), `status` (COMPLETED/FAILED/BLOCKED/INCONCLUSIVE), timestamps UTC, `latency_ms` medida monotonicamente, contadores `input_tokens`, `cached_input_tokens`, `output_tokens`, `reasoning_output_tokens`, custo **estimated_usd** por componente, snapshot tarifa e `error_code` sanitizado. Embeddings registram usage separadamente.
- `null` significa não observado, nunca 0. Não registrar raciocínio privado. Registrar resposta visível (fictícia) e citações em artefato auditável, se explicitamente autorizado; revisão humana deve ocultar arm/modelo para reduzir viés.
- `retrieval_recall_at_3`: |fontes esperadas recuperadas| / |fontes esperadas| somente para perguntas respondíveis em RAG. Casos sem fontes esperadas: N/A. Métricas `expected_sources_present` e `citations_match_expected` são evidências de IDs, não prova semântica. `semantic_correctness` inicialmente `NOT_EVALUATED`; nunca usar `facts_match` como substituto.
- Artefatos da avaliação real: JSONL bruto sanitizado + JSON/CSV agregados e relatório Markdown, com denominadores incluindo erros e avisos de dados faltantes; sem ranking automático ou promoção quando inconclusivo.

## Fronteiras

**Permitido após FROZEN:** `backend/app/evaluation/rag_remote*.py`, `backend/tests/test_rag_remote*.py`, `docs/evidence/rag-001-*`, ajustes estritamente necessários à interface interna `rag.py` após Change Request se quebrar contrato.

**Proibido:** rotas HTTP, frontend, migrations, banco, Docker novo, worker, secret storage, auto-merge, execução de piloto nesta PR. Rollback operacional = desligar `--execute` e voltar ao modo offline, sem dados de produção para migrar.

## Decisões pendentes antes de FROZEN

1. Confirmar modelo `gpt-6-luna` disponível e suporte à configuração desejada na conta de execução (sem testar cobrança nesta fase).
2. Aprovar orçamento apenas em etapa posterior (sugestão provisória US$2, não autorização).
3. Aprovar esquema de resposta visível, método de revisão humana cega e política de retenção de artefatos.
4. Confirmar rigor da reserva de tokens de entrada e tratamento de cobrança incerta.
