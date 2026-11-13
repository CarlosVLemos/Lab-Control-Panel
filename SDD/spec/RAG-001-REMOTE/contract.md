# RAG-001-REMOTE — contrato MVP v2

**Estado:** FROZEN MVP v2 · **FROZEN por humano:** aprovado em 2026-11-13 ([registro na PR #46](https://github.com/CarlosVLemos/Lab-Control-Panel/pull/46#issuecomment-6853766192)) · **Issue:** #45 · **Escopo:** executor CLI experimental, não serviço de produção.

## 1. Experimento e integridade

- Fonte versionada: `backend/app/evaluation/rag.py`; fingerprint esperado `af2f2af7a4ceddba16f7caff52b3b85ef30862fc12aaa716c3e0255b84d827f5`.
- Manifesto: [pilot-manifest.json](pilot-manifest.json), SHA-256 JSON canônico (`sort_keys=True`, `ensure_ascii=False`, separadores `,`/`:`): `cee86695ba30718b6eef0ed378c04a24507ad3077d7801e9005d97eea51e0244`. Ordem **rag-03, rag-19, rag-21, rag-26, rag-27, rag-32**; 2 braços e 1 repetição. No startup, validar hashes, ordem, categorias e seleção; se houver divergência, **BLOCKED sem rede**. Alterar dataset exige novo registro/versão antes de observar resultados.
- `NO_CONTEXT`: mesmo prompt base e pergunta, **sem documentos, IDs, texto das políticas, gabarito ou metadados**. `SEMANTIC_RAG`: mesmo envelope com até 3 documentos recuperados, identificados e delimitados como **dados não confiáveis**, nunca instruções. Não vazar `expected_answer`, `expected_sources`, `expected_facts` ou rubrica para geração. Não ativar ferramentas web/externas.
- Mesmo modelo, prompt-base, formato, esforço de raciocínio, limite de saída e ordem pré-registrada nos dois braços; somente contexto difere. O prompt base **não deve exigir fontes externas como condição de resposta para NO_CONTEXT**, pois isso tornaria a comparação trivial. Deve permitir responder ou admitir incerteza, **sem inventar**.
- Embeddings: `text-embedding-3-small`; construir índice na memória uma vez para o corpus, busca cosseno top-k=3 e embeddings de consulta no braço RAG. Cache em memória durante a execução, identificado por hash do texto/modelo/versão; **sem persistir vetores** neste MVP.

## 2. Runtime mínimo e provedor

- Python com interfaces injetáveis `EmbeddingClient` e `GenerationClient`, usando SDK OpenAI opcional via Responses API. Modelo proposto `gpt-6-luna`, `reasoning.effort=none`, `max_output_tokens=1024`, `store=false`, tier `Standard` e schema de resposta `{answer:string, abstained:boolean, citations:string[]}`. **Verificar acesso e compatibilidade na conta sem gerar resposta paga, se possível; indisponibilidade => BLOCKED, sem fallback automático**.
- CLI: `--dry-run` é padrão e **não instancia cliente com rede**. Modo real requer `--execute --max-usd X --max-generation-calls 12 --max-embedding-requests N` e consentimento financeiro separado. Sem segredo na linha de comando; chave lida somente do ambiente. Sem paralelismo nem repetição automática.
- Criar SDK com **`max_retries=0`**, inclusive geração, embeddings e `with_options`. Timeout, limite/erro do provedor ou usage desconhecido não geram nova tentativa: estado **INCONCLUSIVE**, reserva financeira conservada, execução interrompida. Não registrar exceções cruas.

## 3. Controle de custos pequeno, porém real

- O limite é **local para custo estimado**, **não** teto da cobrança da OpenAI. Antes de **cada** envio (incluindo embeddings) validar limite de quantidade, preço, região, tier e reserva; falhar fechado se não houver informação suficiente.
- Primeira versão aceita **somente Standard, sem processamento regional tarifado e entrada curta**: `max_input_tokens_bound=8192` para geração, `max_embedding_input_tokens_bound=8192` por requisição e `max_output_tokens=1024`. Se não for possível estabelecer **limite superior confiável de tokens incluindo overhead**, bloquear; estimativa por palavras não basta.
- Snapshot de preços com URL, data UTC, modelo, região, tier e categorias de entrada/cache/escrita/saída/embedding; revalidar antes do piloto. Reserva com `Decimal`, pior preço aplicável (sem pressupor cache-hit) × limite superior de tokens, mais taxa/margem documentadas. Valor ausente, multiplicador desconhecido, tier diferente, regional, long-context ou configuração não permitida => **BLOCKED sem envio**. Se o provedor devolver tier divergente, marcar **INCONCLUSIVE** e interromper.
- Validar os bloqueios em testes de limites 8191/8192/8193, 271999/272000/272001, multiplicadores long-context (2× entrada e 1,5× saída), adicional regional de 10%, cache, preço ausente e orçamento insuficiente. Esses modos **não serão implementados** no MVP: apenas verificar que não são executáveis. Retry só em versão futura com nova reserva explícita. Usage incerto não significa gasto zero.

## 4. Artefatos, segurança e avaliação

- Persistir **um JSONL sanitizado de tentativas** e um **relatório resumido** em Markdown/JSON, ambos locais. Campos suficientes: run_id, dataset/manifest hash, caso, braço, documentos recuperados, modelo/configuração, resposta visível, citações, status/erro allowlisted, tokens de entrada/saída/cached quando informados, latência em ms, custo **estimado**, timestamp e versão de preço. `null` = não observado, nunca zero artificial.
- Nada de headers, chave, `repr(exc)`, traceback, objetos SDK, prompts brutos ou request/response brutos. Teste com sentinela injetada em exceção, request e provider assegura ausência nos **bytes** de JSONL/Markdown/JSON e stdout/stderr. Qualquer formato de exportação adicional fica fora do MVP.
- Os artefatos podem ser publicados no repositório **apenas após sanitização e checagem manual** e desde que contenham somente corpus/perguntas fictícios. Debug local fica em diretório gitignored e é apagado após validação; não há agendador de retenção nem armazenamento de produção.
- Rubrica humana **antes das execuções**: correção factual **0=incorreta, 1=parcial, 2=correta**; marcar também **abstenção apropriada / negativa fundamentada / recusa segura / erro**, inclusive caso `rag-32`. O avaliador recebe pergunta, resposta e políticas-gabarito, mas não o braço nem custos. Citações são validadas **separadamente** somente para braço que recebeu contexto; não penalizar o NO_CONTEXT por não citar documento que não recebeu. Um revisor é suficiente no piloto; registrar viés possível e divergências sem inventar segundo juiz.
- `retrieval_recall_at_3` mede recuperação dos documentos esperados nos casos respondíveis. `semantic_correctness` permanece `NOT_EVALUATED` até revisão humana; `facts_match` (autodeclaração estruturada) não comprova verdade. Recusa/negação segura ≠ ausência de conhecimento. Erros não somem do denominador; **nenhum vencedor automático**.

## 5. Limites do trabalho e gates

**Implementação futura, somente após FROZEN:** `backend/app/evaluation/rag_remote*.py`, `backend/tests/test_rag_remote*.py`, `docs/evidence/rag-001-*`. Não tocar HTTP, frontend, migrações, banco, Docker, runners Code, nem instalar serviços novos. Testes da CI **offline**.

**Estado atual:** contrato em DRAFT; runtime e chamadas remotas NÃO EXECUTADOS. **A aprovação de FROZEN não é autorização de merge nem de gasto**. Acesso ao modelo, preço/tier/região e orçamento devem ser confirmados antes da execução real.
