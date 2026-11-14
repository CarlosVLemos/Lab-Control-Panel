# LCP-OBS-001 — Validação da Etapa B

**Estado:** Gate B executado pelo operador; revisão estática Mefisto `passed`.
**Contrato:** CR-002 APPROVED / FROZEN.
**Commit validado:** `4de3185be423231169778c0bc4dc45f241e94af0`.
**Amostra local inspecionada:** `/home/carlos/Documentos/www/Ifood/lcp-audit/agenttrace-sample.json`, 1.531 bytes, SHA-256 `f765bdef22eaed2c7e7e054cd2d3f8c4fbc58d69e3fd05a7bfb5c8fec0977974`.

## Implementação preparada

- Envelope LCP v1 aceita `agent.name` presente como string não vazia ou `null`.
- `event.position` normaliza ausência para `null`, ordinal para a faixa `llm_step` e nanossegundos monotônicos para a faixa `span`.
- Adaptador AgentTrace defensivo, sem rede, backend, execução de conteúdo ou fallback para fixture.
- LLMSteps ordenados por `step_number`; spans por `start_ns` e `span_id`; serialização em faixas sem cronologia global inventada.
- `bash` usa a semântica congelada de `exit_code`; `final_answer` é `message`/`unknown`.
- Telemetria e campos privados são descartados; proveniência e sanitização permanecem declarações não autenticadas.
- A amostra real não foi copiada ao repositório. Fixture versionada é exclusivamente sintética.

## Mapeamento

| AgentTrace | LCP normalizado |
| --- | --- |
| `trace_id` | `runId` |
| `model` | `agent.model`; `agent.name=null` |
| `total_duration_ms` | `totalDurationMs` reportado |
| `dataset_name` | `source.reference` |
| `step_id`, `step_number` | evento `model`, posição ordinal |
| tokens/duração do LLMStep | `usage`, custo `null` |
| `span_id`, `parent_span_id` | ID e hierarquia do evento |
| `start_ns`, `end_ns` | posição monotônica, nunca data UTC |
| span `bash` | `tool`; exit 0 success, demais inteiros error, null unknown |
| span `final_answer` | `message`/`unknown` |
| `telemetry`, conteúdo privado e chaves extras | validados quando aplicável e descartados |

## Evidência fornecida pelo operador

| test_id | comando preparado | environment | exit_status | result | commit_sha | notes |
| --- | --- | --- | --- | --- | --- | --- |
| C01–C10 + E01–E13 sintéticos | `cd frontend && npm test -- src/domain/observation.test.ts src/domain/observation-agenttrace.test.ts` | Ambiente local do operador | Não informado | `PASS` | `4de3185be423231169778c0bc4dc45f241e94af0` | Operador reportou 41/41 testes aprovados. |
| E11 amostra real local | `cd frontend && AGENTTRACE_SAMPLE_PATH=/home/carlos/Documentos/www/Ifood/lcp-audit/agenttrace-sample.json npm test -- src/domain/observation-agenttrace-local.test.ts` | Amostra local com hash congelado | Não informado | `PASS` | `4de3185be423231169778c0bc4dc45f241e94af0` | Operador reportou 1/1 aprovado, incluindo hash e mapeamento 2+2. |
| regressão frontend | `cd frontend && npm test` | Ambiente local do operador | Não informado | `PASS` | `4de3185be423231169778c0bc4dc45f241e94af0` | Operador reportou 50 PASS e 1 SKIPPED; o teste local foi executado separadamente com a variável de ambiente. |
| TypeScript/build | `cd frontend && npm run build` | Ambiente local do operador | Não informado | `PASS` | `4de3185be423231169778c0bc4dc45f241e94af0` | Build TypeScript/Vite aprovado conforme relato do operador. |

Os comandos acima são os comandos preparados para o Gate B. Os totais e resultados foram fornecidos pelo operador; códigos de saída e detalhes adicionais do ambiente não foram fornecidos nem inferidos pelo revisor.

## Revisão independente Mefisto

- Revisão exclusivamente estática do commit e do diff contra CR-002; testes e build não foram reexecutados pelo revisor.
- Parser público aceita `agent.name=null`, exige presença do campo e normaliza posições ausentes/ordinais/monotônicas sem coerção insegura.
- Adaptador ordena LLMSteps e spans em faixas separadas, trata `seq` somente como serialização e sempre emite `PARTIAL_ORDER_ONLY`.
- `bash`, `final_answer`, IDs, pais, ciclos, limites e números inseguros seguem o contrato congelado.
- Conteúdo privado e telemetria não são propagados; erros contêm códigos, paths e mensagens constantes, sem valores brutos.
- Proveniência e sanitização são explicitamente não autenticadas.
- **Veredito:** `passed`; nenhum achado BLOCKER, HIGH ou MEDIUM.

## Riscos e pendências

- A origem e a declaração `_sample_sanitized` não autenticam execução, autoria ou ausência de dados privados.
- Licença, atribuição e sanitização humana precisam ser revistas antes de redistribuir a amostra.
- `seq` é apenas serialização determinística; consumidores futuros devem usar `position` por faixa.
- Métricas agregadas, UI e replay pertencem às Etapas C/D e não foram implementados.
- A fronteira exata de 10.000 eventos combinados e variações complexas de JSONL não têm caso dedicado do adaptador; o código usa limite inclusivo e scanner defensivo, e o limite comum de 10.000 eventos possui cobertura na Etapa A.
- A amostra real continua externa ao repositório e o teste correspondente depende do caminho e hash aprovados.
