# LCP-OBS-001 — Validação da Etapa C

**Estado da execução:** evidências externas do operador recebidas em 2026-11-14.

**Revisão independente Mefisto:** `passed` — correção final revisada estaticamente; nenhum teste ou build executado pelo revisor.

## Escopo implementado

- Projeção pura e determinística `computeObservationMetrics(run)` separada do envelope público `lcp.observation.v1`.
- Contagens observáveis de eventos, gerações, ferramentas, mensagens, erros explícitos e estados desconhecidos.
- Duração da execução com base explícita: reportada, derivada exclusivamente dos timestamps da execução ou indisponível.
- Cobertura e totais de tokens por dimensão, com falha conservadora para lacunas, hierarquia ambígua e aritmética insegura.
- Série cumulativa restrita a eventos `model`, ordenada por ordinal válido e único ou por `seq` com aviso de serialização.
- Custo agregado sempre `null`; nenhuma estimativa de preço ou promoção de custos por evento.
- Avisos de origem preservados e deduplicados, incluindo a distinção de autorrelato, sem conteúdo de `detail`.

O contrato `METRICS_CONTRACT_C_DRAFT.md` foi congelado documentalmente como **FROZEN v1** após validação externa da correção e revisão final. O nome histórico do arquivo foi preservado para evitar quebra de referências. Nenhuma parte da Etapa D foi iniciada.

## Evidências fornecidas pelo operador

Os resultados abaixo foram reportados pelo operador para o commit `30a044324b9dd2b97b6ac619fb50f230eb573bec`; não foram reproduzidos por Mefisto nesta revisão.

| Verificação | Resultado externo |
|---|---|
| Testes focados de métricas | `10/10 PASS` |
| Oráculo da amostra AgentTrace real | `1/1 PASS` |
| Regressão frontend | `60 PASS, 2 SKIPPED`; os dois testes condicionados a variável de ambiente foram executados separadamente nas Etapas B e C |
| Build TypeScript/Vite | `PASS` |

### Evidências da correção final

Os resultados abaixo foram reportados pelo operador para o commit `f61d510edda88eecc94bf42382fd59298dcd8be9`; não foram reproduzidos por Mefisto nesta revisão.

| Verificação | Resultado externo |
|---|---|
| Testes focados de métricas | `15/15 PASS` |
| Oráculo da amostra AgentTrace real | `1/1 PASS` |
| Regressão frontend | `65 PASS, 2 SKIPPED`; os skips permanecem condicionados a variável de ambiente |
| Build TypeScript/Vite | `PASS` |

## Verificações de Mefisto

- `REVIEWED_STATICALLY`: contrato de métricas, implementação e testes comparados linha a linha.
- `REVIEWED_STATICALLY`: totais completos, lacunas e série cumulativa seguem a política fail-closed; uma lacuna não é ocultada por passos posteriores.
- `REVIEWED_STATICALLY`: duração usa total reportado ou timestamps da execução, sem somar operações sobrepostas.
- `REVIEWED_STATICALLY`: contagens usam os tipos normalizados; `final_answer` permanece mensagem quando assim classificado pelo adaptador.
- `REVIEWED_STATICALLY`: custo agregado permanece `null`, avisos de origem são deduplicados por código e `detail` não é propagado.
- `REVIEWED_STATICALLY`: a função não altera o objeto de entrada; o teste M01 verifica equivalência antes/depois.
- `NOT_RUN_BY_REVIEWER`: testes focados, teste real, regressão e build.

## Achados da revisão anterior

### MEDIUM — cobertura considera token inseguro como conhecido

**Estado final:** `RESOLVIDO` no commit `f61d510edda88eecc94bf42382fd59298dcd8be9`.

`aggregateDimension` calcula `known` apenas por `value !== null`, antes de validar se o valor é inteiro seguro. A soma falha fechada e o total fica `null`, porém um valor fracionário ou maior que `Number.MAX_SAFE_INTEGER` ainda pode produzir `known === eligible`. Isso diverge da definição contratual de `known` como quantidade de operações com dado **válido** e gera metadados contraditórios: cobertura completa, total indisponível e aviso de soma insegura.

Correção mínima proposta antes de congelar: contar como conhecido somente token inteiro, não negativo e seguro; manter `eligible` como a quantidade de eventos `model`; emitir o aviso já existente e manter total/cumulativo `null`. Acrescentar casos M09 para valor individual fracionário e inteiro individual inseguro, conferindo cobertura e pontos da série.

### LOW — invalidação hierárquica é deliberadamente ampla

**Estado final:** `RESOLVIDO` por decisão normativa conservadora em FROZEN v1.

Qualquer evento `model` que tenha outro `model` como ancestral torna todos os totais e cumulativos nulos. A regra é segura contra dupla contagem, mas também invalida chamadas aninhadas que poderiam ser independentes. Como v1 não possui metadado capaz de provar inclusão versus uso incremental independente, a postura conservadora é aceitável. Antes do congelamento, o contrato deve explicitar que ancestralidade `model → model` é tratada como ambiguidade em v1; uma futura distinção exige evolução contratual, não inferência.

### LOW — limites dos testes adversariais

**Estado final:** `RESOLVIDO` com cinco casos adversariais adicionais.

M09 cobre overflow da soma de dois inteiros individualmente seguros e ordinal duplicado, mas não cobre token individual fracionário/inseguro, overflow da dimensão de saída nem ancestralidade indireta. Os mesmos helpers atendem esses caminhos, porém os casos não estão protegidos por regressão específica.

## Decisão de congelamento

Os três achados da revisão anterior foram resolvidos, as evidências externas foram aprovadas e não há bloqueadores remanescentes. Mefisto recomenda e registra o contrato de métricas como **FROZEN v1** e a **Etapa C tecnicamente encerrada**. Mudanças semânticas futuras exigem Change Request explícita.

## Correção final preparada por Maquiavel

No momento da preparação, as alterações abaixo ainda dependiam de execução pelo operador e de nova revisão antes do congelamento:

| Correção/verificação | Estado |
|---|---|
| Cobertura `known` restrita a números inteiros, não negativos e seguros | `NOT_RUN` |
| Token individual fracionário e inteiro acima de `Number.MAX_SAFE_INTEGER` | `NOT_RUN` |
| Overflow da soma de tokens de saída | `NOT_RUN` |
| Ancestralidade indireta `model → model` | `NOT_RUN` |
| Cobertura combinando valores válidos, ausentes e inválidos | `NOT_RUN` |
| Regressão do oráculo AgentTrace | `NOT_RUN` |
| Regressão frontend completa | `NOT_RUN` |
| Build TypeScript/Vite | `NOT_RUN` |

A política conservadora de hierarquia foi explicitada normativamente. Os itens desta tabela registram o estado no momento da preparação; a execução posterior está registrada nas evidências da correção final acima.

## Comandos reservados ao operador

```bash
cd /home/carlos/Documentos/www/Ifood/lcp-audit/Lab-Control-Panel/frontend
npm test -- src/domain/observation-metrics.test.ts

AGENTTRACE_SAMPLE_PATH=/home/carlos/Documentos/www/Ifood/lcp-audit/agenttrace-sample.json npm test -- src/domain/observation-metrics-local.test.ts

npm test
npm run build
```

## Riscos remanescentes

- A estrutura permanece separada do envelope A/B e agora constitui contrato FROZEN v1 da projeção de métricas.
- A política fail-closed evita totais artificiais, mas consumidores devem tratar os avisos e os campos nullable como parte do resultado, não como sucesso parcial silencioso.
- A detecção de sobreposição permanece conservadora para eventos `model` em relação ancestral.
- O teste real depende de arquivo externo controlado pelo operador e fica ignorado quando `AGENTTRACE_SAMPLE_PATH` não é informado.
- Mefisto não executou testes ou build nesta revisão; os resultados são evidências externas fornecidas pelo operador.
