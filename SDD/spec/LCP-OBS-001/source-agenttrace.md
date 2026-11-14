# LCP-OBS-001 — Fonte externa inicial: AgentTrace

**Situação:** perfil AgentTrace **aprovado pela CR-002** para desenvolvimento da Etapa B. O operador já gerou uma amostra sanitizada em seu Atlas e o revisor Mefisto relatou inspeção; **não publicada neste repositório**. Não executar nem baixar nada a partir deste documento. Revisão humana de licença e dados sensíveis segue pendente para distribuição.

## Referências públicas verificadas (14/11/2026)
- Dataset e 1.400 traces declarados: https://huggingface.co/datasets/pagarsky/agent-trace
- Código de esquema: https://github.com/pagarsky/agent-trace/blob/main/src/tracing.py
- Instrumentação de ferramentas: https://github.com/pagarsky/agent-trace/blob/main/src/instrumentation.py
- Licença e limitações de material upstream: https://github.com/pagarsky/agent-trace/blob/main/README.md
- Arquivo candidato: `datasets/nl2bash_0_6B_20260328T133144Z.jsonl` (200 traces, Qwen3-0.6B, tarefas NL2Bash). Uma linha = uma execução. **Não importar automaticamente o arquivo inteiro.**

## Estrutura confirmada pelo código de coleta
| Campo externo | Sentido | Destino LCP proposto |
| --- | --- | --- |
| `trace_id` | UUID de execução | `run_id` |
| `model` | nome do modelo | `agent.model` |
| `timestamp_utc` | timestamp criado ao serializar o trace; **não é necessariamente início** | metadado, não `started_at` |
| `total_duration_ms` | duração entre `perf_counter_ns` start/stop | duração da execução **reportada** |
| `spans[]` | invocações de ferramentas | eventos `tool` |
| `spans[].span_id`, `parent_span_id` | IDs/relacionamentos | IDs/parent das ferramentas |
| `spans[].start_ns/end_ns` | relógio monotônico do processo; não timestamps UTC | `event.position` monotonic_ns (CR-002), como números JSON inteiros seguros |
| `spans[].duration_ms` | duração da chamada | duração observada da ferramenta |
| `spans[].exit_code` | status numérico da ferramenta | sucesso/erro **somente quando semântica do código de saída é conhecida** |
| `spans[].telemetry` | CPU, memória pico, I/O do processo | métricas de recursos opcionais; pico RSS **não somável** |
| `llm_steps[].step_id/step_number` | ID e ordem de etapa | `event.position` ordinal/llm_step; eventos `model` |
| `llm_steps[].input_tokens/output_tokens` | tokens da etapa, quando disponíveis | uso de tokens `reported`, nunca estimado silenciosamente |
| `llm_steps[].duration_ms` | duração da etapa, quando disponível | duração reportada da geração |
| `llm_steps[].tool_calls` | chamadas **propostas pelo modelo** | metadado de intenção; **não contar como ferramenta executada** |
| `metadata` | origem, configuração e versão da coleta | proveniência; não inferir medição |

## Restrições específicas
1. **Não é possível sincronizar precisamente steps LLM com spans de ferramenta** porque `LLMStep` não registra timestamps de início/fim; ordem das etapas e tempos das ferramentas ficam em faixas diferentes. Replay ordenado por índice e cronologia parcial, sem posições temporais falsas.
2. `spans[].start_ns/end_ns` são tempos monotônicos de um processo, comparáveis entre si **dentro do mesmo trace**, não datas UTC. A hora absoluta da geração não pode ser reconstruída.
3. O gráfico inicial de tokens deve ser **por etapa ordinal com soma cumulativa**. Não chamá-lo "tokens por segundo" nem representá-lo sobre eixo de segundos sem relógio de cada geração. Um gráfico temporal de operações de ferramenta é permitido com a escala relativa monotônica.
4. `reasoning_content` **não deve ser importado, renderizado, exportado ou retido no modelo de visualização**. Mesmo `prompt`, `tool_input` e `tool_output` podem conter segredos ou conteúdo privado. Para demo pública, usar somente amostra previamente sanitizada com permissão; exibir dados de detalhe resumidos e escapados.
5. Estatísticas de CPU, RSS e I/O descrevem condições da máquina coletora, não automaticamente eficiência de modelo, qualidade de resultado ou custo de API.
6. Código e dataset estão publicados sob licença Apache-2.0 conforme README, **com ressalvas para termos dos prompts upstream**. Antes de commitar um trecho no repositório de portfólio, conferir atribuição, licença e conteúdo desse trecho.
7. Falha na conversão de campo esperado não pode causar fallback silencioso para fixture sintética.

## Protocolo para obter a amostra (executado apenas pelo operador)
- Operador **já obteve** um trace JSON de `nl2bash_0_6B...` com 2 spans e 2 LLMSteps, salvo em `/home/carlos/Documentos/www/Ifood/lcp-audit/agenttrace-sample.json`.
- Script do operador removeu campos textuais incluindo `reasoning_content`; isso não comprova revisão humana de licença/atribuição. Revisar antes de publicar.
- O arquivo local foi examinado por Mefisto: **1.531 bytes**, SHA-256 `f765bdef22eaed2c7e7e054cd2d3f8c4fbc58d69e3fd05a7bfb5c8fec0977974`; 2 spans (bash/final_answer) e 2 LLMSteps, sem timestamp_utc/metadata. Codex pode ler o arquivo, sem executar seu conteúdo nem baixar dependências.
- A CR-002 foi congelada após o relatório de inspeção e aprovação humana explícita. Divergência posterior da amostra/contrato requer nova decisão, não corrigir mapeamento silenciosamente.

## Gates
- **G0:** escolha da fonte e mapeamento preliminar: concluídos por documentação pública.
- **G1:** amostra local obtida e inspecionada pelo revisor; revisão de licença para redistribuição pendente.
- **G2:** perfil e ajustes públicos aprovados (CR-002 FROZEN).
- **G3:** implementação Etapa B **AUTORIZADA SOMENTE PARA ESCRITA E TESTES PREPARADOS**; validação pelo operador NOT_RUN.

Fonte externa não é prova de autenticidade da execução nem autoriza executar comandos que apareçam em suas mensagens.
