export const LCP_OBSERVATION_SCHEMA_VERSION = 'lcp.observation.v1' as const
export const MAX_OBSERVATION_BYTES = 5 * 1024 * 1024
export const MAX_OBSERVATION_EVENTS = 10_000

export type ObservationSourceKind = 'trace' | 'self_report' | 'fixture'
export type ObservationEventKind = 'model' | 'tool' | 'message' | 'system'
export type ObservationEventStatus = 'success' | 'error' | 'unknown'

export interface ObservationSource {
  readonly kind: ObservationSourceKind
  readonly format: string
  readonly producer: string
  readonly reference: string | null
}

export interface ObservationAgent {
  readonly name: string
  readonly model: string | null
}

export interface ObservationUsage {
  readonly inputTokens: number | null
  readonly outputTokens: number | null
  readonly durationMs: number | null
  readonly costUsd: string | null
}

export interface ObservationEvent {
  readonly id: string
  readonly parentId: string | null
  readonly seq: number
  readonly kind: ObservationEventKind
  readonly name: string
  readonly startedAt: string | null
  readonly endedAt: string | null
  readonly status: ObservationEventStatus
  readonly usage: ObservationUsage | null
  readonly detail: string | null
}

export interface ValidationIssue {
  readonly severity: 'error' | 'warning'
  readonly code: string
  readonly path: string
  readonly message: string
}

export interface ObservationRun {
  readonly schemaVersion: typeof LCP_OBSERVATION_SCHEMA_VERSION
  readonly runId: string
  readonly source: ObservationSource
  readonly sourceKind: ObservationSourceKind
  readonly agent: ObservationAgent
  readonly startedAt: string | null
  readonly endedAt: string | null
  readonly totalDurationMs: number | null
  readonly events: readonly ObservationEvent[]
  readonly warnings: readonly ValidationIssue[]
}

export type ParseResult =
  | { readonly ok: true; readonly value: ObservationRun; readonly warnings: readonly ValidationIssue[] }
  | { readonly ok: false; readonly errors: readonly ValidationIssue[] }

const sourceKinds: readonly ObservationSourceKind[] = ['trace', 'self_report', 'fixture']
const eventKinds: readonly ObservationEventKind[] = ['model', 'tool', 'message', 'system']
const eventStatuses: readonly ObservationEventStatus[] = ['success', 'error', 'unknown']
const decimalPattern = /^(?:0|[1-9]\d*)(?:\.\d+)?$/
const isoWithTimezonePattern = /^(\d{4})-(\d{2})-(\d{2})T(\d{2}):(\d{2}):(\d{2})(?:\.(\d{1,9}))?(Z|[+-]\d{2}:\d{2})$/

function isRecord(value: unknown): value is Record<string, unknown> {
  return typeof value === 'object' && value !== null && !Array.isArray(value)
}

function error(code: string, path: string, message: string): ValidationIssue {
  return { severity: 'error', code, path, message }
}

function warning(code: string, path: string, message: string): ValidationIssue {
  return { severity: 'warning', code, path, message }
}

function requiredString(
  record: Record<string, unknown>,
  key: string,
  path: string,
  errors: ValidationIssue[],
): string | null {
  const value = record[key]
  if (typeof value !== 'string' || value.length === 0) {
    errors.push(error('REQUIRED_STRING', path, 'Expected a non-empty string.'))
    return null
  }
  return value
}

function nullableString(
  record: Record<string, unknown>,
  key: string,
  path: string,
  errors: ValidationIssue[],
): string | null {
  const value = record[key]
  if (value === undefined || value === null) return null
  if (typeof value !== 'string') {
    errors.push(error('INVALID_STRING', path, 'Expected a string or null.'))
    return null
  }
  return value
}

function nonNegativeNumber(
  record: Record<string, unknown>,
  key: string,
  path: string,
  errors: ValidationIssue[],
): number | null {
  const value = record[key]
  if (value === undefined || value === null) return null
  if (typeof value !== 'number' || !Number.isFinite(value) || value < 0) {
    errors.push(error('INVALID_NON_NEGATIVE_NUMBER', path, 'Expected a finite non-negative number or null.'))
    return null
  }
  return value
}

function isValidIsoTimestamp(value: string): boolean {
  const match = isoWithTimezonePattern.exec(value)
  if (!match) return false

  const [, yearText, monthText, dayText, hourText, minuteText, secondText, , timezone] = match
  const year = Number(yearText)
  const month = Number(monthText)
  const day = Number(dayText)
  const hour = Number(hourText)
  const minute = Number(minuteText)
  const second = Number(secondText)

  if (month < 1 || month > 12 || hour > 23 || minute > 59 || second > 59) return false
  if (timezone !== 'Z') {
    const offsetHour = Number(timezone.slice(1, 3))
    const offsetMinute = Number(timezone.slice(4, 6))
    if (offsetHour > 23 || offsetMinute > 59) return false
  }

  const daysInMonth = new Date(Date.UTC(year, month, 0)).getUTCDate()
  return day >= 1 && day <= daysInMonth && Number.isFinite(Date.parse(value))
}

function nullableTimestamp(
  record: Record<string, unknown>,
  key: string,
  path: string,
  errors: ValidationIssue[],
): string | null {
  const value = record[key]
  if (value === undefined || value === null) return null
  if (typeof value !== 'string' || !isValidIsoTimestamp(value)) {
    errors.push(error('INVALID_TIMESTAMP', path, 'Expected an ISO 8601 timestamp with a timezone or null.'))
    return null
  }
  return value
}

function enumValue<T extends string>(
  value: unknown,
  allowed: readonly T[],
  path: string,
  errors: ValidationIssue[],
): T | null {
  if (typeof value !== 'string' || !allowed.includes(value as T)) {
    errors.push(error('INVALID_ENUM', path, `Expected one of: ${allowed.join(', ')}.`))
    return null
  }
  return value as T
}

function parseUsage(value: unknown, path: string, errors: ValidationIssue[]): ObservationUsage | null {
  if (value === undefined || value === null) return null
  if (!isRecord(value)) {
    errors.push(error('INVALID_USAGE', path, 'Expected an object or null.'))
    return null
  }

  const inputTokens = nonNegativeNumber(value, 'input_tokens', `${path}.input_tokens`, errors)
  const outputTokens = nonNegativeNumber(value, 'output_tokens', `${path}.output_tokens`, errors)
  const durationMs = nonNegativeNumber(value, 'duration_ms', `${path}.duration_ms`, errors)
  const rawCostUsd = value.cost_usd
  let costUsd: string | null = null
  if (rawCostUsd !== undefined && rawCostUsd !== null) {
    if (typeof rawCostUsd !== 'string' || !decimalPattern.test(rawCostUsd)) {
      errors.push(error('INVALID_DECIMAL', `${path}.cost_usd`, 'Expected a non-negative decimal string or null.'))
    } else {
      costUsd = rawCostUsd
    }
  }

  return { inputTokens, outputTokens, durationMs, costUsd }
}

function parseEvent(value: unknown, index: number, errors: ValidationIssue[]): ObservationEvent | null {
  const path = `$.events[${index}]`
  if (!isRecord(value)) {
    errors.push(error('INVALID_EVENT', path, 'Expected an event object.'))
    return null
  }

  const id = requiredString(value, 'id', `${path}.id`, errors)
  const rawSeq = value.seq
  let seq: number | null = null
  if (typeof rawSeq !== 'number' || !Number.isInteger(rawSeq) || rawSeq <= 0) {
    errors.push(error('INVALID_SEQUENCE', `${path}.seq`, 'Expected a positive integer.'))
  } else {
    seq = rawSeq
  }
  const kind = enumValue(value.kind, eventKinds, `${path}.kind`, errors)
  const name = requiredString(value, 'name', `${path}.name`, errors)
  const status = enumValue(value.status, eventStatuses, `${path}.status`, errors)
  const parentId = nullableString(value, 'parent_id', `${path}.parent_id`, errors)
  const startedAt = nullableTimestamp(value, 'started_at', `${path}.started_at`, errors)
  const endedAt = nullableTimestamp(value, 'ended_at', `${path}.ended_at`, errors)
  const usage = parseUsage(value.usage, `${path}.usage`, errors)
  const detail = nullableString(value, 'detail', `${path}.detail`, errors)

  if (id === null || seq === null || kind === null || name === null || status === null) return null
  return { id, parentId, seq, kind, name, startedAt, endedAt, status, usage, detail }
}

function validateEventIdentityAndHierarchy(events: readonly ObservationEvent[], errors: ValidationIssue[]): void {
  const idIndexes = new Map<string, number>()
  const seqIndexes = new Map<number, number>()

  events.forEach((event, index) => {
    const previousIdIndex = idIndexes.get(event.id)
    if (previousIdIndex !== undefined) {
      errors.push(error('DUPLICATE_EVENT_ID', `$.events[${index}].id`, `Event id duplicates $.events[${previousIdIndex}].id.`))
    } else {
      idIndexes.set(event.id, index)
    }

    const previousSeqIndex = seqIndexes.get(event.seq)
    if (previousSeqIndex !== undefined) {
      errors.push(error('DUPLICATE_EVENT_SEQUENCE', `$.events[${index}].seq`, `Event sequence duplicates $.events[${previousSeqIndex}].seq.`))
    } else {
      seqIndexes.set(event.seq, index)
    }
  })

  const parentById = new Map<string, string | null>()
  events.forEach((event, index) => {
    parentById.set(event.id, event.parentId)
    if (event.parentId !== null && !idIndexes.has(event.parentId)) {
      errors.push(error('UNKNOWN_PARENT', `$.events[${index}].parent_id`, 'Parent event does not exist in this run.'))
    }
  })

  const complete = new Set<string>()
  const visiting = new Set<string>()
  const reportedCycles = new Set<string>()

  const visit = (id: string): void => {
    if (complete.has(id)) return
    if (visiting.has(id)) {
      if (!reportedCycles.has(id)) {
        const index = idIndexes.get(id)
        errors.push(error('CYCLIC_EVENT_HIERARCHY', `$.events[${index ?? 0}].parent_id`, 'Event hierarchy contains a cycle.'))
        reportedCycles.add(id)
      }
      return
    }

    visiting.add(id)
    const parentId = parentById.get(id)
    if (parentId !== null && parentId !== undefined && parentById.has(parentId)) visit(parentId)
    visiting.delete(id)
    complete.add(id)
  }

  for (const id of parentById.keys()) visit(id)
}

function temporalWarnings(
  startedAt: string | null,
  endedAt: string | null,
  totalDurationMs: number | null,
): ValidationIssue[] {
  if (startedAt === null || endedAt === null) return []

  const intervalMs = Date.parse(endedAt) - Date.parse(startedAt)
  const warnings: ValidationIssue[] = []
  if (intervalMs < 0) {
    warnings.push(warning('TIMESTAMP_ORDER', '$.ended_at', 'Run end precedes run start.'))
  }
  if (totalDurationMs !== null && totalDurationMs !== intervalMs) {
    warnings.push(warning(
      'TOTAL_DURATION_MISMATCH',
      '$.total_duration_ms',
      'Reported total duration differs from the comparable timestamp interval.',
    ))
  }
  return warnings
}

export function parseLcpObservation(input: string): ParseResult {
  const inputBytes = new TextEncoder().encode(input).byteLength
  if (inputBytes > MAX_OBSERVATION_BYTES) {
    return {
      ok: false,
      errors: [error('INPUT_TOO_LARGE', '$', `Input exceeds the ${MAX_OBSERVATION_BYTES}-byte limit.`)],
    }
  }

  let parsed: unknown
  try {
    parsed = JSON.parse(input) as unknown
  } catch {
    return { ok: false, errors: [error('INVALID_JSON', '$', 'Input is not valid JSON.')] }
  }

  if (!isRecord(parsed)) {
    return { ok: false, errors: [error('INVALID_ROOT', '$', 'Expected a JSON object.')] }
  }

  if (!Array.isArray(parsed.events)) {
    return { ok: false, errors: [error('REQUIRED_EVENTS', '$.events', 'Expected an events array.')] }
  }
  if (parsed.events.length > MAX_OBSERVATION_EVENTS) {
    return {
      ok: false,
      errors: [error('TOO_MANY_EVENTS', '$.events', `Event count exceeds the ${MAX_OBSERVATION_EVENTS}-event limit.`)],
    }
  }

  const errors: ValidationIssue[] = []
  const schemaVersion = parsed.schema_version
  if (schemaVersion !== LCP_OBSERVATION_SCHEMA_VERSION) {
    errors.push(error('UNSUPPORTED_SCHEMA_VERSION', '$.schema_version', `Expected ${LCP_OBSERVATION_SCHEMA_VERSION}.`))
  }
  const runId = requiredString(parsed, 'run_id', '$.run_id', errors)

  const rawSource = parsed.source
  let source: ObservationSource | null = null
  if (!isRecord(rawSource)) {
    errors.push(error('REQUIRED_SOURCE', '$.source', 'Expected a source object.'))
  } else {
    const kind = enumValue(rawSource.kind, sourceKinds, '$.source.kind', errors)
    const format = requiredString(rawSource, 'format', '$.source.format', errors)
    const producer = requiredString(rawSource, 'producer', '$.source.producer', errors)
    const reference = nullableString(rawSource, 'reference', '$.source.reference', errors)
    if (kind !== null && format !== null && producer !== null) source = { kind, format, producer, reference }
  }

  const rawAgent = parsed.agent
  let agent: ObservationAgent | null = null
  if (!isRecord(rawAgent)) {
    errors.push(error('REQUIRED_AGENT', '$.agent', 'Expected an agent object.'))
  } else {
    const name = requiredString(rawAgent, 'name', '$.agent.name', errors)
    const model = nullableString(rawAgent, 'model', '$.agent.model', errors)
    if (name !== null) agent = { name, model }
  }

  const startedAt = nullableTimestamp(parsed, 'started_at', '$.started_at', errors)
  const endedAt = nullableTimestamp(parsed, 'ended_at', '$.ended_at', errors)
  const totalDurationMs = nonNegativeNumber(parsed, 'total_duration_ms', '$.total_duration_ms', errors)
  const events = parsed.events
    .map((event, index) => parseEvent(event, index, errors))
    .filter((event): event is ObservationEvent => event !== null)

  validateEventIdentityAndHierarchy(events, errors)
  if (errors.length > 0 || runId === null || source === null || agent === null) return { ok: false, errors }

  const warnings = temporalWarnings(startedAt, endedAt, totalDurationMs)
  if (events.length === 0) {
    warnings.push(warning('EMPTY_EVENTS', '$.events', 'The run has no events; observability is limited.'))
  }
  if (source.kind === 'self_report') {
    warnings.push(warning('SELF_REPORTED_EVIDENCE', '$.source.kind', 'Evidence is self-reported, not independently observed.'))
  }

  const normalizedEvents = [...events].sort((left, right) => left.seq - right.seq)
  const value: ObservationRun = {
    schemaVersion: LCP_OBSERVATION_SCHEMA_VERSION,
    runId,
    source,
    sourceKind: source.kind,
    agent,
    startedAt,
    endedAt,
    totalDurationMs,
    events: normalizedEvents,
    warnings,
  }
  return { ok: true, value, warnings }
}
