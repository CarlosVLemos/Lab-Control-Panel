# LCP-OBS-001 — Validação da Etapa B

**Estado:** implementação e testes preparados; execução sob controle do operador.
**Contrato:** CR-002 APPROVED / FROZEN.
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

## Matriz preparada

| test_id | command | environment | exit_status | result | notes |
| --- | --- | --- | --- | --- | --- |
| C01–C10 + E01–E13 sintéticos | `cd frontend && npm test -- src/domain/observation.test.ts src/domain/observation-agenttrace.test.ts` | Dependências frontend providas pelo operador | — | `NOT_RUN` | Contrato público, limites, mapeamento e falhas do adaptador. |
| E11 amostra real local | `cd frontend && AGENTTRACE_SAMPLE_PATH=/home/carlos/Documentos/www/Ifood/lcp-audit/agenttrace-sample.json npm test -- src/domain/observation-agenttrace-local.test.ts` | Arquivo local com hash congelado | — | `NOT_RUN` | Teste lê a amostra como texto, confere hash e valida o mapeamento 2+2. |
| regressão frontend | `cd frontend && npm test` | Dependências frontend providas pelo operador | — | `NOT_RUN` | Inclui teste local como skip quando a variável não é fornecida. |
| TypeScript/build | `cd frontend && npm run build` | Dependências frontend providas pelo operador | — | `NOT_RUN` | Inclui `vue-tsc -b` e Vite. |

## Riscos e pendências

- A origem e a declaração `_sample_sanitized` não autenticam execução, autoria ou ausência de dados privados.
- Licença, atribuição e sanitização humana precisam ser revistas antes de redistribuir a amostra.
- `seq` é apenas serialização determinística; consumidores futuros devem usar `position` por faixa.
- Métricas agregadas, UI e replay pertencem às Etapas C/D e não foram implementados.
- Todos os checks desta etapa permanecem `NOT_RUN` até evidência do operador.
