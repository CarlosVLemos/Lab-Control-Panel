# LCP-OBS-001 — Validação da Etapa D

**Estado:** `NOT_RUN` — implementação, testes Vitest e roteiro visual preparados; execução reservada ao operador.

## Escopo preparado

- Terceira aba `Observability`, com seleção explícita que preserva `Response` e `Code Evaluation`.
- Importação local estrita de um JSON AgentTrace ou LCP Evidence v1, limite de 5 MiB antes da leitura e nenhum upload/backend/storage.
- Indicadores derivados exclusivamente de `computeObservationMetrics`, inclusive cobertura e valores indisponíveis.
- Gráfico cumulativo discreto por etapa LLM, com lacunas e janela de até 100 pontos.
- Faixas independentes para ordinais LLM, spans monotônicos e registros sem posição observável.
- Replay visual por registros com Play/Pause/Anterior/Próximo, intervalo fixo, filtro e cancelamento de timer.
- Paginação explícita de até 100 eventos visíveis por página.
- Detalhes renderizados como texto, truncamento sinalizado e nenhuma execução de conteúdo importado.
- Exemplo sintético explícito; nenhum arquivo AgentTrace real foi copiado ou versionado.

## Matriz automatizada preparada

| ID | Verificação | Estado |
|---|---|---|
| U01 | Roteamento AgentTrace, métricas e `final_answer` como mensagem | `NOT_RUN` |
| U02 | Separação e ordenação das faixas, posição monotônica relativa | `NOT_RUN` |
| U03 | Gráfico vazio quando consumo não está disponível | `NOT_RUN` |
| U04 | Texto hostil inerte e truncamento determinístico | `NOT_RUN` |
| U05 | Autorrelato e eventos sem posição observável | `NOT_RUN` |
| U06 | Lacuna interrompe segmentos cumulativos e cobertura permanece visível | `NOT_RUN` |
| U07 | Ordem estável dentro da faixa sem cronologia global | `NOT_RUN` |
| U08 | Paginação explícita de 10.000 registros | `NOT_RUN` |
| U09 | Rejeição de tamanho, JSONL, formato desconhecido e objeto ambíguo | `NOT_RUN` |
| U10 | Roteamento LCP v1, proveniência sintética e `null` como `—` | `NOT_RUN` |
| Regressão | Suíte frontend completa A/B/C/D | `NOT_RUN` |
| Build | TypeScript/Vite | `NOT_RUN` |

## Comandos para o operador

```bash
cd /home/carlos/Documentos/www/Ifood/lcp-audit/Lab-Control-Panel/frontend

npm test -- src/domain/observation-dashboard.test.ts

AGENTTRACE_SAMPLE_PATH=/home/carlos/Documentos/www/Ifood/lcp-audit/agenttrace-sample.json \
  npm test -- src/domain/observation-agenttrace-local.test.ts src/domain/observation-metrics-local.test.ts

npm test
npm run build
npm run dev
```

Abra no navegador a URL local exibida pelo Vite e selecione a aba `Observability`. Não é necessário configurar backend para importar arquivos locais.

## Roteiro visual manual

Todos os itens abaixo estão `NOT_RUN`:

1. **R01/U10 — abas existentes:** abrir `Response`, executar o fluxo já existente; abrir `Code Evaluation`; retornar a `Observability`. Confirmar que os estados permanecem acessíveis.
2. **Exemplo sintético:** clicar `Exemplo sintético`; conferir rótulo `DADOS SINTÉTICOS`, KPIs, duas faixas e `final_answer` como `message/unknown`.
3. **U01 — AgentTrace real:** importar `/home/carlos/Documentos/www/Ifood/lcp-audit/agenttrace-sample.json`; conferir 4 eventos, 2 model, 1 tool, 1 message, 1 erro explícito, 3 unknown, 3122 input, 1439 output, 4561 total e 15910.931417 ms reportados. Confirmar custo `—`.
4. **U05 — LCP Evidence:** importar um envelope `self_report`; conferir `AUTORRELATO`, avisos, campos ausentes como `—` e eventos sem posição em `Sem posição observável · ordem declarada (seq)`.
5. **U03/U06 — gráfico:** conferir eixo discreto, rótulo ordinal/seq, lacuna sem linha atravessando valor `null` e estado vazio quando não há geração.
6. **U02/U07 — replay:** iniciar Play e alternar faixa/filtro durante a reprodução. Confirmar pausa/cancelamento, apenas um avanço por intervalo e nenhuma execução ou uso das durações reportadas.
7. **U08 — volume:** importar fixture local de até 10.000 eventos; conferir no máximo 100 registros/pontos por página, paginação anunciada e KPIs globais intactos.
8. **U09 — falhas:** tentar arquivo vazio, JSON inválido, JSONL múltiplo, objeto ambíguo/desconhecido e arquivo maior que 5 MiB. Confirmar erro estruturado, remoção do relatório anterior e ausência de fallback.
9. **U04 — hostilidade:** importar `detail` com tags HTML, instruções e URL. Confirmar exibição literal/truncada, sem link clicável, HTML interpretado ou execução.
10. **Privacidade:** com a aba Network aberta, importar arquivo e navegar/reproduzir. Confirmar que a importação não cria requisição, localStorage ou download.
11. **Acessibilidade/mobile:** testar Tab, Shift+Tab, Enter e Space; confirmar foco visível, labels, `aria-live`, botões desabilitados e layout em largura móvel.

## Limitações e riscos para revisão

- Testes Vitest cobrem helpers puros; comportamento DOM, timer, teclado, responsividade e ausência de requisição devem ser verificados manualmente.
- O replay é uma navegação visual em intervalo fixo, não reprodução temporal nem reexecução.
- A janela do gráfico recalcula a escala Y por página; valores e totais não mudam, mas comparações visuais entre páginas exigem observar os rótulos numéricos/KPIs.
- A proveniência externa permanece não autenticada; `_sample_sanitized` continua apenas uma declaração da fonte.
- Nenhum teste, build ou servidor foi executado pelo implementador.
