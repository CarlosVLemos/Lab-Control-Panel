# Independent Test Plan — RAG-001-REMOTE

**Owner:** Mefisto (papel de revisão). **Versão do contrato:** DRAFT v1. **Ambiente:** Python 3.12+, fakes locais; CI sem rede/provedor, credenciais ou cobrança.

| ID | Invariante | Verificação futura | Evidência |
| --- | --- | --- | --- |
| R-01 | Import e CLI `--dry-run` não constroem SDK nem fazem rede | Fake cliente que falha se chamado; `python -m pytest -q backend/tests/test_rag_remote.py` | 0 chamadas observadas |
| R-02 | Sem `--execute` + limites completos, CLI recusa execução | Parametrização de combinações faltantes/invalidas | Falha antes do cliente |
| R-03 | NO_CONTEXT nunca recebe documentos, doc IDs, fatos nem gabarito | Spy requests serializados contra corpus/gabarito | Ausência comprovada |
| R-04 | SEMANTIC_RAG só recebe top-k=3 do índice congelado | Vetores mock + spy; versões/ordem | IDs e hashes determinísticos |
| R-05 | Duas estratégias usam mesmas perguntas, modelo, prompt base e formato | Comparação de envelopes pareados | Diferença só na variável de contexto |
| R-06 | Orçamento é reservado antes de gerar/embedar e falha fechado | Casos limite, usage ausente, preço ausente, solicitação maior que teto | Nenhuma requisição ao exceder teto |
| R-07 | Timeout, erro 429/5xx, resposta parcial/incomplete ou usage ausente não promovem PASS nem acionam retry oculto | Fakes de erro e timeout | Estado BLOCKED/INCONCLUSIVE com reserva |
| R-08 | Limites de 12 gerações e de embeddings incluem cada tentativa, nunca são ultrapassados | Contador fake em indexação e consultas | Contagens observadas ≤ limites |
| R-09 | Cache por hash/modelo/versão invalida mudança de documento | Fake vector de dimensão inválida, cache antigo e documento alterado | Invalidação/erro |
| R-10 | Registros sanitizados preservam null ≠ zero; custo separado e latência medida monotonicamente | Serialização e round-trip JSONL; fake clock | JSON schema/valores corretos |
| R-11 | `semantic_correctness` é NOT_EVALUATED sem revisão cega; métricas de retrieval separadas | Casos correct/incorrect/missing/adversarial | Nenhum vencedor sem evidência |
| R-12 | CI não usa OPENAI_API_KEY nem executa chamadas pagas | Job sem segredo, spy impossibilitando rede | Log da CI |
| R-13 | Recusa/refusal e saída JSON inválida/incompleta são tratadas como não pontuáveis | Respostas provider mockadas | Erros auditáveis, sem fallback sintético |

**Comandos a executar somente após FROZEN e implementação:** `cd backend && python -m pytest -q tests/test_rag_remote.py tests/test_rag.py` e suíte completa CI do backend. **Estado atual:** NOT_RUN — runtime não implementado.

### Revisão não automatizada

- Verificar isoladamente o snapshot de preços e a disponibilidade do modelo no dia da execução.
- Revisão cega por caso do conteúdo textual, não apenas dos fatos auto-reportados.
- Verificação de que os seis casos piloto não foram modificados após medir saídas.
- Inspeção manual de logs, privacidade, comandos, pin do SDK e orçamento do operador.
- Testar defesa de prompt injection vindo **de documentos**, não apenas de perguntas do usuário.

**Regra:** CI verde para fakes não significa autorização de cobrança nem performance real. Aprovação para piloto exige segundo consentimento explícito.
