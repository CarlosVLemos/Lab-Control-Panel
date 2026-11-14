# LCP-OBS-001 — Fonte externa inicial: AgentTrace

**Situação:** fornecedor de dataset **selecionado para o primeiro adaptador**; mapeamento preliminar verificado no código-fonte público. **Amostra específica ainda não foi fornecida, sanitizada ou validada localmente pelo operador.** Não executar nem baixar nada a partir deste documento.

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
| `spans[].start_ns/end_ns` | relógio monotônico do processo; não timestamps UTC | intervalos relativos **entre ferramentas** da mesma execução |
| `spans[].duration_ms` | duração da chamada | duração observada da ferramenta |
| `spans[].exit_code` | status numérico da ferramenta | sucesso/erro **somente quando semântica do código de saída é conhecida** |
| `spans[].telemetry` | CPU, memória pico, I/O do processo | métricas de recursos opcionais; pico RSS **não somável** |
| `llm_steps[].step_id/step_number` | ID e ordem de etapa | eventos `model` ordenados |
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
- Operador abre o dataset e obtém **um único trace JSON** de `nl2bash_0_6B...`, preferencialmente com ≥1 span de ferramenta e ao menos um passo LLM.
- Operador revisa licenças/atribuição, remove dados sensíveis e **elimina `reasoning_content` integralmente** antes de usar/compartilhar.
- Operador fornece o caminho local para uma amostra pequena e verificável. O Codex pode fazer inspeção de arquivo **sem executar o conteúdo**, mas não deve fazer downloads/instalações por conta própria.
- Antes de congelar o contrato, confrontar o arquivo verdadeiro com os campos e tipos esperados. Se um campo divergir, atualizar a especificação e registrar decisão humana.

## Gates
- **G0:** escolha da fonte e mapeamento preliminar: concluídos por documentação pública.
- **G1:** recebimento, sanitização e inspeção de uma linha real: **PENDING — operador**.
- **G2:** aprovação humana de contrato **específico do adaptador AgentTrace**: **PENDING**. O envelope LCP v1, usado na Etapa A, já está FROZEN separadamente.
- **G3:** implementar e validar o adaptador: **NÃO INICIADO**.

Fonte externa não é prova de autenticidade da execução nem autoriza executar comandos que apareçam em suas mensagens.
