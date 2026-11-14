# LCP-OBS-001 — Validação da Etapa C

**Estado da execução:** evidências externas do operador recebidas em 2026-11-14.

**Revisão independente Mefisto:** `passed_with_restrictions` — inspeção estática; nenhum teste ou build executado pelo revisor.

## Escopo implementado

- Projeção pura e determinística `computeObservationMetrics(run)` separada do envelope público `lcp.observation.v1`.
- Contagens observáveis de eventos, gerações, ferramentas, mensagens, erros explícitos e estados desconhecidos.
- Duração da execução com base explícita: reportada, derivada exclusivamente dos timestamps da execução ou indisponível.
- Cobertura e totais de tokens por dimensão, com falha conservadora para lacunas, hierarquia ambígua e aritmética insegura.
- Série cumulativa restrita a eventos `model`, ordenada por ordinal válido e único ou por `seq` com aviso de serialização.
- Custo agregado sempre `null`; nenhuma estimativa de preço ou promoção de custos por evento.
- Avisos de origem preservados e deduplicados, incluindo a distinção de autorrelato, sem conteúdo de `detail`.

O contrato `METRICS_CONTRACT_C_DRAFT.md` permanece identificado como proposta documental; esta implementação local foi autorizada expressamente pelo operador dentro desse limite. Nenhuma parte da Etapa D foi iniciada.

## Evidências fornecidas pelo operador

Os resultados abaixo foram reportados pelo operador para o commit `30a044324b9dd2b97b6ac619fb50f230eb573bec`; não foram reproduzidos por Mefisto nesta revisão.

| Verificação | Resultado externo |
|---|---|
| Testes focados de métricas | `10/10 PASS` |
| Oráculo da amostra AgentTrace real | `1/1 PASS` |
| Regressão frontend | `60 PASS, 2 SKIPPED`; os dois testes condicionados a variável de ambiente foram executados separadamente nas Etapas B e C |
| Build TypeScript/Vite | `PASS` |

## Verificações de Mefisto

- `REVIEWED_STATICALLY`: contrato proposto, implementação e testes comparados linha a linha.
- `REVIEWED_STATICALLY`: totais completos, lacunas e série cumulativa seguem a política fail-closed; uma lacuna não é ocultada por passos posteriores.
- `REVIEWED_STATICALLY`: duração usa total reportado ou timestamps da execução, sem somar operações sobrepostas.
- `REVIEWED_STATICALLY`: contagens usam os tipos normalizados; `final_answer` permanece mensagem quando assim classificado pelo adaptador.
- `REVIEWED_STATICALLY`: custo agregado permanece `null`, avisos de origem são deduplicados por código e `detail` não é propagado.
- `REVIEWED_STATICALLY`: a função não altera o objeto de entrada; o teste M01 verifica equivalência antes/depois.
- `NOT_RUN_BY_REVIEWER`: testes focados, teste real, regressão e build.

## Achados

### MEDIUM — cobertura considera token inseguro como conhecido

`aggregateDimension` calcula `known` apenas por `value !== null`, antes de validar se o valor é inteiro seguro. A soma falha fechada e o total fica `null`, porém um valor fracionário ou maior que `Number.MAX_SAFE_INTEGER` ainda pode produzir `known === eligible`. Isso diverge da definição contratual de `known` como quantidade de operações com dado **válido** e gera metadados contraditórios: cobertura completa, total indisponível e aviso de soma insegura.

Correção mínima proposta antes de congelar: contar como conhecido somente token inteiro, não negativo e seguro; manter `eligible` como a quantidade de eventos `model`; emitir o aviso já existente e manter total/cumulativo `null`. Acrescentar casos M09 para valor individual fracionário e inteiro individual inseguro, conferindo cobertura e pontos da série.

### LOW — invalidação hierárquica é deliberadamente ampla

Qualquer evento `model` que tenha outro `model` como ancestral torna todos os totais e cumulativos nulos. A regra é segura contra dupla contagem, mas também invalida chamadas aninhadas que poderiam ser independentes. Como v1 não possui metadado capaz de provar inclusão versus uso incremental independente, a postura conservadora é aceitável. Antes do congelamento, o contrato deve explicitar que ancestralidade `model → model` é tratada como ambiguidade em v1; uma futura distinção exige evolução contratual, não inferência.

### LOW — limites dos testes adversariais

M09 cobre overflow da soma de dois inteiros individualmente seguros e ordinal duplicado, mas não cobre token individual fracionário/inseguro, overflow da dimensão de saída nem ancestralidade indireta. Os mesmos helpers atendem esses caminhos, porém os casos não estão protegidos por regressão específica.

## Decisão de congelamento

O contrato **não deve ser marcado `FROZEN v1` ainda**. A correção de cobertura do achado MEDIUM e os testes correspondentes são necessários. Depois disso, a política hierárquica pode ser congelada sem mudança de código, desde que sua natureza conservadora seja explicitada normativamente.

## Correção final preparada por Maquiavel

As alterações abaixo foram preparadas após a revisão de Mefisto, mas ainda dependem de execução pelo operador e de nova revisão antes do congelamento:

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

A política conservadora de hierarquia foi explicitada no contrato proposto. O estado continua **não FROZEN** até o operador executar a validação e os achados serem revistos.

## Comandos reservados ao operador

```bash
cd /home/carlos/Documentos/www/Ifood/lcp-audit/Lab-Control-Panel/frontend
npm test -- src/domain/observation-metrics.test.ts

AGENTTRACE_SAMPLE_PATH=/home/carlos/Documentos/www/Ifood/lcp-audit/agenttrace-sample.json npm test -- src/domain/observation-metrics-local.test.ts

npm test
npm run build
```

## Riscos remanescentes

- A estrutura permanece separada do envelope A/B e não deve ser consumida como contrato congelado antes da revalidação da correção indicada.
- A política fail-closed evita totais artificiais, mas consumidores devem tratar os avisos e os campos nullable como parte do resultado, não como sucesso parcial silencioso.
- A detecção de sobreposição permanece conservadora para eventos `model` em relação ancestral.
- O teste real depende de arquivo externo controlado pelo operador e fica ignorado quando `AGENTTRACE_SAMPLE_PATH` não é informado.
- Mefisto não executou testes ou build nesta revisão, conforme proibição do operador.
