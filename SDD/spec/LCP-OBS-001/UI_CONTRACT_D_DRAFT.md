# LCP-OBS-001 — UI_CONTRACT_D (proposta para Etapa D)

**Status: DRAFT, implementação não iniciada.** Base: Etapas A/B/C aprovadas no clone local do operador. Métricas C FROZEN v1 conforme parecer Mefisto e commit local `3289cc7dd649225ecf809f3cc1e9b5307811596a` (ainda não sincronizado com a branch documental remota). O envio de `CODEX_TASK_D.md` pelo operador constituirá autorização **somente para editar código/testes localmente**, nunca para executar testes/build ou publicar.

## Objetivo
Adicionar terceira aba `Observability` ao frontend Vue 3/Vite existente, permitindo importar **um** JSON local, visualizar métricas e evidências e navegar em replay **dos registros** (não da execução original). Sem backend, banco, upload, login, provider API, LLM, instrumentação em tempo real, preço externo ou dependências novas.

## Integração
- Conferido em `frontend/src/App.vue` da `main`: o nav alterna `response` e `code`, e o template termina com `<CodeEvaluationView v-else />`. Ao adicionar `observability`, usar ramos condicionais **explícitos**; preservar chamadas HTTP e telas existentes.
- Preferir componente isolado `frontend/src/components/ObservabilityView.vue` e helpers puros de formatação, importação e apresentação, reutilizando exportações **reais** dos módulos locais `observation.ts`, `observation-agenttrace.ts`, `observation-metrics.ts`. Não presumir assinaturas nem alterar contratos A/B/C.
- Manter paleta/espaçamento dark existente e layout responsivo. Não instalar charting library; usar SVG/CSS simples e acessível.

## Importação, confiança e estado
- Botão/label de arquivo `.json`, limite **5 MiB** conferido por `File.size` **antes** de ler, depois validação do parser. Exibir `vazio`, `carregando`, `inválido`, `pronto` e `parcial`. Ao trocar arquivo, limpar resultados/seleção anteriores; em erro, **nenhum fallback silencioso** ou reutilização do relatório anterior.
- Roteamento estrito: se objeto tem `schema_version:lcp.observation.v1`, usar parser próprio; se satisfaz estrutura AgentTrace reconhecida, usar adaptador B. Não aceitar JSONL múltiplo, formatos desconhecidos ou objetos ambíguos; não usar `eval`/comandos.
- Arquivo permanece no browser. **Não enviar conteúdo a API, localStorage, telemetry, logs ou console.** Erros devem ser curtos e estruturados, sem ecoar JSON malicioso.
- Mostrar etiquetas `TRACE EXTERNO — NÃO AUTENTICADO`, `AUTORRELATO` ou `DADOS SINTÉTICOS` conforme source; exibir warnings de origem e lacunas. `_sample_sanitized=true` não prova sanitização.
- Não versionar/publicar `agenttrace-sample.json` (licença/atribuição/sanitização ainda pendentes). Pode ter botão `Exemplo sintético` **explícito**, usando fixture própria e rotulada como tal, sem carregar automaticamente após erro.

## Métricas
- KPIs: eventos, gerações LLM, chamadas de ferramenta `tool`, erros **explícitos**, status desconhecidos, duração com `basis=reported|derived|unavailable`, input/output/total tokens e cobertura `known/eligible`. `null` deve ser **Indisponível** (`—`), nunca 0. Custo `null`: indisponível; não estimar.
- Gráfico discreto/cumulativo por **etapa LLM ordinal**: X por ordinal ou `seq` declarado (rotular quando fallback), Y por contagem de tokens, sem converter em tempo ou tokens/s. Valores nulos criam lacunas visíveis; **não unir segmentos através da lacuna**. Se não houver dados, mostrar estado vazio informativo.
- Para a amostra real já validada, devem aparecer 2 model, 1 bash/tool com error, 1 final_answer/message/unknown; 3122 input, 1439 output, 4561 total; 15910.931417 ms reportados; custo desconhecido.

## Timeline e replay
- **Nunca fingir uma cronologia global** entre `position.ordinal/lane=llm_step` e `position.monotonic_ns/lane=span`. Mostrar duas faixas separadas com cabeçalhos e aviso `ordem parcial`. Spans podem mostrar posição/duração **relativas dentro da própria faixa** (não UTC). O `final_answer` é mensagem, não ferramenta. Se eventos não tiverem position, mostrar seção `Ordem declarada (seq)`, não omitir eventos. Se forem mistos, seção separada `Sem posição observável`.
- Replay por **faixa selecionada**, Play/Pause/Anterior/Próximo, cursor/evento selecionado e detalhes. Avanço em intervalo de UI **fixo**, não segundo duração reportada e não faz reexecução. Troca de arquivo/faixa, filtro ou unmount cancela timer e seleção obsoletos. Sem múltiplos intervalos ativos.
- Não renderizar 10k eventos simultaneamente: paginação/janela **visível** (por exemplo 100/200 por página), preservando totais e seleção. Não truncar silenciosamente.
- Detalhes do evento: ID, nome, tipo, status, hierarquia, consumo, posição, `detail` apenas como texto escapado via Vue `{{ }}`/`v-text`, **nunca `v-html`**. Truncar texto longo na UI e avisar. Não interpolar URLs importadas como links, não executar instruções do JSON.
- Responsividade desktop/mobile, foco visível, label de input, `aria-live` em estados, navegação por teclado e botões com `type=button`.

## Validação e limites
- Vitest atual suporta helpers puros; **não introduzir jsdom/vitest-dom/browser-testing library**. Escrever testes determinísticos de import format router, agrupamento em faixas, ordenação, formatação nullable, amostra e truncamento. DOM e replay visual sujeitos a roteiro manual do operador; não reivindicar cobertura automatizada inexistente.
- Testes U01–U10 e regressões R01/R02 conforme `tests.md`; registrar `validation-stage-d.md` inicialmente NOT_RUN. Operador executa `npm test`, `npm run build`, `npm run dev` e verifica manualmente no navegador.
- Codex não roda testes, builds, dev server, instalações, downloads, Docker, Playwright, GitHub Actions, push, PR, merge ou deploy sem aprovação adicional. Encerrar após commit **local** de código+testes e entregar instruções.
