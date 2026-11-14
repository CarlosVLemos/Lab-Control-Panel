import { describe, expect, it } from 'vitest'
import { syntheticAgentTraceFixture } from './__fixtures__/agenttrace'
import {
  AGENTTRACE_ADAPTER_FORMAT,
  parseAgentTrace,
  parseObservationInput,
} from './observation-agenttrace'
import {
  LCP_OBSERVATION_SCHEMA_VERSION,
  MAX_OBSERVATION_BYTES,
  MAX_OBSERVATION_EVENTS,
  type ParseResult,
} from './observation'

function parse(value: unknown): ParseResult {
  return parseAgentTrace(JSON.stringify(value))
}

function errorCodes(result: ParseResult): string[] {
  return result.ok ? [] : result.errors.map((issue) => issue.code)
}

function warningCodes(result: ParseResult): string[] {
  return result.ok ? result.warnings.map((issue) => issue.code) : []
}

function minimalStep(overrides: Record<string, unknown> = {}): Record<string, unknown> {
  return {
    step_id: 'step-1',
    step_number: 1,
    input_tokens: null,
    output_tokens: null,
    duration_ms: null,
    ...overrides,
  }
}

function minimalSpan(overrides: Record<string, unknown> = {}): Record<string, unknown> {
  return {
    span_id: 'span-1',
    parent_span_id: null,
    type: 'TOOL',
    tool_name: 'unknown-tool',
    start_ns: 10,
    end_ns: 20,
    duration_ms: 0.00001,
    exit_code: null,
    ...overrides,
  }
}

function minimalTrace(overrides: Record<string, unknown> = {}): Record<string, unknown> {
  return {
    trace_id: 'trace-1',
    model: null,
    total_duration_ms: null,
    dataset_name: null,
    spans: [],
    llm_steps: [],
    ...overrides,
  }
}

describe('AgentTrace adapter', () => {
  it('E01 and E11 map the synthetic 2+2 profile in deterministic lane order', () => {
    const result = parse(syntheticAgentTraceFixture)

    expect(result.ok).toBe(true)
    if (!result.ok) return
    expect(result.value).toMatchObject({
      runId: 'synthetic-agenttrace-run',
      source: {
        kind: 'trace',
        format: AGENTTRACE_ADAPTER_FORMAT,
        producer: 'pagarsky/agent-trace',
        reference: null,
      },
      agent: { name: null, model: 'synthetic-model' },
      startedAt: null,
      endedAt: null,
      totalDurationMs: 500,
    })
    expect(result.value.events.map((event) => [event.seq, event.id, event.kind, event.status])).toEqual([
      [1, 'synthetic-step-1', 'model', 'unknown'],
      [2, 'synthetic-step-2', 'model', 'unknown'],
      [3, 'synthetic-bash', 'tool', 'error'],
      [4, 'synthetic-final', 'message', 'unknown'],
    ])
    expect(result.value.events[0].usage).toEqual({
      inputTokens: 10,
      outputTokens: 4,
      durationMs: 12.5,
      costUsd: null,
    })
    expect(warningCodes(result)).toEqual(expect.arrayContaining([
      'PARTIAL_ORDER_ONLY',
      'SOURCE_NOT_AUTHENTICATED',
      'TELEMETRY_IGNORED',
      'SANITIZATION_SELF_DECLARED',
    ]))
  })

  it('E02 keeps unavailable model, usage, duration, timestamps, and cost as null', () => {
    const result = parse(minimalTrace({ llm_steps: [minimalStep()] }))

    expect(result.ok).toBe(true)
    if (!result.ok) return
    expect(result.value.agent).toEqual({ name: null, model: null })
    expect(result.value.totalDurationMs).toBeNull()
    expect(result.value.events[0]).toMatchObject({
      startedAt: null,
      endedAt: null,
      usage: { inputTokens: null, outputTokens: null, durationMs: null, costUsd: null },
      detail: null,
    })
  })

  it('E01 maps dataset provenance and only applies exit status semantics to bash', () => {
    const result = parse(minimalTrace({
      dataset_name: 'synthetic-dataset',
      spans: [
        minimalSpan({ span_id: 'bash-success', tool_name: 'bash', exit_code: 0 }),
        minimalSpan({ span_id: 'bash-unknown', tool_name: 'bash', exit_code: null, start_ns: 30, end_ns: 40 }),
        minimalSpan({ span_id: 'other-tool', tool_name: 'other', exit_code: 1, start_ns: 50, end_ns: 60 }),
      ],
    }))

    expect(result.ok).toBe(true)
    if (!result.ok) return
    expect(result.value.source.reference).toBe('synthetic-dataset')
    expect(result.value.events.map((event) => [event.id, event.status])).toEqual([
      ['bash-success', 'success'],
      ['bash-unknown', 'unknown'],
      ['other-tool', 'unknown'],
    ])
  })

  it('E01 uses span_id as the deterministic tie-breaker for equal monotonic starts', () => {
    const result = parse(minimalTrace({
      spans: [
        minimalSpan({ span_id: 'span-b', start_ns: 10, end_ns: 30 }),
        minimalSpan({ span_id: 'span-a', start_ns: 10, end_ns: 20 }),
      ],
    }))

    expect(result.ok).toBe(true)
    if (!result.ok) return
    expect(result.value.events.map((event) => event.id)).toEqual(['span-a', 'span-b'])
  })

  it('E03 rejects unsupported signatures, span types, and combined event limits', () => {
    const signature = parse({ trace_id: 'trace-1' })
    const spanType = parse(minimalTrace({ spans: [minimalSpan({ type: 'MODEL' })] }))
    const tooMany = parse(minimalTrace({
      llm_steps: Array.from({ length: MAX_OBSERVATION_EVENTS + 1 }, (_, index) => minimalStep({
        step_id: `step-${index + 1}`,
        step_number: index + 1,
      })),
    }))
    const oversized = parseAgentTrace(JSON.stringify({ padding: 'x'.repeat(MAX_OBSERVATION_BYTES) }))

    expect(errorCodes(signature)).toContain('INVALID_AGENTTRACE_SIGNATURE')
    expect(errorCodes(spanType)).toContain('UNSUPPORTED_SPAN_TYPE')
    expect(errorCodes(tooMany)).toContain('TOO_MANY_EVENTS')
    expect(errorCodes(oversized)).toContain('INPUT_TOO_LARGE')
  })

  it('E04 and E05 preserve ordinal and monotonic positions in separate lanes', () => {
    const result = parse(syntheticAgentTraceFixture)

    expect(result.ok).toBe(true)
    if (!result.ok) return
    expect(result.value.events[0].position).toEqual({ basis: 'ordinal', lane: 'llm_step', ordinal: 1 })
    expect(result.value.events[2].position).toEqual({ basis: 'monotonic_ns', lane: 'span', startNs: 100, endNs: 200 })
    expect(result.value.events.every((event) => event.startedAt === null && event.endedAt === null)).toBe(true)
  })

  it('E06 does not turn proposed tool_calls into executed tool events', () => {
    const result = parse(minimalTrace({
      llm_steps: [minimalStep({ tool_calls: [{ name: 'proposed-only' }] })],
    }))

    expect(result.ok).toBe(true)
    if (!result.ok) return
    expect(result.value.events).toHaveLength(1)
    expect(result.value.events[0].kind).toBe('model')
  })

  it('E07 discards reasoning, tool input, tool output, and arbitrary fields', () => {
    const secret = 'synthetic-secret-marker'
    const result = parse(minimalTrace({
      reasoning_content: secret,
      llm_steps: [minimalStep({ reasoning_content: secret, prompt: secret })],
      spans: [minimalSpan({ tool_input: secret, tool_output: secret, arbitrary: secret })],
    }))

    expect(result.ok).toBe(true)
    expect(JSON.stringify(result)).not.toContain(secret)
  })

  it('E08 rejects multiple JSON values instead of selecting the first trace', () => {
    const line = JSON.stringify(minimalTrace())
    const result = parseAgentTrace(`${line}\n${line}`)

    expect(errorCodes(result)).toEqual(['MULTIPLE_TRACES_NOT_SUPPORTED'])
  })

  it('E10 rejects unsafe or reversed monotonic counters without coercion', () => {
    const unsafe = parse(minimalTrace({ spans: [minimalSpan({ end_ns: Number.MAX_SAFE_INTEGER + 1 })] }))
    const reversed = parse(minimalTrace({ spans: [minimalSpan({ start_ns: 20, end_ns: 10 })] }))

    expect(errorCodes(unsafe)).toContain('INVALID_SAFE_INTEGER')
    expect(errorCodes(reversed)).toContain('INVALID_MONOTONIC_INTERVAL')
  })

  it('E03 rejects invalid token, duration, exit code, and sanitization numbers', () => {
    const result = parse(minimalTrace({
      llm_steps: [minimalStep({ input_tokens: -1, duration_ms: -1 })],
      spans: [minimalSpan({ exit_code: 1.5 })],
      _sample_sanitized: 'yes',
    }))

    expect(errorCodes(result)).toEqual(expect.arrayContaining([
      'INVALID_TOKEN_COUNT',
      'INVALID_NON_NEGATIVE_NUMBER',
      'INVALID_EXIT_CODE',
      'INVALID_SANITIZATION_CLAIM',
    ]))
  })

  it('E12 validates then discards telemetry and treats sanitization only as a claim', () => {
    const declared = parse(minimalTrace({ spans: [minimalSpan({ telemetry: { max_rss_bytes: 123 } })], _sample_sanitized: true }))
    const denied = parse(minimalTrace({ _sample_sanitized: false }))
    const absent = parse(minimalTrace())
    const invalidTelemetry = parse(minimalTrace({ spans: [minimalSpan({ telemetry: null })] }))

    expect(warningCodes(declared)).toEqual(expect.arrayContaining(['TELEMETRY_IGNORED', 'SANITIZATION_SELF_DECLARED']))
    expect(warningCodes(denied)).toContain('SANITIZATION_UNCONFIRMED')
    expect(warningCodes(absent)).toContain('SANITIZATION_UNCONFIRMED')
    expect(errorCodes(invalidTelemetry)).toContain('INVALID_TELEMETRY')
    expect(JSON.stringify(declared)).not.toContain('max_rss_bytes')
  })

  it('E13 reports duplicate steps, duplicate cross-lane ids, and invalid parents at source paths', () => {
    const result = parse(minimalTrace({
      llm_steps: [
        minimalStep({ step_id: 'duplicate', step_number: 1 }),
        minimalStep({ step_id: 'step-2', step_number: 1 }),
      ],
      spans: [minimalSpan({ span_id: 'duplicate', parent_span_id: 'missing' })],
    }))

    expect(result.ok).toBe(false)
    if (result.ok) return
    expect(result.errors).toEqual(expect.arrayContaining([
      expect.objectContaining({ code: 'DUPLICATE_STEP_NUMBER', path: '$.llm_steps[1].step_number' }),
      expect.objectContaining({ code: 'DUPLICATE_EXTERNAL_ID', path: '$.spans[0].span_id' }),
      expect.objectContaining({ code: 'UNKNOWN_SPAN_PARENT', path: '$.spans[0].parent_span_id' }),
    ]))
  })

  it('E13 rejects cyclic span parents at the original AgentTrace path', () => {
    const result = parse(minimalTrace({
      spans: [
        minimalSpan({ span_id: 'span-1', parent_span_id: 'span-2' }),
        minimalSpan({ span_id: 'span-2', parent_span_id: 'span-1', start_ns: 30, end_ns: 40 }),
      ],
    }))

    expect(result.ok).toBe(false)
    if (result.ok) return
    expect(result.errors).toEqual(expect.arrayContaining([
      expect.objectContaining({ code: 'CYCLIC_SPAN_HIERARCHY', path: '$.spans[0].parent_span_id' }),
    ]))
  })

  it('routes only explicitly selected LCP and AgentTrace input formats', () => {
    const lcp = JSON.stringify({
      schema_version: LCP_OBSERVATION_SCHEMA_VERSION,
      run_id: 'lcp-run',
      source: { kind: 'trace', format: LCP_OBSERVATION_SCHEMA_VERSION, producer: 'test' },
      agent: { name: null },
      events: [],
    })

    expect(parseObservationInput(lcp, LCP_OBSERVATION_SCHEMA_VERSION).ok).toBe(true)
    expect(parseObservationInput(JSON.stringify(minimalTrace()), AGENTTRACE_ADAPTER_FORMAT).ok).toBe(true)
  })
})
