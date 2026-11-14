# LCP-OBS-001 — Validação da Etapa D

**Estado:** `passed_with_restrictions` em `20d210ecccf0fdfe419b670e6550f76c2b071ff5` — Vitest, oráculos locais e build aprovados. Playwright bloqueado por dependência ausente; roteiro visual permanece `NOT_RUN`.

**Ambiente:** Node `v26.13.0`, npm `12.2.2`, dependências frontend já presentes. Execução autorizada pelo operador no pedido de limpeza da interface em 14/11/2026; nenhuma dependência foi instalada.

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

## Matriz automatizada

| ID | Verificação | Estado |
|---|---|---|
| U01–U10 | `npm test -- src/domain/observation-dashboard.test.ts` | `PASS` — 10/10 |
| Oráculos locais | `AGENTTRACE_SAMPLE_PATH=/home/carlos/Documentos/www/Ifood/lcp-audit/agenttrace-sample.json npm test -- src/domain/observation-agenttrace-local.test.ts src/domain/observation-metrics-local.test.ts` | `PASS` — 2/2 |
| Regressão | `npm test` | `PASS` — 75/75; 2 testes locais condicionais ignorados e executados separadamente acima |
| Build | `npm run build` | `PASS` — TypeScript e Vite, 26 módulos transformados |
| Playwright | `npx --no-install playwright test --config playwright.config.ts` | `BLOCKED` — `@playwright/test` não está instalado; tentativa sem instalação não coletou testes e foi interrompida |

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
