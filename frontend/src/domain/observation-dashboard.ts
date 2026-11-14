import { parseAgentTrace } from './observation-agenttrace'
import { computeObservationMetrics, type KnownNumber, type ObservationMetrics, type TokenPoint } from './observation-metrics'
import {
  MAX_OBSERVATION_BYTES,
  parseLcpObservation,
  type ObservationEvent,
  type ObservationRun,
  type ParseResult,
  type ValidationIssue,
} from './observation'

export type DashboardInputFormat = 'lcp_evidence_v1' | 'agenttrace'
export type ObservationLaneId = 'llm_steps' | 'spans' | 'unpositioned'

export interface ObservationImportSuccess {
  readonly ok: true
  readonly format: DashboardInputFormat
  readonly run: ObservationRun
  readonly metrics: ObservationMetrics
  readonly state: 'ready' | 'partial'
}

export type ObservationImportResult =
  | ObservationImportSuccess
  | { readonly ok: false; readonly errors: readonly ValidationIssue[] }

export interface ObservationLane {
  readonly id: ObservationLaneId
  readonly label: string
  readonly description: string
  readonly events: readonly ObservationEvent[]
}

export interface ChartDatum {
  readonly eventId: string
  readonly index: number
  readonly label: string
  readonly input: number | null
  readonly output: number | null
  readonly total: number | null
}

export interface TokenChartModel {
  readonly points: readonly ChartDatum[]
  readonly inputSegments: readonly (readonly ChartDatum[])[]
  readonly outputSegments: readonly (readonly ChartDatum[])[]
  readonly totalSegments: readonly (readonly ChartDatum[])[]
  readonly maxValue: number | null
  readonly usesSerializationOrder: boolean
}

export interface TruncatedText {
  readonly text: string
  readonly truncated: boolean
  readonly originalLength: number
}

function isRecord(value: unknown): value is Record<string, unknown> {
  return typeof value === 'object' && value !== null && !Array.isArray(value)
}

function dashboardError(code: string, path: string, message: string): ValidationIssue {
  return { severity: 'error', code, path, message }
}

function isPartial(metrics: ObservationMetrics): boolean {
  const { summary } = metrics
  return metrics.warnings.length > 0
    || summary.duration.basis === 'unavailable'
    || summary.inputTokens.known < summary.inputTokens.eligible
    || summary.outputTokens.known < summary.outputTokens.eligible
}

export function importObservationText(input: string): ObservationImportResult {
  if (new TextEncoder().encode(input).byteLength > MAX_OBSERVATION_BYTES) {
    return {
      ok: false,
      errors: [dashboardError('INPUT_TOO_LARGE', '$', `Input exceeds the ${MAX_OBSERVATION_BYTES}-byte limit.`)],
    }
  }

  let parsed: unknown
  try {
    parsed = JSON.parse(input) as unknown
  } catch {
    const invalid = parseAgentTrace(input)
    return invalid.ok
      ? { ok: false, errors: [dashboardError('UNKNOWN_INPUT_FORMAT', '$', 'Input format is not supported.')] }
      : invalid
  }

  if (!isRecord(parsed)) {
    return { ok: false, errors: [dashboardError('INVALID_ROOT', '$', 'Expected one JSON object.')] }
  }

  const hasSchema = Object.prototype.hasOwnProperty.call(parsed, 'schema_version')
  const hasAgentTraceArrays = Array.isArray(parsed.spans) && Array.isArray(parsed.llm_steps)
  if (hasSchema && hasAgentTraceArrays) {
    return {
      ok: false,
      errors: [dashboardError('AMBIGUOUS_INPUT_FORMAT', '$', 'Input matches more than one supported format.')],
    }
  }

  let format: DashboardInputFormat
  let result: ParseResult
  if (hasSchema) {
    format = 'lcp_evidence_v1'
    result = parseLcpObservation(input)
  } else if (hasAgentTraceArrays) {
    format = 'agenttrace'
    result = parseAgentTrace(input)
  } else {
    return {
      ok: false,
      errors: [dashboardError('UNKNOWN_INPUT_FORMAT', '$', 'Expected LCP Evidence v1 or one AgentTrace object.')],
    }
  }

  if (!result.ok) return result
  const metrics = computeObservationMetrics(result.value)
  return {
    ok: true,
    format,
    run: result.value,
    metrics,
    state: isPartial(metrics) ? 'partial' : 'ready',
  }
}

export function sourceTrustLabel(run: ObservationRun): string {
  if (run.sourceKind === 'self_report') return 'AUTORRELATO'
  if (run.sourceKind === 'fixture') return 'DADOS SINTÉTICOS'
  return 'TRACE EXTERNO — NÃO AUTENTICADO'
}

export function groupObservationLanes(events: readonly ObservationEvent[]): readonly ObservationLane[] {
  const llmSteps = events
    .filter((event) => event.position?.basis === 'ordinal')
    .sort((left, right) => {
      const leftOrdinal = left.position?.basis === 'ordinal' ? left.position.ordinal : 0
      const rightOrdinal = right.position?.basis === 'ordinal' ? right.position.ordinal : 0
      return leftOrdinal - rightOrdinal || left.seq - right.seq
    })
  const spans = events
    .filter((event) => event.position?.basis === 'monotonic_ns')
    .sort((left, right) => {
      const leftStart = left.position?.basis === 'monotonic_ns' ? left.position.startNs : 0
      const rightStart = right.position?.basis === 'monotonic_ns' ? right.position.startNs : 0
      return leftStart - rightStart || left.seq - right.seq
    })
  const unpositioned = events.filter((event) => event.position === null).sort((left, right) => left.seq - right.seq)

  const lanes: ObservationLane[] = []
  if (llmSteps.length > 0) {
    lanes.push({
      id: 'llm_steps',
      label: 'Gerações LLM · ordem ordinal',
      description: 'Passos discretos; não representam timestamps nem compartilham relógio com spans.',
      events: llmSteps,
    })
  }
  if (spans.length > 0) {
    lanes.push({
      id: 'spans',
      label: 'Spans · relógio monotônico',
      description: 'Posições relativas somente dentro desta faixa; não são datas UTC.',
      events: spans,
    })
  }
  if (unpositioned.length > 0) {
    lanes.push({
      id: 'unpositioned',
      label: 'Sem posição observável · ordem declarada (seq)',
      description: 'A sequência declarada organiza os registros sem fabricar tempo.',
      events: unpositioned,
    })
  }
  return lanes
}

function contiguousSegments(
  points: readonly ChartDatum[],
  key: 'input' | 'output' | 'total',
): readonly (readonly ChartDatum[])[] {
  const segments: ChartDatum[][] = []
  let current: ChartDatum[] = []
  for (const point of points) {
    if (point[key] === null) {
      if (current.length > 0) segments.push(current)
      current = []
    } else {
      current.push(point)
    }
  }
  if (current.length > 0) segments.push(current)
  return segments
}

export function buildTokenChart(
  tokenSeries: readonly TokenPoint[],
  events: readonly ObservationEvent[],
  warnings: readonly string[],
): TokenChartModel {
  const eventsById = new Map(events.map((event) => [event.id, event] as const))
  const points = tokenSeries.map((point, index): ChartDatum => {
    const event = eventsById.get(point.eventId)
    return {
      eventId: point.eventId,
      index,
      label: point.ordinal === null ? `seq ${event?.seq ?? index + 1}` : `etapa ${point.ordinal}`,
      input: point.cumulativeInputTokens,
      output: point.cumulativeOutputTokens,
      total: point.cumulativeTotalTokens,
    }
  })
  const values = points.flatMap((point) => [point.input, point.output, point.total])
    .filter((value): value is number => value !== null)
  return {
    points,
    inputSegments: contiguousSegments(points, 'input'),
    outputSegments: contiguousSegments(points, 'output'),
    totalSegments: contiguousSegments(points, 'total'),
    maxValue: values.length === 0 ? null : Math.max(...values),
    usesSerializationOrder: warnings.includes('TOKEN_SERIES_SERIALIZATION_ORDER'),
  }
}

export function formatNullableNumber(value: number | null, maximumFractionDigits = 3): string {
  if (value === null) return '—'
  return new Intl.NumberFormat('pt-BR', { maximumFractionDigits }).format(value)
}

export function formatCoverage(metric: KnownNumber): string {
  return `${formatNullableNumber(metric.value, 0)} · cobertura ${metric.known}/${metric.eligible}`
}

export function formatDuration(metrics: ObservationMetrics): string {
  const { duration } = metrics.summary
  if (duration.valueMs === null) return '—'
  const basis = duration.basis === 'reported' ? 'reportada' : 'derivada'
  return `${formatNullableNumber(duration.valueMs, 6)} ms · ${basis}`
}

export function truncateObservationText(value: string | null, limit = 600): TruncatedText {
  if (value === null) return { text: '—', truncated: false, originalLength: 0 }
  if (value.length <= limit) return { text: value, truncated: false, originalLength: value.length }
  return { text: `${value.slice(0, limit)}…`, truncated: true, originalLength: value.length }
}

export function paginateItems<T>(items: readonly T[], page: number, pageSize = 100): {
  readonly items: readonly T[]
  readonly page: number
  readonly pageCount: number
  readonly total: number
} {
  const safePageSize = Math.max(1, Math.floor(pageSize))
  const pageCount = Math.max(1, Math.ceil(items.length / safePageSize))
  const safePage = Math.min(pageCount, Math.max(1, Math.floor(page)))
  const start = (safePage - 1) * safePageSize
  return { items: items.slice(start, start + safePageSize), page: safePage, pageCount, total: items.length }
}

export function formatEventPosition(event: ObservationEvent, laneEvents: readonly ObservationEvent[]): string {
  if (event.position?.basis === 'ordinal') return `Etapa ordinal ${event.position.ordinal}`
  if (event.position?.basis === 'monotonic_ns') {
    const starts = laneEvents
      .map((item) => item.position?.basis === 'monotonic_ns' ? item.position.startNs : null)
      .filter((value): value is number => value !== null)
    const origin = starts.length === 0 ? event.position.startNs : Math.min(...starts)
    return `+${event.position.startNs - origin} ns → +${event.position.endNs - origin} ns (relativo à faixa)`
  }
  return `Ordem declarada seq ${event.seq}`
}
