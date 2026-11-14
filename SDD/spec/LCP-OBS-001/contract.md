# LCP-OBS-001 — Contrato de importação e métricas (v1, freeze parcial)

**Estado:** **FROZEN v1 apenas para o envelope LCP Evidence e o parser/validador da Etapa A**, por continuidade autorizada pelo operador em 14/11/2026. **Adaptador AgentTrace da Etapa B permanece DRAFT** até inspeção de amostra real e confirmação do contrato de mapeamento. Isso não autoriza downloads, instalações, testes, builds, push que rode CI, nem execução do agente externo. Nenhuma API/persistência foi aprovada.

## 1. Envelope declarativo
Um arquivo JSON UTF-8 com objeto raiz (JSONL apenas para o adaptador externo que for explicitamente definido). Proposta de campos:

```json
{
  "schema_version": "lcp.observation.v1",
  "run_id": "demo-001",
  "source": {
    "kind": "trace",
    "format": "lcp.observation.v1",
    "producer": "example-provider",
    "reference": null
  },
  "agent": {"name": "agent-a", "model": null},
  "started_at": null,
  "ended_at": null,
  "total_duration_ms": null,
  "events": [
    {
      "id": "evt-1",
      "parent_id": null,
      "seq": 1,
      "kind": "tool",
      "name": "read_file",
      "started_at": null,
      "ended_at": null,
      "status": "success",
      "usage": null,
      "detail": "Arquivo consultado"
    }
  ]
}
```

A amostra acima é uma **fixture ilustrativa**, não resultado medido. Os valores desconhecidos são `null`. Campos obrigatórios: `schema_version`, `run_id`, `source.kind`, `source.format`, `source.producer`, `agent.name`, `events[]`; por evento: `id`, `seq`, `kind`, `name`, `status`. Campos opcionais podem estar ausentes ou ser `null`; o parser os normaliza para `null` sem criar valores. `kind`: `model`, `tool`, `message`, `system`; `status`: `success`, `error`, `unknown`. `seq` é inteiro positivo, único por execução. Eventos vazios são válidos, com aviso de observabilidade limitada. `total_duration_ms` é a **duração total reportada**, não resultado de soma de eventos.

## 2. Uso e confiança
- `usage` por evento é opcional e descreve **somente aquela operação**: `input_tokens: number|null`, `output_tokens: number|null`, `duration_ms: number|null`, `cost_usd: string|null`. Contagem de tokens não deve ser projetada em segundos quando só existe `step_number`.
- `source.kind` diferencia `trace`, `self_report`, `fixture`. `reference` não implica autenticação. A UI nomeia os dados `reported`, `derived`, `estimated` ou `unavailable`.
- A soma de uso só é permitida quando não há sobreposição/cumulatividade ambígua; campos ambíguos ficam `unavailable` com explicação. Duração total pode ser **reportada** em `total_duration_ms` OU derivada de `started_at`/`ended_at` com relógios comparáveis. Se ambos estão presentes e conflitantes, registrar discrepância; nunca substituir um silenciosamente. Não somar duração de eventos para produzir duração total.
- USD é opcional: preservar tarifa e origem quando uma estimativa existir; sem referência tarifária não gerar custo estimado automaticamente.

## 3. Normalização interna
Representação somente leitura com `runId`, `sourceKind`, `events[]`, `summary`, `warnings[]`. As linhas do replay são formadas por eventos **observados ou autorrelatados**, nunca invocados no sistema.

## 4. Parser externo — AgentTrace
Fonte **selecionada para o primeiro adaptador**: [AgentTrace](source-agenttrace.md), com campos verificados no coletor público. O adaptador será congelado apenas após receber e inspecionar uma linha real sanitizada. A entrada da primeira entrega é um **trace por arquivo**, mesmo quando origem externa usa JSONL; arquivo com múltiplas linhas deve mostrar erro de escopo ou seleção explícita, não ignorar execuções. O LCP não executa código de trace.

**Nuance temporal:** spans de ferramentas têm start_ns/end_ns monotônicos; etapas LLM têm step_number e duração, mas não têm início/fim. Gráficos de tokens são por etapa ordinal; não atribuir tokens a um instante UTC. Duração total reportada não implica alinhamento entre classes de eventos. `reasoning_content` deve ser descartado antes da normalização/renderização.

## 5. Segurança e limites
- Proposta inicial: arquivo até 5 MiB e no máximo 10.000 eventos; excedentes resultam em erro claro, não truncamento silencioso de somas.
- Rejeitar JSON malformado, identidade inválida/duplicada, tamanhos excessivos, números negativos/não finitos e hierarquias cíclicas quando relevantes.
- Não interpretar conteúdo como HTML, script, URL a ser aberta ou comando a executar; exibir texto escapado/truncado. Não criar upload nem salvar dados em armazenamento persistente.
- Não aceitar segredos em amostras publicadas; o prompt de exportação pede sanitização. A UI deve alertar que arquivos locais podem conter dados sensíveis.
- Sem gravar mensagens ou artefatos de trace em logs da aplicação.

## 6. Retrocompatibilidade
Preservar `frontend/src/App.vue` e fonte HTTP Response, `CodeEvaluationView.vue`, CODE v1a e RAG-001 sem modificar seus contratos. Nova interface deve ser independente e testável.

## 7. Gate
**Etapa A:** envelope/validador FROZEN v1; autorizada somente a escrita de código e testes. Operador executará testes depois. **Etapa B:** parser AgentTrace permanece DRAFT até o operador disponibilizar a amostra concreta e aprovar mapeamento atualizado. Qualquer alteração no envelope FROZEN requer Change Request; nenhuma etapa seguinte avança automaticamente.
