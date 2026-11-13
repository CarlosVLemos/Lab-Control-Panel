# Spec: RAG-001-REMOTE — avaliação pareada com execução remota

**Estado:** draft; nenhuma implementação autorizada. **Issue:** [#45](https://github.com/CarlosVLemos/Lab-Control-Panel/issues/45); experimento-mãe [#43](https://github.com/CarlosVLemos/Lab-Control-Panel/issues/43). **Owner:** Jarvis; implementação futura: Maquiavel; revisão independente: Mefisto. **Modo:** SINGLE_WRITER.

## Problema e hipótese

O LCP já possui o corpus fictício e o avaliador RAG-001 offline integrados na PR #44. Ainda não mede respostas de um modelo real. Hipótese a testar, não conclusão: contexto recuperado melhora respostas fundamentadas e reduz respostas não sustentadas, a algum custo de latência/tokens. A fundação offline não valida qualidade semântica.

## Escopo desta PR

Somente especificação, contrato e plano de testes para adaptador remoto. Nenhuma chamada de IA, criação de chave, runner, cliente, fixture nova, endpoint ou alteração no produto será implementada nesta PR. Esta documentação só poderá virar `FROZEN` após aprovação humana explícita e revisão independente.

## Escopo de implementação futura (após FROZEN)

- SDK OpenAI de geração via Responses API, modelo candidato `gpt-6-luna` (confirmar acesso na conta), e embeddings `text-embedding-3-small`; clientes injetáveis.
- CLI offline por padrão; opt-in explícito, orçamento estimado, limite de requisições, interrupção segura, registro de usage e falhas.
- Comparação pareada do mesmo conjunto de questões `NO_CONTEXT` vs `SEMANTIC_RAG` (top-k=3), mesmo modelo/configuração e protocolo de resposta.
- Indexação prévia em memória e cache persistente seguro de embeddings versionados; sem banco vetorial.
- Resultado por caso, evidências e comparação sem vencedor automático.

## Piloto pré-registrado

A seleção do piloto está versionada em [pilot-manifest.json](pilot-manifest.json), com lista ordenada `rag-03` (factual vigente), `rag-19` (negação fundamentada), `rag-21` (síntese), `rag-26` (síntese), `rag-27` (informação ausente) e `rag-32` (adversarial por documento). O manifesto referencia o fingerprint do dataset `af2f2af7a4ceddba16f7caff52b3b85ef30862fc12aaa716c3e0255b84d827f5` e tem SHA-256 da serialização canônica `cee86695ba30718b6eef0ed378c04a24507ad3077d7801e9005d97eea51e0244`. **Antes de qualquer envio**, o executor deve recalcular ambos os fingerprints, conferir lista, categorias e os dados congelados dos casos, bloqueando desvios. Mudanças de dataset/manifesto após inspeção de resultados exigem nova versão e aprovação; nunca edição silenciosa. Duas condições por caso, uma tentativa inicial sem retry: **12 gerações**, além de chamadas de embeddings pré-contabilizadas. Repetições completas (36 × 2 × 3) ficam para autorização distinta após análise do piloto.

## Riscos e interpretação

- Custo e credenciais externas; timeout pode consumir tokens apesar de ausência de usage. O SDK deve ser inicializado com `max_retries=0`, preservando **uma** tentativa por request; falha/timeout não dispara reenvio automático. A execução fica limitada aos modos/tier e região explicitamente permitidos, com bloqueio na ausência de limites superiores verificáveis de tokens e preços. Ver [contract.md](contract.md) e testes R-06/R-07/R-15/R-16.
- Vazamento de gabarito ou IDs de fatos no prompt compromete o experimento; vazamento de segredos em logs compromete a segurança. O plano R-10 exige injeção de chave sentinela e verificação de ausência em **todos** os formatos (JSONL, JSON/CSV, Markdown e CLI), inclusive em falhas do SDK.
- O modelo pode responder adequadamente em texto e ainda não produzir os identificadores canônicos esperados. `facts_match` avalia fatos declarados, não a verdade da resposta; `semantic_correctness` inicia `NOT_EVALUATED` e exige avaliação humana cega para conclusão.
- Amostra de 6 casos é piloto de integração, **não evidência de superioridade estatística**; modelo e variação de saída devem ser reportados.
- RAG exige medir `retrieval recall@3` independentemente de correção de geração; referências por doc_id não provam apoio textual às afirmações.

## Não escopo

HTTP, PostgreSQL/Alembic, frontend, Redis, workers, LangChain, pgvector, execução de código de terceiros, deploy, agente autônomo, LLM-as-judge como veredito primário ou geração de dados reais.

## Aceite desta PR

Contrato com parâmetros, isolamento, controle de custo, falhas, auditabilidade e testes completos; revisão independente e decisão humana. **Aprovação de contrato ≠ aprovação de execução paga.**

**Contrato:** [contract.md](contract.md) · **Tarefas:** [tasks.md](tasks.md) · **Testes:** [tests.md](tests.md) · **Manifesto:** [pilot-manifest.json](pilot-manifest.json) · **Aprovação humana:** PENDING.
