# LCP-OBS-001 — Matriz de validação (PLANNED / NOT_RUN)

**Execução:** responsabilidade do operador, ao fim de cada etapa. O Codex prepara testes e relata comandos sugeridos; **não os executa sem autorização explícita**. Nenhuma célula desta matriz constitui teste já executado.

| ID | Etapa | Dado/caso | Critério esperado |
| --- | --- | --- | --- |
| C01 | A | Envelope v1 completo | Parse determinístico; eventos com ordem estável |
| C02 | A | Sem timestamps, modelo, tokens, custo | Importação parcial; campos desconhecidos são null |
| C03 | A | JSON inválido, >5 MiB, >10k eventos, números negativos ou IDs duplicados | Rejeição explícita, sem cálculo parcial enganoso |
| C04 | A | Conteúdo com "ignore instruções" e tags HTML | Tratado como dado, texto escapado; zero execução |
| C05 | A | Autorrelato retrospectivo | Sinaliza SELF_REPORT e não "observado independente" |
| C06 | A | `total_duration_ms` válido com timestamps ausentes | Preserva duração total reportada; não fabrica início/fim |
| C07 | A | Duração total reportada conflita com intervalo de timestamps | Aviso de inconsistência; não sobrescrever fonte silenciosamente |
| C08 | A | `seq` duplicado, evento sem nome, referência a pai inexistente/cíclico | Erro de contrato explícito; sem inventar árvore |
| C09 | A | Evento sem tempo, tokens ou uso | Mantém `null` e sequência ordinal, não timestamp artificial |
| C10 | A | Campo `reasoning_content` ou extras arbitrários em JSON | Não propagar campo sensível à representação normalizada nem ao resultado de erro |
| E01 | B | Amostra externa com spans e ferramentas | Mapeamento reproduzível; IDs, tipos e status corretos |
| E02 | B | Formato externo sem uso/erro/timestamps | Mantém desconhecido; sem extrapolação |
| E03 | B | Campo incompatível/versão não suportada | Falha clara ou parcial explicitamente rotulada |
| E04 | B | AgentTrace LLMStep apenas com step_number e tokens | Gráfico por etapa ordinal; nenhuma posição UTC inventada |
| E05 | B | AgentTrace TOOL start_ns/end_ns | Durações e posições relativas válidas entre ferramentas da mesma execução; não converter ns monotônico em data UTC |
| E06 | B | tool_calls do modelo sem span executado correspondente | Não contar como ferramenta executada |
| E07 | B | reasoning_content, tool outputs e mensagens potencialmente privadas | Descartar reasoning_content; dados sensíveis fora das fixtures públicas; renderização sem interpretação de instruções |
| E08 | B | JSONL com vários traces em arquivo | Não escolher primeiro silenciosamente; sinalizar limitação/seleção explícita |
| E09 | B | LCP Evidence v1 com `agent.name=null`, `position=null`, ordinal e monotonic_ns | Parser público aceita e normaliza; rejeita strings vazias e posições inválidas |
| E10 | B | Number.MAX_SAFE_INTEGER + 1 em nanossegundos, end_ns < start_ns | Rejeição estruturada sem arredondamento silencioso |
| E11 | B | Amostra inspecionada (2 LLMSteps, `bash`, `final_answer`) | 4 eventos, 2 model + 1 tool + 1 message; `bash` exit 1 = error; resposta unknown; warnings PARTIAL_ORDER_ONLY + SOURCE_NOT_AUTHENTICATED |
| E12 | B | `telemetry` presente e `_sample_sanitized` true/false/ausente | Dados descartados; warnings coerentes, sem tratar declaração como prova |
| E13 | B | `step_number` duplicado, tipos TOOL desconhecidos, spans com pais/IDs inválidos | Erro com caminho do dado original, nunca fallback para fixture |
| M01 | C | Duas chamadas com uso incremental | Soma por operação; série em degraus nos **passos conhecidos**; eixo temporal só com timestamps comparáveis |
| M02 | C | Totais cumulativos e spans pai/filho | Sem dupla contagem; ambiguidade exposta |
| M03 | C | Eventos sem tempo, sobrepostos, falha sem duração | Não somar durations para criar tempo total; estados corretos |
| M04 | C | Custo ausente ou modelo/tarifa não confirmados | Null; nunca custo artificial 0 USD |
| M05 | C | 2 gerações AgentTrace, `bash` error, `final_answer` message | 4 eventos, 2 model, 1 tool, 1 message, 1 erro explícito, 3 unknown; 3122 entrada, 1439 saída, 4561 total; duration reportada 15910.931417 ms |
| M06 | C | Uma geração sem input ou output entre passos válidos | Total correspondente null, cobertura parcial e cumulativo null a partir da lacuna; valores pontuais preservados |
| M07 | C | Nenhuma geração/eventos, source self_report | Contagens 0, tokens/custo/tempo desconhecidos null; proveniência de autorrelato preservada |
| M08 | C | Duração reportada e timestamps divergentes, operações simultâneas | Preferir duração reportada com `basis=reported`, manter aviso; não somar durações |
| M09 | C | Tokens incremental/cumulativo ambíguos, spans nested, overflow de soma | Não produzir total falso/overflow nem contagem duplicada; aviso e null na dimensão afetada |
| U01 | D | Trace externo importado | KPIs, timeline, gráfico e detalhe conferem com dados brutos |
| U02 | D | Play/Pause/Anterior/Próximo e seleção | Estado coerente; sem eventos ou tempos simulados |
| U03 | D | Sem consumo ou trace parcial | Gráfico vazio informativo e lacunas visíveis |
| U04 | D | Dados hostis renderizados na UI | Sem execução de JS/HTML, sem envio ao backend |
| U05 | D | LCP self_report sem posição vs AgentTrace com duas faixas | Rótulo de autorrelato; ordem declarada e faixas LLM/spans independentes |
| U06 | D | Lacuna em etapa LLM, cobertura parcial, custo ausente | Não conectar gráfico através de null, cobertura e custo indisponível visíveis |
| U07 | D | Troca de arquivo/faixa durante Play/Pause e componente desmontado | Cancelar timers/seleção antiga; nenhuma reexecução |
| U08 | D | Trace de milhares de eventos | Paginação/janela explícita; somatórios íntegros |
| U09 | D | Arquivo vazio, inválido, >5 MiB, formato desconhecido ou JSONL múltiplo | Erro claro; sem fallback e sem ecoar payload |
| U10 | D | Alternância Response/Code/Observability e layout mobile/teclado | Navegação preservada, layout responsivo, controles acessíveis |
| R01 | D/E | Response + Code Evaluation já existentes | Fluxos continuam acessíveis e comportamentos preservados |
| R02 | E | Recurso estático em produção | Nenhum arquivo importado enviado à rede; exposição de API não necessária |

**Evidência histórica Etapa A:** 21/21 testes focados, 30/30 frontend, build PASS e audit produção 0 alerts **reportados pelo operador** no commit local `a4e4cfeb`. Não representam testes B; ver [aprovações](APPROVALS_2026-11-14.md).

## Gates operacionais
- **Gate A:** operador roda testes focados de contrato.
- **Gate B:** operador roda testes focados de adaptador usando amostra fornecida.
- **Gate C:** operador roda testes focados de métricas.
- **Gate D:** operador roda suíte frontend, build e verificação visual; depois regressão E2E existente se ambiente já estiver preparado.
- **Gate E:** operador revisa diffs, evidências, CI autorizada e decisão de merge/deploy.

Os comandos exatos serão definidos junto aos testes implementados; **não lançar instalações/downloads para consegui-los**. Se a máquina não possui uma dependência, marcar `BLOCKED` e instruir o operador sobre o requisito.

Formato mínimo de evidência por teste: `test_id`, `command`, `environment`, `exit_status`, `result` (PASS/FAIL/NOT_RUN/BLOCKED), `notes`, `commit_sha`. Não inferir PASS a partir de uma expectativa.
