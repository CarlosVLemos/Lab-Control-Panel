<script setup lang="ts">
import { computed, onUnmounted, ref, watch } from 'vue'
import { syntheticAgentTraceFixture } from '../domain/__fixtures__/agenttrace'
import {
  buildTokenChart,
  formatCoverage,
  formatDuration,
  formatEventPosition,
  formatNullableNumber,
  groupObservationLanes,
  importObservationText,
  paginateItems,
  sourceTrustLabel,
  truncateObservationText,
  type ChartDatum,
  type ObservationLaneId,
} from '../domain/observation-dashboard'
import { MAX_OBSERVATION_BYTES, type ObservationEvent, type ObservationEventKind, type ObservationRun, type ValidationIssue } from '../domain/observation'
import type { ObservationMetrics } from '../domain/observation-metrics'

type ImportState = 'empty' | 'loading' | 'invalid' | 'ready' | 'partial'
type EventFilter = 'all' | ObservationEventKind
type ChartKey = 'input' | 'output' | 'total'

const PAGE_SIZE = 100
const PLAY_INTERVAL_MS = 900

const state = ref<ImportState>('empty')
const run = ref<ObservationRun | null>(null)
const metrics = ref<ObservationMetrics | null>(null)
const inputFormat = ref('')
const fileName = ref('')
const errors = ref<readonly ValidationIssue[]>([])
const selectedLaneId = ref<ObservationLaneId | null>(null)
const selectedEventId = ref<string | null>(null)
const eventFilter = ref<EventFilter>('all')
const currentPage = ref(1)
const chartPage = ref(1)
const playing = ref(false)
let timer: ReturnType<typeof setInterval> | null = null
let importGeneration = 0

const lanes = computed(() => run.value ? groupObservationLanes(run.value.events) : [])
const selectedLane = computed(() => lanes.value.find((lane) => lane.id === selectedLaneId.value) ?? null)
const activeEvents = computed(() => {
  const events = selectedLane.value?.events ?? []
  return eventFilter.value === 'all' ? events : events.filter((event) => event.kind === eventFilter.value)
})
const eventPage = computed(() => paginateItems(activeEvents.value, currentPage.value, PAGE_SIZE))
const selectedEvent = computed(() => run.value?.events.find((event) => event.id === selectedEventId.value) ?? null)
const selectedDetail = computed(() => truncateObservationText(selectedEvent.value?.detail ?? null))
const chartPagination = computed(() => paginateItems(metrics.value?.tokenSeries ?? [], chartPage.value, PAGE_SIZE))
const chart = computed(() => buildTokenChart(
  chartPagination.value.items,
  run.value?.events ?? [],
  metrics.value?.warnings ?? [],
))
const trustLabel = computed(() => run.value ? sourceTrustLabel(run.value) : '')
const partialOrder = computed(() => lanes.value.length > 1)
const statusMessage = computed(() => ({
  empty: 'Nenhum arquivo importado.',
  loading: 'Lendo arquivo.',
  invalid: 'Arquivo rejeitado.',
  ready: 'Arquivo validado.',
  partial: 'Arquivo validado com avisos.',
})[state.value])

function stopReplay(): void {
  if (timer !== null) clearInterval(timer)
  timer = null
  playing.value = false
}

function clearReport(): void {
  stopReplay()
  run.value = null
  metrics.value = null
  inputFormat.value = ''
  errors.value = []
  selectedLaneId.value = null
  selectedEventId.value = null
  eventFilter.value = 'all'
  currentPage.value = 1
  chartPage.value = 1
}

function applyImport(input: string, label: string): void {
  clearReport()
  fileName.value = label
  const result = importObservationText(input)
  if (!result.ok) {
    errors.value = result.errors.slice(0, 6)
    state.value = 'invalid'
    return
  }
  run.value = result.run
  metrics.value = result.metrics
  inputFormat.value = result.format === 'agenttrace' ? 'AgentTrace' : 'LCP Evidence v1'
  state.value = result.state
  const firstLane = groupObservationLanes(result.run.events)[0]
  selectedLaneId.value = firstLane?.id ?? null
  selectedEventId.value = firstLane?.events[0]?.id ?? null
}

async function handleFile(event: Event): Promise<void> {
  const input = event.target as HTMLInputElement
  const file = input.files?.[0]
  const generation = ++importGeneration
  clearReport()
  fileName.value = file?.name ?? ''
  if (!file) {
    state.value = 'empty'
    return
  }
  if (file.size === 0) {
    errors.value = [{ severity: 'error', code: 'EMPTY_FILE', path: '$', message: 'The selected file is empty.' }]
    state.value = 'invalid'
    input.value = ''
    return
  }
  if (file.size > MAX_OBSERVATION_BYTES) {
    errors.value = [{
      severity: 'error',
      code: 'INPUT_TOO_LARGE',
      path: '$',
      message: `File exceeds the ${MAX_OBSERVATION_BYTES}-byte limit.`,
    }]
    state.value = 'invalid'
    input.value = ''
    return
  }

  state.value = 'loading'
  try {
    const text = await file.text()
    if (generation !== importGeneration) return
    applyImport(text, file.name)
  } catch {
    if (generation !== importGeneration) return
    errors.value = [{ severity: 'error', code: 'FILE_READ_FAILED', path: '$', message: 'The file could not be read.' }]
    state.value = 'invalid'
  } finally {
    input.value = ''
  }
}

function loadSyntheticExample(): void {
  importGeneration += 1
  applyImport(JSON.stringify(syntheticAgentTraceFixture), 'exemplo-sintetico-agenttrace.json')
}

function selectEvent(event: ObservationEvent): void {
  selectedEventId.value = event.id
  const index = activeEvents.value.findIndex((item) => item.id === event.id)
  if (index >= 0) currentPage.value = Math.floor(index / PAGE_SIZE) + 1
}

function moveSelection(direction: -1 | 1): void {
  const events = activeEvents.value
  if (events.length === 0) return
  const currentIndex = events.findIndex((event) => event.id === selectedEventId.value)
  const baseIndex = currentIndex < 0 ? 0 : currentIndex
  const nextIndex = Math.min(events.length - 1, Math.max(0, baseIndex + direction))
  selectEvent(events[nextIndex])
  if (nextIndex === events.length - 1 && direction === 1) stopReplay()
}

function playReplay(): void {
  if (timer !== null || activeEvents.value.length === 0) return
  const currentIndex = activeEvents.value.findIndex((event) => event.id === selectedEventId.value)
  if (currentIndex < 0 || currentIndex >= activeEvents.value.length - 1) selectEvent(activeEvents.value[0])
  playing.value = true
  timer = setInterval(() => moveSelection(1), PLAY_INTERVAL_MS)
}

function changePage(direction: -1 | 1): void {
  stopReplay()
  currentPage.value = Math.min(eventPage.value.pageCount, Math.max(1, eventPage.value.page + direction))
}

function changeChartPage(direction: -1 | 1): void {
  chartPage.value = Math.min(chartPagination.value.pageCount, Math.max(1, chartPagination.value.page + direction))
}

function chartX(point: ChartDatum): number {
  const count = Math.max(1, chart.value.points.length - 1)
  return 44 + (point.index / count) * 712
}

function chartY(value: number | null): number {
  const max = chart.value.maxValue
  if (value === null || max === null || max === 0) return 218
  return 218 - (value / max) * 174
}

function polylinePoints(segment: readonly ChartDatum[], key: ChartKey): string {
  return segment.map((point) => `${chartX(point)},${chartY(point[key])}`).join(' ')
}

function positionLabel(event: ObservationEvent): string {
  return formatEventPosition(event, selectedLane.value?.events ?? [])
}

watch([selectedLaneId, eventFilter], () => {
  stopReplay()
  currentPage.value = 1
  selectedEventId.value = activeEvents.value[0]?.id ?? null
})

onUnmounted(() => {
  importGeneration += 1
  stopReplay()
})
</script>

<template>
  <section id="main-content" class="observability-hero" aria-labelledby="observability-title">
    <div>
      <h1 id="observability-title">Observabilidade</h1>
      <p class="lede">AgentTrace ou LCP Evidence v1 · processamento local, sem upload</p>
    </div>
    <div class="import-actions">
      <label class="file-label" for="observation-file">Arquivo JSON local</label>
      <input id="observation-file" class="file-input" type="file" accept=".json,application/json" @change="handleFile">
      <button class="button ghost" type="button" @click="loadSyntheticExample">Exemplo sintético</button>
      <small>Máximo 5 MiB · um objeto por arquivo</small>
    </div>
  </section>

  <section class="import-status" :class="state" aria-live="polite" :role="state === 'invalid' ? 'alert' : 'status'">
    <div><strong>{{ statusMessage }}</strong><span v-if="fileName">{{ fileName }}</span></div>
    <ul v-if="state === 'invalid'" class="issue-list">
      <li v-for="issue in errors" :key="`${issue.code}-${issue.path}`"><code>{{ issue.code }}</code> · {{ issue.path }} · {{ issue.message }}</li>
    </ul>
  </section>

  <template v-if="run && metrics">
    <section class="metadata" aria-label="Metadados da observação">
      <span>Formato: {{ inputFormat }}</span><span>Execução: {{ run.runId }}</span><span>Fonte: {{ run.source.producer }}</span><span>Agente: {{ run.agent.name ?? '—' }}</span><span>Modelo: {{ run.agent.model ?? '—' }}</span>
    </section>

    <section class="trust-banner" :class="run.sourceKind">
      <strong>{{ trustLabel }}</strong>
      <p>Origem declarada; conteúdo e sanitização não verificados.</p>
    </section>

    <section class="observation-kpis" aria-label="Indicadores observados">
      <article><span>Eventos</span><strong>{{ metrics.summary.eventCount }}</strong></article>
      <article><span>Gerações LLM</span><strong>{{ metrics.summary.modelStepCount }}</strong></article>
      <article><span>Ferramentas</span><strong>{{ metrics.summary.toolCallCount }}</strong></article>
      <article><span>Mensagens</span><strong>{{ metrics.summary.messageCount }}</strong></article>
      <article><span>Erros explícitos</span><strong>{{ metrics.summary.explicitErrorCount }}</strong></article>
      <article><span>Status desconhecidos</span><strong>{{ metrics.summary.unknownStatusCount }}</strong></article>
      <article class="wide"><span>Duração da execução</span><strong>{{ formatDuration(metrics) }}</strong></article>
      <article class="wide"><span>Tokens de entrada</span><strong>{{ formatCoverage(metrics.summary.inputTokens) }}</strong></article>
      <article class="wide"><span>Tokens de saída</span><strong>{{ formatCoverage(metrics.summary.outputTokens) }}</strong></article>
      <article><span>Total de tokens</span><strong>{{ formatNullableNumber(metrics.summary.totalTokens, 0) }}</strong></article>
      <article><span>Custo reportado</span><strong>{{ metrics.summary.reportedCostUsd ?? '—' }}</strong></article>
    </section>

    <section v-if="metrics.warnings.length" class="warning-panel" aria-label="Advertências da observação">
      <strong>Avisos ({{ metrics.warnings.length }})</strong>
      <ul><li v-for="warning in metrics.warnings" :key="warning"><code>{{ warning }}</code></li></ul>
    </section>

    <section class="chart-card" aria-labelledby="token-chart-title">
      <div class="section-heading">
        <h2 id="token-chart-title">Tokens por etapa LLM</h2>
        <span>{{ chartPagination.total }} etapas · {{ chart.usesSerializationOrder ? 'ordem seq declarada' : 'ordem ordinal' }}</span>
      </div>
      <p class="chart-note">Eixo por etapa, não por tempo; lacunas interrompem as linhas.</p>
      <div v-if="chart.points.length === 0 || chart.maxValue === null" class="chart-empty">Consumo acumulado indisponível para esta observação.</div>
      <template v-else>
        <div class="chart-legend"><span class="input-line">Entrada</span><span class="output-line">Saída</span><span class="total-line">Total</span></div>
        <svg class="token-chart" viewBox="0 0 800 250" role="img" aria-label="Consumo acumulado de tokens por etapa registrada">
          <line x1="44" y1="218" x2="756" y2="218" class="axis" />
          <line x1="44" y1="44" x2="44" y2="218" class="axis" />
          <polyline v-for="(segment, index) in chart.inputSegments" :key="`input-${index}`" :points="polylinePoints(segment, 'input')" class="chart-series input" />
          <polyline v-for="(segment, index) in chart.outputSegments" :key="`output-${index}`" :points="polylinePoints(segment, 'output')" class="chart-series output" />
          <polyline v-for="(segment, index) in chart.totalSegments" :key="`total-${index}`" :points="polylinePoints(segment, 'total')" class="chart-series total" />
          <template v-for="point in chart.points" :key="point.eventId">
            <circle v-if="point.input !== null" :cx="chartX(point)" :cy="chartY(point.input)" r="3" class="chart-dot input" />
            <circle v-if="point.output !== null" :cx="chartX(point)" :cy="chartY(point.output)" r="3" class="chart-dot output" />
            <circle v-if="point.total !== null" :cx="chartX(point)" :cy="chartY(point.total)" r="3" class="chart-dot total" />
          </template>
        </svg>
        <div class="chart-labels"><span>{{ chart.points[0]?.label }}</span><span>{{ chart.points[chart.points.length - 1]?.label }}</span></div>
      </template>
      <div v-if="chartPagination.pageCount > 1" class="pagination" aria-label="Paginação do gráfico">
        <button type="button" :disabled="chartPagination.page === 1" @click="changeChartPage(-1)">Anterior</button>
        <span>Página {{ chartPagination.page }} de {{ chartPagination.pageCount }} · até {{ PAGE_SIZE }} etapas visíveis</span>
        <button type="button" :disabled="chartPagination.page === chartPagination.pageCount" @click="changeChartPage(1)">Próxima</button>
      </div>
    </section>

    <section class="lane-card" aria-labelledby="replay-title">
      <div class="section-heading">
        <h2 id="replay-title">Eventos por faixa</h2>
        <span>{{ run.events.length }} eventos totais</span>
      </div>
      <p v-if="partialOrder" class="partial-order visible">Ordem parcial: as faixas não têm cronologia comum. Reprodução a cada {{ PLAY_INTERVAL_MS }} ms.</p>
      <p v-else class="partial-order">Reprodução a cada {{ PLAY_INTERVAL_MS }} ms, sem usar a duração reportada.</p>
      <div class="lane-switcher" role="group" aria-label="Selecionar faixa de eventos">
        <button v-for="lane in lanes" :key="lane.id" type="button" :class="{ active: selectedLaneId === lane.id }" :aria-pressed="selectedLaneId === lane.id" @click="selectedLaneId = lane.id">
          {{ lane.label }} <span>{{ lane.events.length }}</span>
        </button>
      </div>
      <p v-if="selectedLane" class="lane-description">{{ selectedLane.description }}</p>

      <div class="replay-toolbar">
        <div class="replay-controls" role="group" aria-label="Controles de replay visual">
          <button type="button" :disabled="activeEvents.length === 0" @click="moveSelection(-1)">← Anterior</button>
          <button v-if="!playing" type="button" :disabled="activeEvents.length === 0" @click="playReplay">▶ Reproduzir</button>
          <button v-else type="button" @click="stopReplay">Ⅱ Pausar</button>
          <button type="button" :disabled="activeEvents.length === 0" @click="moveSelection(1)">Próximo →</button>
        </div>
        <label>Filtrar tipo
          <select v-model="eventFilter">
            <option value="all">Todos</option><option value="model">Modelo</option><option value="tool">Ferramenta</option><option value="message">Mensagem</option><option value="system">Sistema</option>
          </select>
        </label>
      </div>

      <div class="replay-grid">
        <div class="event-list" role="group" aria-label="Eventos visíveis da faixa">
          <button v-for="event in eventPage.items" :key="event.id" type="button" :aria-pressed="selectedEventId === event.id" :class="['event-row', event.status, { selected: selectedEventId === event.id }]" @click="selectEvent(event)">
            <span class="event-seq">{{ event.seq }}</span><span><strong>{{ event.name }}</strong><small>{{ event.kind }} · {{ event.status }}</small></span><code>{{ positionLabel(event) }}</code>
          </button>
          <p v-if="activeEvents.length === 0" class="empty-list">Nenhum evento nesta faixa para o filtro selecionado.</p>
          <div v-if="eventPage.pageCount > 1" class="pagination">
            <button type="button" :disabled="eventPage.page === 1" @click="changePage(-1)">Anterior</button>
            <span>Página {{ eventPage.page }} de {{ eventPage.pageCount }} · {{ eventPage.total }} registros</span>
            <button type="button" :disabled="eventPage.page === eventPage.pageCount" @click="changePage(1)">Próxima</button>
          </div>
        </div>

        <aside class="event-detail" aria-live="polite">
          <template v-if="selectedEvent">
            <h3>{{ selectedEvent.name }}</h3>
            <dl>
              <div><dt>ID</dt><dd><code>{{ selectedEvent.id }}</code></dd></div>
              <div><dt>Tipo / status</dt><dd>{{ selectedEvent.kind }} / {{ selectedEvent.status }}</dd></div>
              <div><dt>Pai</dt><dd><code>{{ selectedEvent.parentId ?? '—' }}</code></dd></div>
              <div><dt>Posição</dt><dd>{{ positionLabel(selectedEvent) }}</dd></div>
              <div><dt>Input / output</dt><dd>{{ formatNullableNumber(selectedEvent.usage?.inputTokens ?? null, 0) }} / {{ formatNullableNumber(selectedEvent.usage?.outputTokens ?? null, 0) }} tokens</dd></div>
              <div><dt>Duração da operação</dt><dd>{{ selectedEvent.usage?.durationMs === null || selectedEvent.usage?.durationMs === undefined ? '—' : `${formatNullableNumber(selectedEvent.usage.durationMs, 6)} ms` }}</dd></div>
              <div><dt>Custo reportado</dt><dd>{{ selectedEvent.usage?.costUsd ?? '—' }}</dd></div>
            </dl>
            <div class="event-detail-text"><strong>Conteúdo importado</strong><pre>{{ selectedDetail.text }}</pre><small v-if="selectedDetail.truncated">Truncado: {{ selectedDetail.originalLength }} caracteres no registro original.</small></div>
          </template>
          <template v-else><h3>Nenhum evento selecionado</h3></template>
        </aside>
      </div>
    </section>
  </template>
</template>
