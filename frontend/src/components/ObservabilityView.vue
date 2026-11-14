<script setup lang="ts">
import { computed, nextTick, onUnmounted, ref, watch } from 'vue'
import realSampleText from '../data/evidence/obs-002-agenttrace-sample.json?raw'
import {
  collectionDiagnostics, collectionOverview, durationOutlierFence, parseAgentTraceCollection, spanEvidence,
  type TraceCollection, type TraceDiagnostic, type TraceRecord,
} from '../domain/observation-collection'
import {
  buildTokenChart, formatCoverage, formatDuration, formatEventPosition, formatNullableNumber,
  groupObservationLanes, importObservationText, paginateItems, sourceTrustLabel, truncateObservationText,
  type ChartDatum, type ObservationLaneId,
} from '../domain/observation-dashboard'
import { MAX_OBSERVATION_BYTES, type ObservationEvent, type ObservationEventKind, type ObservationRun, type ValidationIssue } from '../domain/observation'
import type { ObservationMetrics } from '../domain/observation-metrics'

type ImportState = 'empty' | 'loading' | 'invalid' | 'ready' | 'partial'
type EventFilter = 'all' | ObservationEventKind
type StatusFilter = 'all' | 'success' | 'error' | 'unknown'
type ChartKey = 'input' | 'output' | 'total'

const PAGE_SIZE = 100
const PLAY_INTERVAL_MS = 900
const state = ref<ImportState>('empty')
const collection = ref<TraceCollection | null>(null)
const run = ref<ObservationRun | null>(null)
const metrics = ref<ObservationMetrics | null>(null)
const selectedTraceId = ref<string | null>(null)
const fileName = ref('')
const inputFormat = ref('')
const errors = ref<readonly ValidationIssue[]>([])
const modelFilter = ref('all')
const toolFilter = ref('all')
const statusFilter = ref<StatusFilter>('all')
const selectedLaneId = ref<ObservationLaneId | null>(null)
const selectedEventId = ref<string | null>(null)
const eventFilter = ref<EventFilter>('all')
const currentPage = ref(1)
const chartPage = ref(1)
const playing = ref(false)
let timer: ReturnType<typeof setInterval> | null = null
let importGeneration = 0

const selectedTrace = computed(() => collection.value?.traces.find((trace) => trace.traceId === selectedTraceId.value) ?? null)
const overview = computed(() => collection.value ? collectionOverview(collection.value) : null)
const diagnostics = computed(() => collection.value ? collectionDiagnostics(collection.value) : [])
const models = computed(() => [...new Set(collection.value?.traces.map((trace) => trace.model ?? 'Modelo não informado') ?? [])])
const tools = computed(() => [...new Set(collection.value?.traces.flatMap((trace) => trace.spans.map((span) => span.toolName)) ?? [])].sort())
const filteredTraces = computed(() => collection.value?.traces.filter((trace) => {
  if (modelFilter.value !== 'all' && (trace.model ?? 'Modelo não informado') !== modelFilter.value) return false
  if (toolFilter.value !== 'all' && !trace.spans.some((span) => span.toolName === toolFilter.value)) return false
  if (statusFilter.value !== 'all' && !traceMatchesStatus(trace, statusFilter.value)) return false
  return true
}) ?? [])
const lanes = computed(() => run.value ? groupObservationLanes(run.value.events) : [])
const selectedLane = computed(() => lanes.value.find((lane) => lane.id === selectedLaneId.value) ?? null)
const activeEvents = computed(() => {
  const events = selectedLane.value?.events ?? []
  return eventFilter.value === 'all' ? events : events.filter((event) => event.kind === eventFilter.value)
})
const eventPage = computed(() => paginateItems(activeEvents.value, currentPage.value, PAGE_SIZE))
const selectedEvent = computed(() => run.value?.events.find((event) => event.id === selectedEventId.value) ?? null)
const selectedDetail = computed(() => truncateObservationText(selectedEvent.value?.detail ?? null))
const selectedSpan = computed(() => spanEvidence(selectedTrace.value, selectedEventId.value))
const selectedFailureCount = computed(() => selectedTrace.value ? traceFailureCount(selectedTrace.value) : metrics.value?.summary.explicitErrorCount ?? 0)
const spanInput = computed(() => truncateObservationText(selectedSpan.value?.toolInput ?? null, 1200))
const spanOutput = computed(() => truncateObservationText(selectedSpan.value?.toolOutput ?? null, 1200))
const chartPagination = computed(() => paginateItems(metrics.value?.tokenSeries ?? [], chartPage.value, PAGE_SIZE))
const chart = computed(() => buildTokenChart(chartPagination.value.items, run.value?.events ?? [], metrics.value?.warnings ?? []))
const trustLabel = computed(() => run.value ? sourceTrustLabel(run.value) : '')
const partialOrder = computed(() => lanes.value.length > 1)
const statusMessage = computed(() => ({
  empty: 'Nenhuma evidência carregada.', loading: 'Lendo arquivo.', invalid: 'Arquivo rejeitado.',
  ready: 'Evidência real validada.', partial: 'Arquivo validado com avisos.',
})[state.value])

function stopReplay(): void {
  if (timer !== null) clearInterval(timer)
  timer = null
  playing.value = false
}

function traceFailureCount(trace: TraceRecord): number {
  return trace.spans.filter((span) => span.toolName !== 'final_answer' && span.exitCode !== null && span.exitCode !== 0).length
}

function traceMatchesStatus(trace: TraceRecord, status: Exclude<StatusFilter, 'all'>): boolean {
  if (status === 'error' && traceFailureCount(trace) > 0) return true
  if (status === 'success' && trace.spans.some((span) => span.toolName !== 'final_answer' && span.exitCode === 0)) return true
  return trace.run.events.some((event) => event.status === status)
}

function resetSelection(): void {
  stopReplay()
  selectedLaneId.value = null
  selectedEventId.value = null
  eventFilter.value = 'all'
  currentPage.value = 1
  chartPage.value = 1
}

function selectTrace(trace: TraceRecord): void {
  resetSelection()
  selectedTraceId.value = trace.traceId
  run.value = trace.run
  metrics.value = trace.metrics
  const firstLane = groupObservationLanes(trace.run.events)[0]
  selectedLaneId.value = firstLane?.id ?? null
  selectedEventId.value = firstLane?.events[0]?.id ?? null
}

function applyInput(input: string, label: string): void {
  stopReplay()
  errors.value = []
  fileName.value = label
  const batch = parseAgentTraceCollection(input)
  if (batch.ok) {
    collection.value = batch.value
    inputFormat.value = batch.value.traces.length > 1 ? 'AgentTrace JSONL · coleção' : 'AgentTrace'
    state.value = 'ready'
    modelFilter.value = 'all'; toolFilter.value = 'all'; statusFilter.value = 'all'
    selectTrace(batch.value.traces[0]!)
    return
  }
  const single = importObservationText(input)
  if (single.ok) {
    collection.value = null
    selectedTraceId.value = null
    run.value = single.run
    metrics.value = single.metrics
    inputFormat.value = single.format === 'agenttrace' ? 'AgentTrace' : 'LCP Evidence v1'
    state.value = single.state
    resetSelection()
    const firstLane = groupObservationLanes(single.run.events)[0]
    selectedLaneId.value = firstLane?.id ?? null
    selectedEventId.value = firstLane?.events[0]?.id ?? null
    return
  }
  collection.value = null; run.value = null; metrics.value = null
  errors.value = batch.errors.slice(0, 8)
  state.value = 'invalid'
}

async function handleFile(event: Event): Promise<void> {
  const input = event.target as HTMLInputElement
  const file = input.files?.[0]
  const generation = ++importGeneration
  stopReplay()
  if (!file) return
  fileName.value = file.name
  if (file.size === 0 || file.size > MAX_OBSERVATION_BYTES) {
    errors.value = [{ severity: 'error', code: file.size === 0 ? 'EMPTY_FILE' : 'INPUT_TOO_LARGE', path: '$', message: file.size === 0 ? 'The selected file is empty.' : `File exceeds the ${MAX_OBSERVATION_BYTES}-byte limit.` }]
    state.value = 'invalid'; input.value = ''; return
  }
  state.value = 'loading'
  try {
    const text = await file.text()
    if (generation === importGeneration) applyInput(text, file.name)
  } catch {
    errors.value = [{ severity: 'error', code: 'FILE_READ_FAILED', path: '$', message: 'The file could not be read.' }]
    state.value = 'invalid'
  } finally { input.value = '' }
}

function loadRealSample(): void {
  importGeneration += 1
  applyInput(realSampleText, 'agenttrace-sample.jsonl · derivado real incluído')
}

function selectEvent(event: ObservationEvent): void {
  selectedEventId.value = event.id
  const index = activeEvents.value.findIndex((item) => item.id === event.id)
  if (index >= 0) currentPage.value = Math.floor(index / PAGE_SIZE) + 1
}

function moveSelection(direction: -1 | 1): void {
  if (activeEvents.value.length === 0) return
  const index = activeEvents.value.findIndex((event) => event.id === selectedEventId.value)
  const next = Math.min(activeEvents.value.length - 1, Math.max(0, (index < 0 ? 0 : index) + direction))
  selectEvent(activeEvents.value[next]!)
  if (next === activeEvents.value.length - 1 && direction === 1) stopReplay()
}

function playReplay(): void {
  if (timer !== null || activeEvents.value.length === 0) return
  if (!activeEvents.value.some((event) => event.id === selectedEventId.value)) selectEvent(activeEvents.value[0]!)
  playing.value = true
  timer = setInterval(() => moveSelection(1), PLAY_INTERVAL_MS)
}

async function openDiagnostic(diagnostic: TraceDiagnostic): Promise<void> {
  const trace = collection.value?.traces.find((item) => item.traceId === diagnostic.traceId)
  if (!trace) return
  selectTrace(trace)
  await nextTick()
  if (!diagnostic.spanId) return
  const lane = groupObservationLanes(trace.run.events).find((item) => item.events.some((event) => event.id === diagnostic.spanId))
  if (lane) {
    selectedLaneId.value = lane.id
    await nextTick()
  }
  selectedEventId.value = diagnostic.spanId
}

function chartX(point: ChartDatum): number { return 44 + (point.index / Math.max(1, chart.value.points.length - 1)) * 712 }
function chartY(value: number | null): number {
  const max = chart.value.maxValue
  return value === null || max === null || max === 0 ? 218 : 218 - (value / max) * 174
}
function polylinePoints(segment: readonly ChartDatum[], key: ChartKey): string { return segment.map((point) => `${chartX(point)},${chartY(point[key])}`).join(' ') }
function positionLabel(event: ObservationEvent): string { return formatEventPosition(event, selectedLane.value?.events ?? []) }
function formatBytes(value: number | null): string {
  if (value === null) return '—'
  if (value < 1024) return `${value} B`
  if (value < 1024 * 1024) return `${(value / 1024).toFixed(1)} KiB`
  return `${(value / 1024 / 1024).toFixed(1)} MiB`
}
function formatMs(value: number | null): string { return value === null ? '—' : `${new Intl.NumberFormat('pt-BR', { maximumFractionDigits: 3 }).format(value)} ms` }
function spanBar(event: ObservationEvent): { left: string; width: string } | null {
  if (event.position?.basis !== 'monotonic_ns') return null
  const spans = (selectedLane.value?.events ?? []).filter((item) => item.position?.basis === 'monotonic_ns')
  const starts = spans.map((item) => item.position?.basis === 'monotonic_ns' ? item.position.startNs : 0)
  const ends = spans.map((item) => item.position?.basis === 'monotonic_ns' ? item.position.endNs : 0)
  const origin = Math.min(...starts); const range = Math.max(1, Math.max(...ends) - origin)
  return { left: `${((event.position.startNs - origin) / range) * 100}%`, width: `${Math.max(0.7, ((event.position.endNs - event.position.startNs) / range) * 100)}%` }
}

watch([selectedLaneId, eventFilter], () => { stopReplay(); currentPage.value = 1; selectedEventId.value = activeEvents.value[0]?.id ?? null })
watch(filteredTraces, (traces) => { if (collection.value && !traces.some((trace) => trace.traceId === selectedTraceId.value) && traces[0]) selectTrace(traces[0]) })
onUnmounted(() => { importGeneration += 1; stopReplay() })
loadRealSample()
</script>

<template>
  <section id="main-content" class="observability-hero" aria-labelledby="observability-title">
    <div><h1 id="observability-title">Observabilidade</h1><p class="lede">12 traces reais · AgentTrace · análise determinística</p></div>
    <div class="import-actions"><label class="file-label" for="observation-file">Arquivo JSON ou JSONL local</label><input id="observation-file" class="file-input" type="file" accept=".json,.jsonl,application/json" @change="handleFile"><button class="button ghost" type="button" @click="loadRealSample">Restaurar amostra real</button><small>Máximo 5 MiB · processamento local, sem upload</small></div>
  </section>
  <section class="import-status" :class="state" aria-live="polite" :role="state === 'invalid' ? 'alert' : 'status'"><div><strong>{{ statusMessage }}</strong><span v-if="fileName">{{ fileName }}</span></div><ul v-if="state === 'invalid'" class="issue-list"><li v-for="item in errors" :key="`${item.code}-${item.path}`"><code>{{ item.code }}</code> · {{ item.path }} · {{ item.message }}</li></ul></section>

  <template v-if="collection && overview">
    <section class="metadata" aria-label="Procedência da coleção"><span>Dataset: {{ collection.source.dataset }}</span><span>Revisão: {{ collection.source.revision ?? 'não registrada no manifesto' }}</span><span>SHA-256: {{ collection.source.localSha256 ?? '—' }}</span><span>Licença: {{ collection.source.license ?? '—' }}</span></section>
    <section class="overview-kpis" aria-label="Visão geral das execuções"><article><span>Execuções</span><strong>{{ overview.traces }}</strong></article><article><span>Duração p50</span><strong>{{ formatMs(overview.durationP50Ms) }}</strong></article><article><span>Duração p95</span><strong>{{ formatMs(overview.durationP95Ms) }}</strong></article><article><span>Chamadas de ferramentas</span><strong>{{ overview.toolCalls }}</strong></article><article><span>Falhas registradas</span><strong>{{ overview.failures }}</strong></article></section>
    <section class="model-comparison" aria-label="Comparação observada por modelo"><article v-for="model in overview.models" :key="model.model"><h2>{{ model.model }}</h2><dl><div><dt>Execuções</dt><dd>{{ model.traces }}</dd></div><div><dt>p50</dt><dd>{{ formatMs(model.durationP50Ms) }}</dd></div><div><dt>Ferramentas</dt><dd>{{ model.toolCalls }}</dd></div><div><dt>Falhas</dt><dd>{{ model.failures }}</dd></div></dl></article></section>
    <p class="method-note">Percentis: nearest-rank. Duração atípica: limite superior de Tukey (Q3 + 1,5 × IQR) = {{ formatMs(durationOutlierFence(collection.traces)) }}.</p>

    <section class="trace-browser" aria-labelledby="trace-browser-title"><div class="section-heading"><h2 id="trace-browser-title">Execuções</h2><span>{{ filteredTraces.length }} de {{ collection.traces.length }}</span></div><div class="trace-filters"><label>Modelo<select v-model="modelFilter"><option value="all">Todos</option><option v-for="model in models" :key="model" :value="model">{{ model }}</option></select></label><label>Ferramenta<select v-model="toolFilter"><option value="all">Todas</option><option v-for="tool in tools" :key="tool" :value="tool">{{ tool }}</option></select></label><label>Status<select v-model="statusFilter"><option value="all">Todos</option><option value="success">Sucesso</option><option value="error">Erro</option><option value="unknown">Desconhecido</option></select></label></div><div class="trace-list"><button v-for="trace in filteredTraces" :key="trace.traceId" type="button" :class="{ selected: trace.traceId === selectedTraceId }" :aria-pressed="trace.traceId === selectedTraceId" @click="selectTrace(trace)"><strong>{{ trace.model ?? 'Modelo não informado' }}</strong><span>{{ trace.datasetName }}/{{ trace.taskId }}</span><small>{{ formatMs(trace.run.totalDurationMs) }} · {{ traceFailureCount(trace) }} falha(s)</small></button></div></section>

    <section class="diagnostics-card" aria-labelledby="diagnostics-title"><div class="section-heading"><h2 id="diagnostics-title">Diagnósticos determinísticos</h2><span>{{ diagnostics.length }} evidências</span></div><div class="diagnostic-groups"><article v-for="kind in (['tool_error', 'repeated_call', 'duration_outlier', 'top_contributor'] as const)" :key="kind"><h3>{{ { tool_error: 'Erros de ferramenta', repeated_call: 'Chamadas repetidas', duration_outlier: 'Durações atípicas', top_contributor: 'Maiores operações medidas' }[kind] }}</h3><button v-for="item in diagnostics.filter((entry) => entry.kind === kind)" :key="item.id" type="button" @click="openDiagnostic(item)"><strong>{{ item.title }}</strong><span>{{ item.evidence }}</span><code>{{ item.traceId }}{{ item.spanId ? ` · ${item.spanId}` : '' }}</code></button><p v-if="!diagnostics.some((entry) => entry.kind === kind)">Nenhuma ocorrência na amostra.</p></article></div></section>
  </template>

  <template v-if="run && metrics">
    <section class="metadata" aria-label="Metadados da execução selecionada"><span>Formato: {{ inputFormat }}</span><span>Execução: {{ run.runId }}</span><span>Fonte: {{ run.source.producer }}</span><span>Modelo: {{ run.agent.model ?? '—' }}</span></section>
    <section class="trust-banner" :class="run.sourceKind"><strong>{{ trustLabel }}</strong><p>Origem declarada; conteúdo não autenticado. Nenhum comando importado é executado.</p></section>
    <section v-if="selectedTrace?.prompt" class="prompt-card"><strong>Entrada da execução</strong><p>{{ selectedTrace.prompt }}</p></section>
    <section class="observation-kpis" aria-label="Indicadores da execução selecionada"><article><span>Eventos</span><strong>{{ metrics.summary.eventCount }}</strong></article><article><span>Gerações LLM</span><strong>{{ metrics.summary.modelStepCount }}</strong></article><article><span>Ferramentas</span><strong>{{ metrics.summary.toolCallCount }}</strong></article><article><span>Falhas registradas</span><strong>{{ selectedFailureCount }}</strong></article><article class="wide"><span>Duração</span><strong>{{ formatDuration(metrics) }}</strong></article><article class="wide"><span>Tokens de entrada</span><strong>{{ formatCoverage(metrics.summary.inputTokens) }}</strong></article><article class="wide"><span>Tokens de saída</span><strong>{{ formatCoverage(metrics.summary.outputTokens) }}</strong></article><article><span>Total de tokens</span><strong>{{ formatNullableNumber(metrics.summary.totalTokens, 0) }}</strong></article></section>

    <section class="chart-card" aria-labelledby="token-chart-title"><div class="section-heading"><h2 id="token-chart-title">Tokens por etapa LLM</h2><span>{{ chartPagination.total }} etapas</span></div><p class="chart-note">Eixo ordinal, não temporal; lacunas interrompem as linhas.</p><div v-if="chart.points.length === 0 || chart.maxValue === null" class="chart-empty">Consumo acumulado indisponível.</div><template v-else><div class="chart-legend"><span class="input-line">Entrada</span><span class="output-line">Saída</span><span class="total-line">Total</span></div><svg class="token-chart" viewBox="0 0 800 250" role="img" aria-label="Tokens acumulados por etapa"><line x1="44" y1="218" x2="756" y2="218" class="axis"/><line x1="44" y1="44" x2="44" y2="218" class="axis"/><polyline v-for="(segment, index) in chart.inputSegments" :key="`i-${index}`" :points="polylinePoints(segment, 'input')" class="chart-series input"/><polyline v-for="(segment, index) in chart.outputSegments" :key="`o-${index}`" :points="polylinePoints(segment, 'output')" class="chart-series output"/><polyline v-for="(segment, index) in chart.totalSegments" :key="`t-${index}`" :points="polylinePoints(segment, 'total')" class="chart-series total"/></svg></template></section>

    <section class="lane-card" aria-labelledby="replay-title"><div class="section-heading"><h2 id="replay-title">Timeline e spans</h2><span>{{ run.events.length }} eventos</span></div><p :class="['partial-order', { visible: partialOrder }]">{{ partialOrder ? 'Ordem parcial: faixas sem cronologia comum.' : 'Ordem declarada.' }} Replay visual a cada {{ PLAY_INTERVAL_MS }} ms.</p><div class="lane-switcher" role="group" aria-label="Selecionar faixa"><button v-for="lane in lanes" :key="lane.id" type="button" :class="{ active: selectedLaneId === lane.id }" @click="selectedLaneId = lane.id">{{ lane.label }} <span>{{ lane.events.length }}</span></button></div><div class="replay-toolbar"><div class="replay-controls"><button type="button" @click="moveSelection(-1)">← Anterior</button><button v-if="!playing" type="button" @click="playReplay">▶ Reproduzir</button><button v-else type="button" @click="stopReplay">Ⅱ Pausar</button><button type="button" @click="moveSelection(1)">Próximo →</button></div><label>Tipo<select v-model="eventFilter"><option value="all">Todos</option><option value="model">Modelo</option><option value="tool">Ferramenta</option><option value="message">Mensagem</option></select></label></div>
      <div class="replay-grid"><div class="event-list"><button v-for="event in eventPage.items" :key="event.id" type="button" :class="['event-row', event.status, { selected: selectedEventId === event.id }]" @click="selectEvent(event)"><span class="event-seq">{{ event.seq }}</span><span><strong>{{ event.name }}</strong><small>{{ event.kind }} · {{ event.status }}</small></span><code>{{ positionLabel(event) }}</code><span v-if="spanBar(event)" class="waterfall-track"><i :style="spanBar(event)!"/></span></button></div><aside class="event-detail" aria-live="polite"><template v-if="selectedEvent"><h3>{{ selectedEvent.name }}</h3><dl><div><dt>ID</dt><dd><code>{{ selectedEvent.id }}</code></dd></div><div><dt>Tipo / status</dt><dd>{{ selectedEvent.kind }} / {{ selectedEvent.status }}</dd></div><div><dt>Posição</dt><dd>{{ positionLabel(selectedEvent) }}</dd></div><div><dt>Duração</dt><dd>{{ formatMs(selectedEvent.usage?.durationMs ?? null) }}</dd></div><div><dt>Exit code</dt><dd>{{ selectedSpan?.exitCode ?? '—' }}</dd></div><div><dt>CPU usuário / sistema</dt><dd>{{ selectedSpan?.telemetry ? `${selectedSpan.telemetry.userTimeS ?? '—'} s / ${selectedSpan.telemetry.systemTimeS ?? '—'} s` : '—' }}</dd></div><div><dt>Memória RSS máxima</dt><dd>{{ formatBytes(selectedSpan?.telemetry?.maxRssBytes ?? null) }}</dd></div><div><dt>Leitura / escrita</dt><dd>{{ formatBytes(selectedSpan?.telemetry?.readBytes ?? null) }} / {{ formatBytes(selectedSpan?.telemetry?.writeBytes ?? null) }}</dd></div></dl><div v-if="selectedSpan" class="io-grid"><div><strong>Entrada da ferramenta</strong><pre>{{ spanInput.text }}</pre></div><div><strong>Saída da ferramenta</strong><pre>{{ spanOutput.text }}</pre></div></div><div v-else class="event-detail-text"><strong>Conteúdo importado</strong><pre>{{ selectedDetail.text }}</pre></div></template></aside></div>
    </section>
  </template>
</template>
