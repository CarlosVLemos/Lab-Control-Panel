# CHANGE_REQUEST-002 — Contrato público de posição e perfil AgentTrace

**Estado:** APPROVED / FROZEN para a Etapa B · **Aprovação humana:** 2026-11-14 (resposta "sim" ao contrato revisado) · **Tipo:** mudança do contrato FROZEN da Etapa A.

## Problema
Uma amostra sanitizada de AgentTrace foi examinada pelo revisor, com 2 spans e 2 LLMSteps. O AgentTrace pode não informar nome do agente e não compartilha uma ordem temporal completa entre gerações e ferramentas. O envelope v1 da Etapa A não representava posição monotônica nem nome de agente nulo.

## Decisão
1. Relaxar **também o JSON público** `agent.name` para `string | null` (quando null, nome desconhecido; nunca substituir por nome do modelo). String vazia continua inválida.
2. Acrescentar `event.position` opcional, normalizado para null quando ausente:

```json
{"basis": "ordinal", "lane": "llm_step", "ordinal": 2}
```

ou

```json
{"basis": "monotonic_ns", "lane": "span", "start_ns": 120, "end_ns": 190}
```

`start_ns/end_ns` são contadores **monotônicos** relativos ao processo de origem, não timestamps UTC. Inteiros JSON devem ser seguros em JavaScript e não negativos; valores inseguros são rejeitados, nunca arredondados. `end_ns >= start_ns`.
3. `seq` significa somente ordem de serialização/visualização determinística. O adaptador AgentTrace emite LLMSteps por `step_number`, seguidos de spans por `start_ns` e `span_id`, **sem alegar cronologia global**. Adicionar `PARTIAL_ORDER_ONLY`.
4. Converter `bash` exit_code `0` em `success`, códigos inteiros diferentes de zero em `error` e ausência/null em `unknown`. Status de outras ferramentas sem contrato específico: `unknown`. `final_answer` é `message`/unknown e não ferramenta operacional.
5. Preservar como declarado `trace_id` (`run_id`), `model`, `total_duration_ms`, LLMStep tokens e durações, span id, hierarquia e tempos relativos. `dataset_name` string|null vai para `source.reference`; null permanece null.
6. Validar `telemetry` como objeto se presente e descartá-lo; aviso único `TELEMETRY_IGNORED`. `_sample_sanitized: true` gera `SANITIZATION_SELF_DECLARED`; ausência ou false, `SANITIZATION_UNCONFIRMED`. Em todos os casos emitir `SOURCE_NOT_AUTHENTICATED`. Nunca propagar `reasoning_content`, prompts, entradas/saídas de ferramenta ou chaves arbitrárias.
7. Formato externo suportado: um objeto JSON AgentTrace por arquivo, sem autodetecção universal. 5 MiB e máximo 10.000 eventos totais; rejeitar JSONL multilinha sem escolher linha silenciosamente; spans `type=TOOL`, IDs únicos entre coleções, `step_number` inteiro positivo e único, tempos válidos, pais existentes apenas entre spans.
8. Não há transformação para HTML executável, comando, upload HTTP ou persistência. Fonte não autenticada não equivale a prova independente.

## Compatibilidade e implementação
- `schema_version` permanece `lcp.observation.v1`, mas as mudanças de null/position são normativas e exigem novos testes. O parser/normalizador da Etapa A precisa aceitar explicitamente esses casos (sem deixar campos extras passar sem validação).
- A representação normalizada segue o contrato público; campos opcionais ausentes são null. O adaptador **não pode contornar validação**; saída AgentTrace precisa passar pelos invariantes do validador comum.
- `summary` **não** integra Etapa B (CR-001 aprovada; será definido na C).
- Não incluir amostra real sanitizada no repositório sem revisão humana de licença, atribuição e dados sensíveis.
- Não aprovar no automático etapas C/D ou alterações no backend.

## Evidência disponível e limitações
Relatório Mefisto da amostra local `/home/carlos/Documentos/www/Ifood/lcp-audit/agenttrace-sample.json`: 1.531 bytes; SHA-256 `f765bdef22eaed2c7e7e054cd2d3f8c4fbc58d69e3fd05a7bfb5c8fec0977974`; 2 spans, 2 LLMSteps; arquivo JSON único; 2 ferramentas listadas (`bash`, `final_answer`); tokens por etapa. Este registro se baseia no relatório fornecido pelo operador; o arquivo local não foi copiado para esta branch documental. A verificação de licença/atribuição para redistribuição permanece pendente.

## Aprovação, stop conditions e testes
Aprovado para **implementação Etapa B no clone local após sincronizar a branch documental**, sem instalação, download, execução de testes/builds, push ou PR. Validar regressão do envelope v1 e E01–E08, incluindo null, position, ordenação parcial, estado de `bash`, `final_answer` e remoção de campos sensíveis. Operador executa os testes e apresenta as evidências.

Mudanças além destas cláusulas exigem nova Change Request.
