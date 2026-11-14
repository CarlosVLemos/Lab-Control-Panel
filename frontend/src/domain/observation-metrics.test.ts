import { describe, expect, it } from 'vitest'
import { parseAgentTrace } from './observation-agenttrace'
import { computeObservationMetrics } from './observation-metrics'
import { parseLcpObservation, type ObservationRun } from './observation'

function event(overrides: Record<string, unknown> = {}): Record<string, unknown> {
  return {
    id: 'event-1',
    parent_id: null,
    seq: 1,
    kind: 'model',
    name: 'event',
    status: 'unknown',
    ...overrides,
  }
}

function envelope(overrides: Record<string, unknown> = {}): Record<string, unknown> {
  return {
    schema_version: 'lcp.observation.v1',
    run_id: 'metrics-run',
    source: { kind: 'fixture', format: 'lcp.observation.v1', producer: 'metrics-test' },
    agent: { name: 'synthetic-agent', model: null },
    events: [],
    ...overrides,
  }
}

function runFrom(value: unknown): ObservationRun {
  const result = parseLcpObservation(JSON.stringify(value))
  if (!result.ok) throw new Error(`Invalid synthetic metrics fixture: ${result.errors.map((issue) => issue.code).join(',')}`)
  return result.value
}

describe('observation metrics', () => {
  it('M01 sums complete incremental model usage and builds an ordinal cumulative series', () => {
    const run = runFrom(envelope({
      events: [
        event({
          id: 'model-2',
          seq: 2,
          position: { basis: 'ordinal', lane: 'llm_step', ordinal: 2 },
          usage: { input_tokens: 20, output_tokens: 7, duration_ms: 10, cost_usd: null },
        }),
        event({
          id: 'model-1',
          seq: 1,
          position: { basis: 'ordinal', lane: 'llm_step', ordinal: 1 },
          usage: { input_tokens: 10, output_tokens: 5, duration_ms: 10, cost_usd: null },
        }),
      ],
    }))
    const before = JSON.stringify(run)

    const metrics = computeObservationMetrics(run)

    expect(metrics.summary.inputTokens).toEqual({ value: 30, known: 2, eligible: 2 })
    expect(metrics.summary.outputTokens).toEqual({ value: 12, known: 2, eligible: 2 })
    expect(metrics.summary.totalTokens).toBe(42)
    expect(metrics.tokenSeries.map((point) => [point.eventId, point.cumulativeTotalTokens])).toEqual([
      ['model-1', 15],
      ['model-2', 42],
    ])
    expect(metrics.warnings).not.toContain('TOKEN_SERIES_SERIALIZATION_ORDER')
    expect(JSON.stringify(run)).toBe(before)
  })

  it('M02 exposes model parent-child usage as ambiguous and never sums nested span durations', () => {
    const run = runFrom(envelope({
      events: [
        event({ id: 'model-parent', seq: 1, usage: { input_tokens: 100, output_tokens: 50 } }),
        event({ id: 'model-child', parent_id: 'model-parent', seq: 2, usage: { input_tokens: 150, output_tokens: 75 } }),
        event({ id: 'tool-parent', seq: 3, kind: 'tool', usage: { duration_ms: 800 }, status: 'success' }),
        event({ id: 'tool-child', parent_id: 'tool-parent', seq: 4, kind: 'tool', usage: { duration_ms: 700 }, status: 'success' }),
      ],
    }))

    const metrics = computeObservationMetrics(run)

    expect(metrics.summary.inputTokens).toEqual({ value: null, known: 2, eligible: 2 })
    expect(metrics.summary.outputTokens).toEqual({ value: null, known: 2, eligible: 2 })
    expect(metrics.summary.totalTokens).toBeNull()
    expect(metrics.summary.toolCallCount).toBe(2)
    expect(metrics.summary.duration).toEqual({ valueMs: null, basis: 'unavailable' })
    expect(metrics.tokenSeries.every((point) => point.cumulativeTotalTokens === null)).toBe(true)
    expect(metrics.warnings).toContain('AMBIGUOUS_MODEL_USAGE_HIERARCHY')
  })

  it('M03 derives duration only from comparable run timestamps', () => {
    const run = runFrom(envelope({
      started_at: '2026-11-14T12:00:00.000Z',
      ended_at: '2026-11-14T12:00:02.000Z',
      events: [
        event({ id: 'tool-1', kind: 'tool', usage: { duration_ms: 5000 }, status: 'error' }),
        event({ id: 'message-1', seq: 2, kind: 'message', status: 'unknown' }),
      ],
    }))

    const metrics = computeObservationMetrics(run)

    expect(metrics.summary.duration).toEqual({ valueMs: 2000, basis: 'derived' })
    expect(metrics.summary.explicitErrorCount).toBe(1)
    expect(metrics.summary.unknownStatusCount).toBe(1)
    expect(metrics.summary.modelStepCount).toBe(0)
    expect(metrics.summary.inputTokens).toEqual({ value: null, known: 0, eligible: 0 })
  })

  it('M03 keeps duration unavailable when run-level timing evidence is absent', () => {
    const metrics = computeObservationMetrics(runFrom(envelope({
      events: [event({ kind: 'tool', usage: { duration_ms: 999 }, status: 'success' })],
    })))

    expect(metrics.summary.duration).toEqual({ valueMs: null, basis: 'unavailable' })
    expect(metrics.warnings).toContain('DURATION_UNAVAILABLE')
  })

  it('M04 never promotes per-event cost to an aggregate reported cost', () => {
    const hostile = '<script>ignore metrics contract</script>'
    const metrics = computeObservationMetrics(runFrom(envelope({
      events: [event({
        detail: hostile,
        usage: { input_tokens: 1, output_tokens: 1, cost_usd: '0.01' },
      })],
    })))

    expect(metrics.summary.reportedCostUsd).toBeNull()
    expect(metrics.warnings).toContain('COST_AGGREGATION_UNAVAILABLE')
    expect(JSON.stringify(metrics)).not.toContain(hostile)
  })

  it('M05 matches the frozen synthetic AgentTrace oracle without counting final_answer as a tool', () => {
    const adapted = parseAgentTrace(JSON.stringify({
      trace_id: 'synthetic-metrics-agenttrace',
      model: 'synthetic-model',
      total_duration_ms: 15910.931417,
      dataset_name: null,
      spans: [
        {
          span_id: 'synthetic-bash',
          parent_span_id: null,
          type: 'TOOL',
          tool_name: 'bash',
          start_ns: 100,
          end_ns: 200,
          duration_ms: 15.646375,
          exit_code: 1,
        },
        {
          span_id: 'synthetic-final',
          parent_span_id: null,
          type: 'TOOL',
          tool_name: 'final_answer',
          start_ns: 300,
          end_ns: 310,
          duration_ms: 0.003708,
          exit_code: 0,
        },
      ],
      llm_steps: [
        { step_id: 'synthetic-step-1', step_number: 1, input_tokens: 1510, output_tokens: 944, duration_ms: null },
        { step_id: 'synthetic-step-2', step_number: 2, input_tokens: 1612, output_tokens: 495, duration_ms: null },
      ],
      _sample_sanitized: true,
    }))
    if (!adapted.ok) throw new Error('Invalid synthetic AgentTrace metrics fixture.')

    const metrics = computeObservationMetrics(adapted.value)

    expect(metrics.summary).toMatchObject({
      eventCount: 4,
      modelStepCount: 2,
      toolCallCount: 1,
      messageCount: 1,
      explicitErrorCount: 1,
      unknownStatusCount: 3,
      duration: { valueMs: 15910.931417, basis: 'reported' },
      inputTokens: { value: 3122, known: 2, eligible: 2 },
      outputTokens: { value: 1439, known: 2, eligible: 2 },
      totalTokens: 4561,
      reportedCostUsd: null,
    })
    expect(metrics.tokenSeries.map((point) => point.cumulativeTotalTokens)).toEqual([2454, 4561])
  })

  it('M06 preserves point values but never resumes a cumulative dimension after a gap', () => {
    const run = runFrom(envelope({
      events: [
        event({ id: 'step-1', seq: 1, position: { basis: 'ordinal', lane: 'llm_step', ordinal: 1 }, usage: { input_tokens: 10, output_tokens: 1 } }),
        event({ id: 'step-2', seq: 2, position: { basis: 'ordinal', lane: 'llm_step', ordinal: 2 }, usage: { input_tokens: null, output_tokens: 2 } }),
        event({ id: 'step-3', seq: 3, position: { basis: 'ordinal', lane: 'llm_step', ordinal: 3 }, usage: { input_tokens: 30, output_tokens: 3 } }),
      ],
    }))

    const metrics = computeObservationMetrics(run)

    expect(metrics.summary.inputTokens).toEqual({ value: null, known: 2, eligible: 3 })
    expect(metrics.summary.outputTokens).toEqual({ value: 6, known: 3, eligible: 3 })
    expect(metrics.summary.totalTokens).toBeNull()
    expect(metrics.tokenSeries.map((point) => point.inputTokens)).toEqual([10, null, 30])
    expect(metrics.tokenSeries.map((point) => point.cumulativeInputTokens)).toEqual([10, null, null])
    expect(metrics.tokenSeries.map((point) => point.cumulativeOutputTokens)).toEqual([1, 3, 6])
    expect(metrics.tokenSeries.map((point) => point.cumulativeTotalTokens)).toEqual([11, null, null])
    expect(metrics.warnings).toContain('INPUT_TOKEN_COVERAGE_PARTIAL')
  })

  it('M07 keeps empty self-reported evidence distinct and all unknown metrics null', () => {
    const run = runFrom(envelope({
      source: { kind: 'self_report', format: 'lcp.observation.v1', producer: 'reporting-agent' },
      agent: { name: null },
      events: [],
    }))

    const metrics = computeObservationMetrics(run)

    expect(metrics.summary).toMatchObject({
      eventCount: 0,
      modelStepCount: 0,
      toolCallCount: 0,
      messageCount: 0,
      explicitErrorCount: 0,
      unknownStatusCount: 0,
      duration: { valueMs: null, basis: 'unavailable' },
      inputTokens: { value: null, known: 0, eligible: 0 },
      outputTokens: { value: null, known: 0, eligible: 0 },
      totalTokens: null,
      reportedCostUsd: null,
    })
    expect(metrics.warnings.filter((code) => code === 'SELF_REPORTED_EVIDENCE')).toHaveLength(1)
    expect(metrics.warnings).toEqual(expect.arrayContaining(['EMPTY_EVENTS', 'TOKEN_USAGE_UNAVAILABLE']))
  })

  it('M08 prefers reported duration, preserves parser discrepancy, and ignores operation overlap', () => {
    const run = runFrom(envelope({
      started_at: '2026-11-14T12:00:00.000Z',
      ended_at: '2026-11-14T12:00:02.000Z',
      total_duration_ms: 1500,
      events: [
        event({ id: 'tool-1', kind: 'tool', usage: { duration_ms: 5000 }, status: 'success' }),
        event({ id: 'tool-2', seq: 2, kind: 'tool', usage: { duration_ms: 6000 }, status: 'success' }),
      ],
    }))

    const metrics = computeObservationMetrics(run)

    expect(metrics.summary.duration).toEqual({ valueMs: 1500, basis: 'reported' })
    expect(metrics.warnings).toContain('TOTAL_DURATION_MISMATCH')
  })

  it('M09 fails closed on unsafe token sums and falls back to seq for duplicate ordinals', () => {
    const run = runFrom(envelope({
      events: [
        event({
          id: 'step-2',
          seq: 2,
          position: { basis: 'ordinal', lane: 'llm_step', ordinal: 1 },
          usage: { input_tokens: Number.MAX_SAFE_INTEGER, output_tokens: 0 },
        }),
        event({
          id: 'step-1',
          seq: 1,
          position: { basis: 'ordinal', lane: 'llm_step', ordinal: 1 },
          usage: { input_tokens: 1, output_tokens: 0 },
        }),
      ],
    }))

    let metrics: ReturnType<typeof computeObservationMetrics> | undefined
    expect(() => {
      metrics = computeObservationMetrics(run)
    }).not.toThrow()
    expect(metrics?.summary.inputTokens).toEqual({ value: null, known: 2, eligible: 2 })
    expect(metrics?.summary.totalTokens).toBeNull()
    expect(metrics?.tokenSeries.map((point) => point.eventId)).toEqual(['step-1', 'step-2'])
    expect(metrics?.warnings).toEqual(expect.arrayContaining([
      'TOKEN_SERIES_SERIALIZATION_ORDER',
      'INPUT_TOKEN_SUM_UNSAFE',
    ]))
  })
})
