import { parseAgentTrace } from './observation-agenttrace'
import { computeObservationMetrics, type ObservationMetrics } from './observation-metrics'
import { MAX_OBSERVATION_BYTES, type ObservationRun, type ValidationIssue } from './observation'

export interface TraceTelemetry {
  readonly userTimeS: number | null
  readonly systemTimeS: number | null
  readonly maxRssBytes: number | null
  readonly readBytes: number | null
  readonly writeBytes: number | null
}

export interface TraceSpanEvidence {
  readonly spanId: string
  readonly toolName: string
  readonly toolInput: string | null
  readonly toolOutput: string | null
  readonly startNs: number
  readonly endNs: number
  readonly durationMs: number | null
  readonly exitCode: number | null
  readonly telemetry: TraceTelemetry | null
}

export interface TraceRecord {
  readonly traceId: string
  readonly model: string | null
  readonly datasetName: string | null
  readonly taskId: string
  readonly prompt: string | null
  readonly timestampUtc: string | null
  readonly run: ObservationRun
  readonly metrics: ObservationMetrics
  readonly spans: readonly TraceSpanEvidence[]
}

export interface CollectionSource {
  readonly dataset: string
  readonly revision: string | null
  readonly revisionNote: string | null
  readonly path: string | null
  readonly localSha256: string | null
  readonly license: string | null
}

export interface TraceCollection {
  readonly source: CollectionSource
  readonly traces: readonly TraceRecord[]
}

export type CollectionParseResult =
  | { readonly ok: true; readonly value: TraceCollection }
  | { readonly ok: false; readonly errors: readonly ValidationIssue[] }

export interface ModelOverview {
  readonly model: string
  readonly traces: number
  readonly durationP50Ms: number | null
  readonly toolCalls: number
  readonly failures: number
}

export interface CollectionOverview {
  readonly traces: number
  readonly durationP50Ms: number | null
  readonly durationP95Ms: number | null
  readonly toolCalls: number
  readonly failures: number
  readonly models: readonly ModelOverview[]
}

export type DiagnosticKind = 'tool_error' | 'repeated_call' | 'duration_outlier' | 'top_contributor'

export interface TraceDiagnostic {
  readonly id: string
  readonly kind: DiagnosticKind
  readonly traceId: string
  readonly spanId: string | null
  readonly title: string
  readonly evidence: string
}

function isRecord(value: unknown): value is Record<string, unknown> {
  return typeof value === 'object' && value !== null && !Array.isArray(value)
}

function issue(code: string, path: string, message: string): ValidationIssue {
  return { severity: 'error', code, path, message }
}

function nullableString(value: unknown): string | null {
  return typeof value === 'string' && value.length > 0 ? value : null
}

function nullableNumber(value: unknown): number | null {
  return typeof value === 'number' && Number.isFinite(value) ? value : null
}

function parseSpan(value: unknown): TraceSpanEvidence | null {
  if (!isRecord(value) || typeof value.span_id !== 'string' || typeof value.tool_name !== 'string'
    || typeof value.start_ns !== 'number' || typeof value.end_ns !== 'number') return null
  const telemetry = isRecord(value.telemetry) ? {
    userTimeS: nullableNumber(value.telemetry.user_time_s),
    systemTimeS: nullableNumber(value.telemetry.system_time_s),
    maxRssBytes: nullableNumber(value.telemetry.max_rss_bytes),
    readBytes: nullableNumber(value.telemetry.read_bytes),
    writeBytes: nullableNumber(value.telemetry.write_bytes),
  } : null
  return {
    spanId: value.span_id,
    toolName: value.tool_name,
    toolInput: nullableString(value.tool_input),
    toolOutput: nullableString(value.tool_output),
    startNs: value.start_ns,
    endNs: value.end_ns,
    durationMs: nullableNumber(value.duration_ms),
    exitCode: nullableNumber(value.exit_code),
    telemetry,
  }
}

function defaultSource(): CollectionSource {
  return { dataset: 'pagarsky/agent-trace', revision: null, revisionNote: null, path: null, localSha256: null, license: null }
}

function parseSource(value: unknown): CollectionSource {
  if (!isRecord(value)) return defaultSource()
  return {
    dataset: nullableString(value.dataset) ?? 'pagarsky/agent-trace',
    revision: nullableString(value.revision),
    revisionNote: nullableString(value.revision_note),
    path: nullableString(value.path),
    localSha256: nullableString(value.local_sha256),
    license: nullableString(value.license),
  }
}

function parseObjects(input: string): { values: readonly unknown[]; source: CollectionSource } | null {
  try {
    const parsed = JSON.parse(input) as unknown
    if (isRecord(parsed) && Array.isArray(parsed.traces)) {
      return { values: parsed.traces, source: parseSource(parsed.source) }
    }
    return { values: [parsed], source: defaultSource() }
  } catch {
    const lines = input.split(/\r?\n/).filter((line) => line.trim().length > 0)
    if (lines.length < 2) return null
    try {
      return { values: lines.map((line) => JSON.parse(line) as unknown), source: defaultSource() }
    } catch {
      return null
    }
  }
}

export function parseAgentTraceCollection(input: string): CollectionParseResult {
  if (new TextEncoder().encode(input).byteLength > MAX_OBSERVATION_BYTES) {
    return { ok: false, errors: [issue('INPUT_TOO_LARGE', '$', `Input exceeds the ${MAX_OBSERVATION_BYTES}-byte limit.`)] }
  }
  const parsed = parseObjects(input)
  if (!parsed) return { ok: false, errors: [issue('INVALID_COLLECTION', '$', 'Expected AgentTrace JSON or JSONL.')] }
  const traces: TraceRecord[] = []
  const traceIds = new Set<string>()
  for (let index = 0; index < parsed.values.length; index += 1) {
    const raw = parsed.values[index]
    if (!isRecord(raw)) return { ok: false, errors: [issue('INVALID_TRACE', `$.traces[${index}]`, 'Expected an object.')] }
    const normalized = parseAgentTrace(JSON.stringify(raw))
    if (!normalized.ok) {
      return { ok: false, errors: normalized.errors.map((entry) => ({ ...entry, path: `$.traces[${index}]${entry.path.slice(1)}` })) }
    }
    if (traceIds.has(normalized.value.runId)) {
      return { ok: false, errors: [issue('DUPLICATE_TRACE_ID', `$.traces[${index}].trace_id`, 'Trace ID must be unique.')] }
    }
    traceIds.add(normalized.value.runId)
    const spans = Array.isArray(raw.spans) ? raw.spans.map(parseSpan).filter((span): span is TraceSpanEvidence => span !== null) : []
    traces.push({
      traceId: normalized.value.runId,
      model: normalized.value.agent.model,
      datasetName: nullableString(raw.dataset_name),
      taskId: raw.task_id === null || raw.task_id === undefined ? '—' : String(raw.task_id),
      prompt: nullableString(raw.prompt),
      timestampUtc: nullableString(raw.timestamp_utc),
      run: normalized.value,
      metrics: computeObservationMetrics(normalized.value),
      spans,
    })
  }
  if (traces.length === 0) return { ok: false, errors: [issue('EMPTY_COLLECTION', '$', 'No traces found.')] }
  return { ok: true, value: { source: parsed.source, traces } }
}

export function percentileNearestRank(values: readonly number[], percentile: number): number | null {
  if (values.length === 0) return null
  const sorted = [...values].sort((left, right) => left - right)
  const rank = Math.max(1, Math.ceil(Math.min(1, Math.max(0, percentile)) * sorted.length))
  return sorted[rank - 1] ?? null
}

function toolSpans(trace: TraceRecord): readonly TraceSpanEvidence[] {
  return trace.spans.filter((span) => span.toolName !== 'final_answer')
}

export function collectionOverview(collection: TraceCollection): CollectionOverview {
  const durations = collection.traces.map((trace) => trace.run.totalDurationMs).filter((value): value is number => value !== null)
  const modelNames = [...new Set(collection.traces.map((trace) => trace.model ?? 'Modelo não informado'))]
  const summarize = (traces: readonly TraceRecord[]): Omit<ModelOverview, 'model'> => ({
    traces: traces.length,
    durationP50Ms: percentileNearestRank(
      traces.map((trace) => trace.run.totalDurationMs).filter((value): value is number => value !== null), 0.5,
    ),
    toolCalls: traces.flatMap(toolSpans).length,
    failures: traces.flatMap(toolSpans).filter((span) => span.exitCode !== null && span.exitCode !== 0).length,
  })
  const total = summarize(collection.traces)
  return {
    ...total,
    durationP95Ms: percentileNearestRank(durations, 0.95),
    models: modelNames.map((model) => ({ model, ...summarize(collection.traces.filter((trace) => (trace.model ?? 'Modelo não informado') === model)) })),
  }
}

function median(values: readonly number[]): number {
  const sorted = [...values].sort((left, right) => left - right)
  const middle = Math.floor(sorted.length / 2)
  return sorted.length % 2 === 0 ? ((sorted[middle - 1] ?? 0) + (sorted[middle] ?? 0)) / 2 : (sorted[middle] ?? 0)
}

export function durationOutlierFence(traces: readonly TraceRecord[]): number | null {
  const values = traces.map((trace) => trace.run.totalDurationMs).filter((value): value is number => value !== null).sort((a, b) => a - b)
  if (values.length < 4) return null
  const middle = Math.floor(values.length / 2)
  const lower = values.slice(0, middle)
  const upper = values.slice(values.length % 2 === 0 ? middle : middle + 1)
  const q1 = median(lower)
  const q3 = median(upper)
  return q3 + 1.5 * (q3 - q1)
}

export function collectionDiagnostics(collection: TraceCollection): readonly TraceDiagnostic[] {
  const diagnostics: TraceDiagnostic[] = []
  for (const trace of collection.traces) {
    const spans = toolSpans(trace)
    for (const span of spans.filter((item) => item.exitCode !== null && item.exitCode !== 0)) {
      diagnostics.push({
        id: `error-${trace.traceId}-${span.spanId}`, kind: 'tool_error', traceId: trace.traceId, spanId: span.spanId,
        title: `${span.toolName} retornou exit code ${span.exitCode}`,
        evidence: `span ${span.spanId} · ${span.durationMs ?? 'duração não informada'} ms`,
      })
    }
    const calls = new Map<string, TraceSpanEvidence[]>()
    for (const span of spans) {
      const key = `${span.toolName}\u0000${span.toolInput ?? ''}`
      calls.set(key, [...(calls.get(key) ?? []), span])
    }
    for (const repeated of calls.values()) {
      if (repeated.length < 2) continue
      diagnostics.push({
        id: `repeat-${trace.traceId}-${repeated[0]!.spanId}`, kind: 'repeated_call', traceId: trace.traceId,
        spanId: repeated[0]!.spanId, title: `Chamada idêntica repetida ${repeated.length} vezes`,
        evidence: `${repeated[0]!.toolName} · spans ${repeated.map((span) => span.spanId).join(', ')}`,
      })
    }
  }
  const fence = durationOutlierFence(collection.traces)
  if (fence !== null) {
    for (const trace of collection.traces.filter((item) => item.run.totalDurationMs !== null && item.run.totalDurationMs > fence)) {
      diagnostics.push({
        id: `outlier-${trace.traceId}`, kind: 'duration_outlier', traceId: trace.traceId, spanId: null,
        title: 'Duração total atípica', evidence: `${trace.run.totalDurationMs} ms > limite Tukey ${fence} ms`,
      })
    }
  }
  const contributors = collection.traces.flatMap((trace) => toolSpans(trace).map((span) => ({ trace, span })))
    .filter((item) => item.span.durationMs !== null)
    .sort((left, right) => (right.span.durationMs ?? 0) - (left.span.durationMs ?? 0)).slice(0, 5)
  for (const { trace, span } of contributors) {
    const share = trace.run.totalDurationMs && span.durationMs !== null ? (span.durationMs / trace.run.totalDurationMs) * 100 : null
    diagnostics.push({
      id: `contributor-${trace.traceId}-${span.spanId}`, kind: 'top_contributor', traceId: trace.traceId, spanId: span.spanId,
      title: `${span.toolName} entre as operações medidas mais longas`,
      evidence: `${span.durationMs} ms${share === null ? '' : ` · ${share.toFixed(4)}% da duração total reportada`}`,
    })
  }
  return diagnostics
}

export function spanEvidence(trace: TraceRecord | null, eventId: string | null): TraceSpanEvidence | null {
  if (!trace || !eventId) return null
  return trace.spans.find((span) => span.spanId === eventId) ?? null
}
