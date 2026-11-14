# LCP-OBS-001 — Validação da Etapa C

**Estado:** `NOT_RUN` — implementação e testes preparados; execução reservada ao operador.

## Escopo implementado

- Projeção pura e determinística `computeObservationMetrics(run)` separada do envelope público `lcp.observation.v1`.
- Contagens observáveis de eventos, gerações, ferramentas, mensagens, erros explícitos e estados desconhecidos.
- Duração da execução com base explícita: reportada, derivada exclusivamente dos timestamps da execução ou indisponível.
- Cobertura e totais de tokens por dimensão, com falha conservadora para lacunas, hierarquia ambígua e aritmética insegura.
- Série cumulativa restrita a eventos `model`, ordenada por ordinal válido e único ou por `seq` com aviso de serialização.
- Custo agregado sempre `null`; nenhuma estimativa de preço ou promoção de custos por evento.
- Avisos de origem preservados e deduplicados, incluindo a distinção de autorrelato, sem conteúdo de `detail`.

O contrato `METRICS_CONTRACT_C_DRAFT.md` permanece identificado como proposta documental; esta implementação local foi autorizada expressamente pelo operador dentro desse limite. Nenhuma parte da Etapa D foi iniciada.

## Matriz preparada

| Verificação | Cobertura | Estado |
|---|---|---|
| Testes focados M01–M09 | Totais completos, sobreposição, duração, custo, oráculo sintético AgentTrace, lacuna, vazio/autorrelato, conflito e overflow | `NOT_RUN` |
| Oráculo da amostra real | Hash aprovado, adaptação B e valores congelados da Etapa C | `NOT_RUN` |
| Regressão frontend | Suíte completa, incluindo A/B/C | `NOT_RUN` |
| Build TypeScript/Vite | Tipos e empacotamento | `NOT_RUN` |

## Comandos reservados ao operador

```bash
cd /home/carlos/Documentos/www/Ifood/lcp-audit/Lab-Control-Panel/frontend
npm test -- src/domain/observation-metrics.test.ts

AGENTTRACE_SAMPLE_PATH=/home/carlos/Documentos/www/Ifood/lcp-audit/agenttrace-sample.json npm test -- src/domain/observation-metrics-local.test.ts

npm test
npm run build
```

## Riscos e pendências para revisão

- A estrutura ainda requer revisão humana final antes de congelar o contrato de métricas; não foi incorporada ao envelope A/B.
- Tokens são aceitos no domínio validado como números finitos, mas a agregação exige inteiros seguros e falha fechada caso contrário, evitando perda silenciosa de precisão.
- A detecção de sobreposição é deliberadamente conservadora para eventos `model` em relação ancestral; estruturas cuja fonte não sustente uso incremental devem continuar produzindo total `null` e aviso.
- O teste real depende de arquivo externo controlado pelo operador e fica ignorado quando `AGENTTRACE_SAMPLE_PATH` não é informado.
- Testes e build não foram executados nesta implementação, conforme proibição do operador.
