import {
  LCP_OBSERVATION_SCHEMA_VERSION,
  MAX_OBSERVATION_BYTES,
  MAX_OBSERVATION_EVENTS,
  parseLcpObservation,
  type ObservationEventStatus,
  type ParseResult,
  type ValidationIssue,
} from './observation'

export const AGENTTRACE_ADAPTER_FORMAT = 'agenttrace.lcp-adapter.v1' as const
export type ObservationInputFormat = typeof LCP_OBSERVATION_SCHEMA_VERSION | typeof AGENTTRACE_ADAPTER_FORMAT

interface AgentTraceLlmStep {
  readonly id: string
  readonly stepNumber: number
  readonly inputTokens: number | null
  readonly outputTokens: number | null
  readonly durationMs: number | null
  readonly sourceIndex: number
}

interface AgentTraceSpan {
  readonly id: string
  readonly parentId: string | null
  readonly toolName: string
  readonly startNs: number
  readonly endNs: number
  readonly durationMs: number | null
  readonly exitCode: number | null
  readonly sourceIndex: number
}

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
  if (typeof value !== 'string' || value.length === 0) {
    errors.push(error('INVALID_STRING', path, 'Expected a non-empty string or null.'))
    return null
  }
  return value
}

function nullableNonNegativeNumber(
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

function nullableTokenCount(
  record: Record<string, unknown>,
  key: string,
  path: string,
  errors: ValidationIssue[],
): number | null {
  const value = record[key]
  if (value === undefined || value === null) return null
  if (typeof value !== 'number' || !Number.isSafeInteger(value) || value < 0) {
    errors.push(error('INVALID_TOKEN_COUNT', path, 'Expected a non-negative safe integer or null.'))
    return null
  }
  return value
}

function requiredPositiveSafeInteger(value: unknown, path: string, errors: ValidationIssue[]): number | null {
  if (typeof value !== 'number' || !Number.isSafeInteger(value) || value <= 0) {
    errors.push(error('INVALID_POSITIVE_INTEGER', path, 'Expected a positive safe integer.'))
    return null
  }
  return value
}

function requiredNonNegativeSafeInteger(value: unknown, path: string, errors: ValidationIssue[]): number | null {
  if (typeof value !== 'number' || !Number.isSafeInteger(value) || value < 0) {
    errors.push(error('INVALID_SAFE_INTEGER', path, 'Expected a non-negative safe integer.'))
    return null
  }
  return value
}

function nullableExitCode(value: unknown, path: string, errors: ValidationIssue[]): number | null {
  if (value === undefined || value === null) return null
  if (typeof value !== 'number' || !Number.isSafeInteger(value)) {
    errors.push(error('INVALID_EXIT_CODE', path, 'Expected a safe integer or null.'))
    return null
  }
  return value
}

function hasMultipleTopLevelValues(input: string): boolean {
  let depth = 0
  let inString = false
  let escaped = false
  let started = false

  for (let index = 0; index < input.length; index += 1) {
    const character = input[index]
    if (!started) {
      if (/\s/.test(character)) continue
      if (character !== '{' && character !== '[') return false
      started = true
      depth = 1
      continue
    }
    if (inString) {
      if (escaped) escaped = false
      else if (character === '\\') escaped = true
      else if (character === '"') inString = false
      continue
    }
    if (character === '"') {
      inString = true
      continue
    }
    if (character === '{' || character === '[') depth += 1
    else if (character === '}' || character === ']') depth -= 1
    if (depth === 0) {
      const trailing = input.slice(index + 1).trim()
      return trailing.startsWith('{') || trailing.startsWith('[')
    }
  }
  return false
}

function parseLlmStep(value: unknown, index: number, errors: ValidationIssue[]): AgentTraceLlmStep | null {
  const path = `$.llm_steps[${index}]`
  if (!isRecord(value)) {
    errors.push(error('INVALID_LLM_STEP', path, 'Expected an LLMStep object.'))
    return null
  }

  const id = requiredString(value, 'step_id', `${path}.step_id`, errors)
  const stepNumber = requiredPositiveSafeInteger(value.step_number, `${path}.step_number`, errors)
  const inputTokens = nullableTokenCount(value, 'input_tokens', `${path}.input_tokens`, errors)
  const outputTokens = nullableTokenCount(value, 'output_tokens', `${path}.output_tokens`, errors)
  const durationMs = nullableNonNegativeNumber(value, 'duration_ms', `${path}.duration_ms`, errors)
  if (id === null || stepNumber === null) return null
  return { id, stepNumber, inputTokens, outputTokens, durationMs, sourceIndex: index }
}

function parseSpan(
  value: unknown,
  index: number,
  errors: ValidationIssue[],
  telemetry: { present: boolean },
): AgentTraceSpan | null {
  const path = `$.spans[${index}]`
  if (!isRecord(value)) {
    errors.push(error('INVALID_SPAN', path, 'Expected a span object.'))
    return null
  }
  if (value.type !== 'TOOL') {
    errors.push(error('UNSUPPORTED_SPAN_TYPE', `${path}.type`, 'Only TOOL spans are supported.'))
  }

  const id = requiredString(value, 'span_id', `${path}.span_id`, errors)
  const parentId = nullableString(value, 'parent_span_id', `${path}.parent_span_id`, errors)
  const toolName = requiredString(value, 'tool_name', `${path}.tool_name`, errors)
  const startNs = requiredNonNegativeSafeInteger(value.start_ns, `${path}.start_ns`, errors)
  const endNs = requiredNonNegativeSafeInteger(value.end_ns, `${path}.end_ns`, errors)
  const durationMs = nullableNonNegativeNumber(value, 'duration_ms', `${path}.duration_ms`, errors)
  const exitCode = nullableExitCode(value.exit_code, `${path}.exit_code`, errors)

  if (Object.prototype.hasOwnProperty.call(value, 'telemetry')) {
    if (!isRecord(value.telemetry)) {
      errors.push(error('INVALID_TELEMETRY', `${path}.telemetry`, 'Expected a telemetry object when present.'))
    } else {
      telemetry.present = true
    }
  }
  if (startNs !== null && endNs !== null && endNs < startNs) {
    errors.push(error('INVALID_MONOTONIC_INTERVAL', `${path}.end_ns`, 'Span end must not precede span start.'))
  }

  if (value.type !== 'TOOL' || id === null || toolName === null || startNs === null || endNs === null) return null
  return { id, parentId, toolName, startNs, endNs, durationMs, exitCode, sourceIndex: index }
}

function validateExternalIdentity(
  steps: readonly AgentTraceLlmStep[],
  spans: readonly AgentTraceSpan[],
  errors: ValidationIssue[],
): void {
  const ids = new Map<string, string>()
  const stepNumbers = new Map<number, number>()

  for (const step of steps) {
    const path = `$.llm_steps[${step.sourceIndex}]`
    const previousIdPath = ids.get(step.id)
    if (previousIdPath) errors.push(error('DUPLICATE_EXTERNAL_ID', `${path}.step_id`, `ID duplicates ${previousIdPath}.`))
    else ids.set(step.id, `${path}.step_id`)

    const previousStepIndex = stepNumbers.get(step.stepNumber)
    if (previousStepIndex !== undefined) {
      errors.push(error('DUPLICATE_STEP_NUMBER', `${path}.step_number`, `Step number duplicates $.llm_steps[${previousStepIndex}].step_number.`))
    } else {
      stepNumbers.set(step.stepNumber, step.sourceIndex)
    }
  }

  const spanIds = new Set(spans.map((span) => span.id))
  const spansById = new Map(spans.map((span) => [span.id, span] as const))
  for (const span of spans) {
    const path = `$.spans[${span.sourceIndex}]`
    const previousIdPath = ids.get(span.id)
    if (previousIdPath) errors.push(error('DUPLICATE_EXTERNAL_ID', `${path}.span_id`, `ID duplicates ${previousIdPath}.`))
    else ids.set(span.id, `${path}.span_id`)
    if (span.parentId !== null && !spanIds.has(span.parentId)) {
      errors.push(error('UNKNOWN_SPAN_PARENT', `${path}.parent_span_id`, 'Parent must reference another span in this trace.'))
    }
  }

  const states = new Map<string, 'visiting' | 'complete'>()
  for (const startSpan of spans) {
    if (states.has(startSpan.id)) continue
    const path: AgentTraceSpan[] = []
    let current: AgentTraceSpan | undefined = startSpan
    while (current) {
      const state = states.get(current.id)
      if (state === 'complete') break
      if (state === 'visiting') {
        errors.push(error(
          'CYCLIC_SPAN_HIERARCHY',
          `$.spans[${current.sourceIndex}].parent_span_id`,
          'Span hierarchy contains a cycle.',
        ))
        break
      }
      states.set(current.id, 'visiting')
      path.push(current)
      current = current.parentId === null ? undefined : spansById.get(current.parentId)
    }
    for (const span of path) states.set(span.id, 'complete')
  }
}

function spanStatus(span: AgentTraceSpan): ObservationEventStatus {
  if (span.toolName !== 'bash' || span.exitCode === null) return 'unknown'
  return span.exitCode === 0 ? 'success' : 'error'
}

export function parseAgentTrace(input: string): ParseResult {
  const inputBytes = new TextEncoder().encode(input).byteLength
  if (inputBytes > MAX_OBSERVATION_BYTES) {
    return { ok: false, errors: [error('INPUT_TOO_LARGE', '$', `Input exceeds the ${MAX_OBSERVATION_BYTES}-byte limit.`)] }
  }

  let parsed: unknown
  try {
    parsed = JSON.parse(input) as unknown
  } catch {
    const code = hasMultipleTopLevelValues(input) ? 'MULTIPLE_TRACES_NOT_SUPPORTED' : 'INVALID_JSON'
    const message = code === 'MULTIPLE_TRACES_NOT_SUPPORTED'
      ? 'Expected exactly one AgentTrace object per file.'
      : 'Input is not valid JSON.'
    return { ok: false, errors: [error(code, '$', message)] }
  }
  if (!isRecord(parsed)) {
    return { ok: false, errors: [error('INVALID_AGENTTRACE_ROOT', '$', 'Expected an AgentTrace object.')] }
  }
  if (Object.prototype.hasOwnProperty.call(parsed, 'schema_version')) {
    return { ok: false, errors: [error('INVALID_AGENTTRACE_SIGNATURE', '$.schema_version', 'LCP Evidence must use the LCP parser.')] }
  }
  if (!Array.isArray(parsed.spans) || !Array.isArray(parsed.llm_steps)) {
    return { ok: false, errors: [error('INVALID_AGENTTRACE_SIGNATURE', '$', 'Expected spans and llm_steps arrays.')] }
  }
  if (parsed.spans.length + parsed.llm_steps.length > MAX_OBSERVATION_EVENTS) {
    return { ok: false, errors: [error('TOO_MANY_EVENTS', '$', `Combined event count exceeds ${MAX_OBSERVATION_EVENTS}.`)] }
  }

  const errors: ValidationIssue[] = []
  const traceId = requiredString(parsed, 'trace_id', '$.trace_id', errors)
  const model = nullableString(parsed, 'model', '$.model', errors)
  const totalDurationMs = nullableNonNegativeNumber(parsed, 'total_duration_ms', '$.total_duration_ms', errors)
  const datasetName = nullableString(parsed, 'dataset_name', '$.dataset_name', errors)
  const telemetry = { present: false }
  const steps = parsed.llm_steps
    .map((step, index) => parseLlmStep(step, index, errors))
    .filter((step): step is AgentTraceLlmStep => step !== null)
  const spans = parsed.spans
    .map((span, index) => parseSpan(span, index, errors, telemetry))
    .filter((span): span is AgentTraceSpan => span !== null)

  const sanitizationClaim = parsed._sample_sanitized
  if (sanitizationClaim !== undefined && typeof sanitizationClaim !== 'boolean') {
    errors.push(error('INVALID_SANITIZATION_CLAIM', '$._sample_sanitized', 'Expected a boolean when present.'))
  }
  validateExternalIdentity(steps, spans, errors)
  if (errors.length > 0 || traceId === null) return { ok: false, errors }

  const sortedSteps = [...steps].sort((left, right) => left.stepNumber - right.stepNumber)
  const sortedSpans = [...spans].sort((left, right) => {
    if (left.startNs !== right.startNs) return left.startNs - right.startNs
    return left.id < right.id ? -1 : left.id > right.id ? 1 : 0
  })
  const rawEvents: Record<string, unknown>[] = []

  for (const step of sortedSteps) {
    rawEvents.push({
      id: step.id,
      parent_id: null,
      seq: rawEvents.length + 1,
      kind: 'model',
      name: 'llm_step',
      started_at: null,
      ended_at: null,
      status: 'unknown',
      position: { basis: 'ordinal', lane: 'llm_step', ordinal: step.stepNumber },
      usage: {
        input_tokens: step.inputTokens,
        output_tokens: step.outputTokens,
        duration_ms: step.durationMs,
        cost_usd: null,
      },
      detail: null,
    })
  }
  for (const span of sortedSpans) {
    rawEvents.push({
      id: span.id,
      parent_id: span.parentId,
      seq: rawEvents.length + 1,
      kind: span.toolName === 'final_answer' ? 'message' : 'tool',
      name: span.toolName,
      started_at: null,
      ended_at: null,
      status: span.toolName === 'final_answer' ? 'unknown' : spanStatus(span),
      position: { basis: 'monotonic_ns', lane: 'span', start_ns: span.startNs, end_ns: span.endNs },
      usage: {
        input_tokens: null,
        output_tokens: null,
        duration_ms: span.durationMs,
        cost_usd: null,
      },
      detail: null,
    })
  }

  const normalized = parseLcpObservation(JSON.stringify({
    schema_version: LCP_OBSERVATION_SCHEMA_VERSION,
    run_id: traceId,
    source: {
      kind: 'trace',
      format: AGENTTRACE_ADAPTER_FORMAT,
      producer: 'pagarsky/agent-trace',
      reference: datasetName,
    },
    agent: { name: null, model },
    started_at: null,
    ended_at: null,
    total_duration_ms: totalDurationMs,
    events: rawEvents,
  }))
  if (!normalized.ok) return normalized

  const adapterWarnings: ValidationIssue[] = [
    warning('PARTIAL_ORDER_ONLY', '$', 'LLMSteps and spans do not share a global chronology.'),
    warning('SOURCE_NOT_AUTHENTICATED', '$', 'AgentTrace provenance is reported and not authenticated.'),
  ]
  if (telemetry.present) {
    adapterWarnings.push(warning('TELEMETRY_IGNORED', '$.spans', 'Telemetry was validated as an object and discarded.'))
  }
  adapterWarnings.push(sanitizationClaim === true
    ? warning('SANITIZATION_SELF_DECLARED', '$._sample_sanitized', 'Sanitization is self-declared and not independently verified.')
    : warning('SANITIZATION_UNCONFIRMED', '$._sample_sanitized', 'Sanitization is absent or not confirmed.'))

  const warnings = [...normalized.warnings, ...adapterWarnings]
  return { ok: true, value: { ...normalized.value, warnings }, warnings }
}

export function parseObservationInput(input: string, format: ObservationInputFormat): ParseResult {
  if (format === LCP_OBSERVATION_SCHEMA_VERSION) return parseLcpObservation(input)
  if (format === AGENTTRACE_ADAPTER_FORMAT) return parseAgentTrace(input)
  return { ok: false, errors: [error('UNSUPPORTED_INPUT_FORMAT', '$', 'Input format is not supported.')] }
}
