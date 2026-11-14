# LCP-OBS-001 — Contrato de importação e métricas (v1 + CR-001/CR-002)

**Estado:** **FROZEN v1 + CR-001 e CR-002 aprovadas em 14/11/2026**; Etapa A testada pelo operador (21/21 + 30/30 + build), Etapa B **autorizada para implementar e preparar testes, ainda NOT_RUN**. A CR-002 altera o **envelope público e o tipo interno**. Não autoriza download/instalação/testes/builds/CI ou execução de agentes pelo Codex. Nenhuma API ou persistência nova aprovada. Veja [decisões](APPROVALS_2026-11-14.md) e [CR-002](CHANGE_REQUEST-002.md).

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
  "agent": {"name": null, "model": "Qwen/Qwen3-0.6B"},
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
      "position": {"basis": "monotonic_ns", "lane": "span", "start_ns": 120, "end_ns": 190},
      "usage": null,
      "detail": "Arquivo consultado"
    }
  ]
}
```

A amostra acima é uma **fixture ilustrativa**, não resultado medido. Os valores desconhecidos são `null`. Campos obrigatórios: `schema_version`, `run_id`, `source.kind`, `source.format`, `source.producer`, `agent.name` (campo presente com **string não vazia ou null**), `events[]`; por evento: `id`, `seq`, `kind`, `name`, `status`. Campos opcionais podem estar ausentes ou ser `null`; o parser os normaliza para `null` sem criar valores. `kind`: `model`, `tool`, `message`, `system`; `status`: `success`, `error`, `unknown`. `seq` é inteiro positivo, único por execução. Eventos vazios são válidos, com aviso de observabilidade limitada. `total_duration_ms` é a **duração total reportada**, não resultado de soma de eventos.

## 2. Uso e confiança
- `usage` por evento é opcional e descreve **somente aquela operação**: `input_tokens: number|null`, `output_tokens: number|null`, `duration_ms: number|null`, `cost_usd: string|null`. Contagem de tokens não deve ser projetada em segundos quando só existe `step_number`.
- `source.kind` diferencia `trace`, `self_report`, `fixture`. `reference` não implica autenticação. A UI nomeia os dados `reported`, `derived`, `estimated` ou `unavailable`.
- A soma de uso só é permitida quando não há sobreposição/cumulatividade ambígua; campos ambíguos ficam `unavailable` com explicação. Duração total pode ser **reportada** em `total_duration_ms` OU derivada de `started_at`/`ended_at` com relógios comparáveis. Se ambos estão presentes e conflitantes, registrar discrepância; nunca substituir um silenciosamente. Não somar duração de eventos para produzir duração total.
- USD é opcional: preservar tarifa e origem quando uma estimativa existir; sem referência tarifária não gerar custo estimado automaticamente.

## 3. Normalização e posições
A Etapa A fornece `runId`, `sourceKind`, `events[]` e `warnings[]`, **sem summary** (CR-001 aprovada); a Etapa C definirá e calculará `summary` separadamente.

O envelope público v1 e o modelo interno aceitam `agent.name: string|null`. `event.position` é opcional (normalizar ausência para null) e tem três possibilidades:

```json
null
```
```json
{"basis":"ordinal","lane":"llm_step","ordinal":1}
```
```json
{"basis":"monotonic_ns","lane":"span","start_ns":120,"end_ns":190}
```

No TypeScript, normalizar `start_ns/end_ns` para `startNs/endNs`. `ordinal` inteiro positivo; nanossegundos `Number.isSafeInteger` não negativos, fim >= início. É proibido arredondar valores maiores que MAX_SAFE_INTEGER ou converter relógio monotônico em data UTC. `seq` ordena a **serialização**, não cronologia global. As linhas do replay são formadas somente de eventos **observados ou autorrelatados**.

## 4. Parser externo — AgentTrace
Fonte **selecionada para o primeiro adaptador**: [AgentTrace](source-agenttrace.md), com campos verificados no coletor público. O perfil do adaptador foi **aprovado e congelado pela CR-002** com base no relatório de inspeção de amostra sanitizada fornecido pelo operador (2 spans/2 LLMSteps). A amostra não foi copiada à branch; a validação de implementação ainda será executada pelo operador. A entrada da primeira entrega é um **trace por arquivo**, mesmo quando origem externa usa JSONL; arquivo com múltiplas linhas deve mostrar erro de escopo ou seleção explícita, não ignorar execuções. O LCP não executa código de trace.

**Nuance temporal:** spans de ferramentas têm start_ns/end_ns monotônicos; etapas LLM têm step_number e duração, mas não início/fim absolutos. As duas faixas **não têm ordem global comprovável**. Ordenar LLMSteps por step_number, depois spans por start_ns/span_id, emitir aviso `PARTIAL_ORDER_ONLY`. Gráficos de tokens são por etapa ordinal, não por segundo; `reasoning_content` é descartado antes de normalizar/renderizar. `bash` usa exit_code quando inteiro; `final_answer` é evento `message`/unknown.

## 5. Segurança e limites
- Proposta inicial: arquivo até 5 MiB e no máximo 10.000 eventos; excedentes resultam em erro claro, não truncamento silencioso de somas.
- Rejeitar JSON malformado, identidade inválida/duplicada, tamanhos excessivos, números negativos/não finitos e hierarquias cíclicas quando relevantes.
- Não interpretar conteúdo como HTML, script, URL a ser aberta ou comando a executar; exibir texto escapado/truncado. Não criar upload nem salvar dados em armazenamento persistente.
- Não aceitar segredos em amostras publicadas; o prompt de exportação pede sanitização. A UI deve alertar que arquivos locais podem conter dados sensíveis.
- Sem gravar mensagens ou artefatos de trace em logs da aplicação.

## 6. Retrocompatibilidade
Preservar `frontend/src/App.vue` e fonte HTTP Response, `CodeEvaluationView.vue`, CODE v1a e RAG-001 sem modificar seus contratos. Nova interface deve ser independente e testável.

## 7. Gate
**Etapa A:** testes originais e pós-correção executados pelo operador; CR-001 aprovada. Código local precisará atualizar evidências e alinhar CR-002. **Etapa B:** perfil AgentTrace e ajustes de contrato FROZEN pela CR-002, autorização somente para escrita de código/testes; operador executa Gate B. **Etapas C/D/E:** não autorizadas. Nova alteração de contrato requer outra Change Request.
