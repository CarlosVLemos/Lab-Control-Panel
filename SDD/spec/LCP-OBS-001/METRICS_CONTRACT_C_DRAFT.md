# LCP-OBS-001 — Contrato de métricas (Etapa C) — FROZEN v1

**Estado:** **FROZEN v1**, após autorização do operador, implementação da Etapa C, correção dos achados finais e revisão independente Mefisto `passed`. Mudanças semânticas futuras exigem Change Request explícita. Este contrato não modifica o envelope público `lcp.observation.v1` nem os contratos FROZEN das Etapas A/B.

## Fronteira e API
- Implementação: função **pura e determinística** `computeObservationMetrics(run: ObservationRun): ObservationMetrics` em `frontend/src/domain/observation-metrics.ts`, consumindo **somente resultado já validado** de A/B, sem leitura de arquivo, HTTP, preço remoto, modelo de IA, logs, persistência ou UI.
- Projeção separada do envelope: não adicionar `summary` de volta a `ObservationRun` da Etapa A nem ao JSON v1; consumidores da Etapa D usam `{run, metrics}`.
- Representação: `summary` com contagens explícitas, duração com origem, cobertura de uso, totais nullable, custos nullable e `tokenSeries` (pontos por etapa de geração). Qualquer alteração de semântica, campos ou interpretação normativa requer aprovação do operador por Change Request.

## Campos semânticos mínimos
```ts
type KnownNumber = {
  value: number | null;
  known: number;  // operações elegíveis com inteiro não negativo e seguro
  eligible: number; // quantas operações exigiriam o dado para total completo
};
type DurationMetric = {
  valueMs: number | null;
  basis: "reported" | "derived" | "unavailable";
};
type TokenPoint = {
  eventId: string;
  ordinal: number | null; // step_number explícito, não timestamp
  inputTokens: number | null;
  outputTokens: number | null;
  cumulativeInputTokens: number | null;
  cumulativeOutputTokens: number | null;
  cumulativeTotalTokens: number | null;
};
type ObservationMetrics = {
  summary: {
    eventCount: number;
    modelStepCount: number;
    toolCallCount: number;
    messageCount: number;
    explicitErrorCount: number;
    unknownStatusCount: number;
    duration: DurationMetric;
    inputTokens: KnownNumber;
    outputTokens: KnownNumber;
    totalTokens: number | null;
    reportedCostUsd: string | null; // no MVP: null se fonte/preço/semântica insuficientes
  };
  tokenSeries: TokenPoint[];
  warnings: string[];
};
```

## Contagem e duração
- `eventCount` = número de eventos normalizados; `modelStepCount` = `kind=model`; `toolCallCount` = `kind=tool`, não contar `message` (inclusive `final_answer`); `explicitErrorCount` conta **somente** `status=error`; `unknownStatusCount` separado. Zero erros explícitos **não prova** ausência de erros.
- Valores para uma execução com zero eventos podem ser 0 **somente para contagens observáveis**; zero nunca substitui tokens, duração ou custo desconhecidos.
- Se `run.totalDurationMs` válido foi reportado, preferi-lo, com `basis=reported`. Caso contrário, calcular diferença somente de `run.startedAt/endedAt` ISO comparáveis e válidos com `basis=derived`; sem ambos, `valueMs=null` e `basis=unavailable`. Não somar `usage.durationMs` ou spans sobrepostos. Preservar avisos de inconsistência do parser.

## Tokens, lacunas e custo
- Elegíveis à série são eventos `kind=model` em sua **faixa própria**; ordenar por `position.ordinal` se todos fornecem ordinais válidos e únicos; para LCP v1 sem ordinais usar ordem declarada `seq` **rotulada** como serialização, nunca coordenadas de tempo. Jamais misturar spans monotônicos na série de tokens.
- `inputTokens`/`outputTokens` só são somáveis se valores por operação forem **incrementais**, não cumulativos, e nenhum evento elegível for ambíguo/duplicado por uma hierarquia sobreposta. O envelope LCP v1 define `usage` como uso da operação. Quando uma fonte externa ou estrutura não sustentar essa semântica, marcar total `null` e emitir aviso; não deduzir pelo modelo.
- Política conservadora v1 para hierarquia: qualquer relação ancestral `model → model`, direta ou indireta, torna a agregação de uso ambígua e mantém os totais e cumulativos em `null`, mesmo que as chamadas possam ser independentes. Não deduplicar nem inferir cobrança separada sem evidência contratual adicional.
- `KnownNumber.known/eligible` mostram cobertura por dimensão. Somente valor `number`, inteiro seguro e não negativo conta como conhecido; `null`, fração, número negativo, infinito ou inteiro inseguro não aumenta `known` nem é substituído por zero. Na projeção `TokenPoint`, valor inválido é `null`; o `ObservationRun` original permanece inalterado. Se falta valor válido de input/output em **qualquer** geração, o total respectivo é `null` (sem somar parcialmente como se fosse completo). `totalTokens` só existe quando ambos os totais têm cobertura completa e sem ambiguidade.
- Na curva acumulada, um passo sem métrica torna aquela dimensão acumulada `null` a partir desse ponto, inclusive passos seguintes; nunca retomar soma cumulativa ocultando lacuna. A UI pode exibir valores pontuais ainda conhecidos.
- Para execuções sem gerações: `known=0`, `eligible=0`, **total de tokens null**, em vez de zero observado.
- `reportedCostUsd` é null **até existir evidência suficiente de custos por operação e semântica de reporte bem definida**; não estimar preço, multiplicar tokens por tabela presumida nem tratar ausência como US$ 0. Caso agregado reportado confiável seja introduzido, exigir alteração explícita e testes de precisão decimal.
- `source.kind=self_report` mantém advertência de autorrelato; jamais transformar métricas derivadas de autorrelato em medição independente.
- Preservar e propagar avisos de origem sem duplicação e acrescentar lacunas/cobertura. Não incluir conteúdo hostil ou detalhes textuais de eventos nos warnings.

## Oráculo para amostra real AgentTrace (relatório Mefisto)
Amostra local `agenttrace-sample.json`, de hash `f765bdef22eaed2c7e7e054cd2d3f8c4fbc58d69e3fd05a7bfb5c8fec0977974`, apresenta 2 LLMSteps, um span `bash` de erro e um `final_answer` (message/unknown):
- `eventCount=4`, `modelStepCount=2`, `toolCallCount=1`, `messageCount=1`, `explicitErrorCount=1` e `unknownStatusCount=3` conforme mapeamento B.
- Duração reportada `15_910.931417 ms` (não a soma das durações de spans).
- Entrada por passo: `1510,1612` -> **3122 tokens**; saída por passo: `944,495` -> **1439 tokens**; total completo **4561**.
- Acumulado de entrada `1510,3122`; de saída `944,1439`; total acumulado `2454,4561`; custo USD `null`.
- Estes são **valores esperados de teste**, não números já calculados ou exibidos por código de Etapa C.

## Critérios de aceite
M01–M04 mais M05–M09 em [tests.md](tests.md), incluindo autorrelato, eventos vazios, lacuna intercalada, spans pai/filho, overflow, duração conflitante e fonte AgentTrace real. Testes escritos pelo Codex, **executados apenas pelo operador**. Nenhuma modificação em backend, banco, dependências, UI, adaptadores ou contratos congelados sem nova decisão.
