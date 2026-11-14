import { describe, expect, it } from 'vitest'
import { completeObservationFixture } from './__fixtures__/observation'
import {
  MAX_OBSERVATION_BYTES,
  MAX_OBSERVATION_EVENTS,
  parseLcpObservation,
  type ParseResult,
} from './observation'

function parse(value: unknown): ParseResult {
  return parseLcpObservation(JSON.stringify(value))
}

function minimalEvent(overrides: Record<string, unknown> = {}): Record<string, unknown> {
  return {
    id: 'evt-1',
    seq: 1,
    kind: 'message',
    name: 'message',
    status: 'unknown',
    ...overrides,
  }
}

function minimalEnvelope(overrides: Record<string, unknown> = {}): Record<string, unknown> {
  return {
    schema_version: 'lcp.observation.v1',
    run_id: 'minimal-run',
    source: { kind: 'trace', format: 'lcp.observation.v1', producer: 'contract-test' },
    agent: { name: 'contract-agent' },
    events: [minimalEvent()],
    ...overrides,
  }
}

function errorCodes(result: ParseResult): string[] {
  return result.ok ? [] : result.errors.map((issue) => issue.code)
}

function hierarchyEvents(length: number, cyclic: boolean): Record<string, unknown>[] {
  return Array.from({ length }, (_, index) => minimalEvent({
    id: `evt-${index + 1}`,
    seq: index + 1,
    parent_id: index === 0
      ? (cyclic ? `evt-${length}` : null)
      : `evt-${index}`,
  }))
}

describe('LCP Evidence v1 parser and normalizer', () => {
  it('C01 parses a complete envelope deterministically and orders events by sequence', () => {
    const result = parse({
      ...completeObservationFixture,
      events: [...completeObservationFixture.events].reverse(),
    })

    expect(result.ok).toBe(true)
    if (!result.ok) return
    expect(result.value).toMatchObject({
      schemaVersion: 'lcp.observation.v1',
      runId: 'synthetic-run-001',
      sourceKind: 'fixture',
      agent: { name: 'synthetic-agent', model: 'synthetic-model' },
      totalDurationMs: 2500,
    })
    expect(result.value.events.map((event) => event.seq)).toEqual([1, 2])
    expect(result.value.events[0].usage).toEqual({
      inputTokens: 12,
      outputTokens: 8,
      durationMs: 1500,
      costUsd: '0.0012',
    })
    expect(result.warnings).toEqual([])
  })

  it('C02 normalizes absent optional fields to null without inventing evidence', () => {
    const result = parse(minimalEnvelope())

    expect(result.ok).toBe(true)
    if (!result.ok) return
    expect(result.value).toMatchObject({
      startedAt: null,
      endedAt: null,
      totalDurationMs: null,
      source: { reference: null },
      agent: { model: null },
    })
    expect(result.value.events[0]).toMatchObject({
      parentId: null,
      startedAt: null,
      endedAt: null,
      position: null,
      usage: null,
      detail: null,
    })
  })

  it('E09 accepts a present null agent name without substituting the model', () => {
    const result = parse(minimalEnvelope({ agent: { name: null, model: 'reported-model' } }))

    expect(result.ok).toBe(true)
    if (!result.ok) return
    expect(result.value.agent).toEqual({ name: null, model: 'reported-model' })
  })

  it('E09 rejects an absent or empty agent name', () => {
    const absent = parse(minimalEnvelope({ agent: { model: 'reported-model' } }))
    const empty = parse(minimalEnvelope({ agent: { name: '' } }))

    expect(errorCodes(absent)).toContain('REQUIRED_NULLABLE_STRING')
    expect(errorCodes(empty)).toContain('REQUIRED_NULLABLE_STRING')
  })

  it('E09 normalizes ordinal and monotonic positions without inventing timestamps', () => {
    const result = parse(minimalEnvelope({
      events: [
        minimalEvent({
          id: 'model-1',
          seq: 1,
          kind: 'model',
          position: { basis: 'ordinal', lane: 'llm_step', ordinal: 2 },
        }),
        minimalEvent({
          id: 'tool-1',
          seq: 2,
          kind: 'tool',
          position: { basis: 'monotonic_ns', lane: 'span', start_ns: 120, end_ns: 190 },
        }),
      ],
    }))

    expect(result.ok).toBe(true)
    if (!result.ok) return
    expect(result.value.events[0].position).toEqual({ basis: 'ordinal', lane: 'llm_step', ordinal: 2 })
    expect(result.value.events[1].position).toEqual({ basis: 'monotonic_ns', lane: 'span', startNs: 120, endNs: 190 })
    expect(result.value.events.every((event) => event.startedAt === null && event.endedAt === null)).toBe(true)
  })

  it('E10 accepts MAX_SAFE_INTEGER and rejects unsafe or reversed monotonic positions', () => {
    const accepted = parse(minimalEnvelope({ events: [minimalEvent({
      position: {
        basis: 'monotonic_ns',
        lane: 'span',
        start_ns: Number.MAX_SAFE_INTEGER,
        end_ns: Number.MAX_SAFE_INTEGER,
      },
    })] }))
    const unsafe = parse(minimalEnvelope({ events: [minimalEvent({
      position: { basis: 'monotonic_ns', lane: 'span', start_ns: 0, end_ns: Number.MAX_SAFE_INTEGER + 1 },
    })] }))
    const reversed = parse(minimalEnvelope({ events: [minimalEvent({
      position: { basis: 'monotonic_ns', lane: 'span', start_ns: 2, end_ns: 1 },
    })] }))

    expect(accepted.ok).toBe(true)
    expect(errorCodes(unsafe)).toContain('INVALID_POSITION_END')
    expect(errorCodes(reversed)).toContain('INVALID_POSITION_INTERVAL')
  })

  it('E09 rejects invalid ordinal positions and mismatched lanes', () => {
    const ordinal = parse(minimalEnvelope({ events: [minimalEvent({
      position: { basis: 'ordinal', lane: 'llm_step', ordinal: 0 },
    })] }))
    const lane = parse(minimalEnvelope({ events: [minimalEvent({
      position: { basis: 'monotonic_ns', lane: 'llm_step', start_ns: 1, end_ns: 2 },
    })] }))

    expect(errorCodes(ordinal)).toContain('INVALID_POSITION_ORDINAL')
    expect(errorCodes(lane)).toContain('INVALID_POSITION_LANE')
  })

  it('C03 rejects malformed JSON before producing a normalized run', () => {
    const result = parseLcpObservation('{"schema_version":')

    expect(result).toEqual({
      ok: false,
      errors: [{ severity: 'error', code: 'INVALID_JSON', path: '$', message: 'Input is not valid JSON.' }],
    })
  })

  it('C03 rejects UTF-8 input larger than 5 MiB without echoing it', () => {
    const oversized = JSON.stringify({ padding: 'x'.repeat(MAX_OBSERVATION_BYTES) })
    const result = parseLcpObservation(oversized)

    expect(errorCodes(result)).toEqual(['INPUT_TOO_LARGE'])
    expect(JSON.stringify(result)).not.toContain('xxxxxxxxxxxxxxxx')
  })

  it('C03 rejects more than 10,000 events without partial normalization', () => {
    const events = Array.from({ length: MAX_OBSERVATION_EVENTS + 1 }, (_, index) => minimalEvent({
      id: `evt-${index + 1}`,
      seq: index + 1,
    }))
    const result = parse(minimalEnvelope({ events }))

    expect(errorCodes(result)).toEqual(['TOO_MANY_EVENTS'])
  })

  it('C03 rejects negative and non-finite numeric evidence', () => {
    const negative = parse(minimalEnvelope({
      total_duration_ms: -1,
      events: [minimalEvent({ usage: { input_tokens: -1, output_tokens: 0, duration_ms: -2, cost_usd: '-0.1' } })],
    }))
    const nonFinite = parseLcpObservation(JSON.stringify(minimalEnvelope()).replace(
      '"events"',
      '"total_duration_ms":1e400,"events"',
    ))

    expect(errorCodes(negative)).toEqual([
      'INVALID_NON_NEGATIVE_NUMBER',
      'INVALID_NON_NEGATIVE_NUMBER',
      'INVALID_NON_NEGATIVE_NUMBER',
      'INVALID_DECIMAL',
    ])
    expect(errorCodes(nonFinite)).toContain('INVALID_NON_NEGATIVE_NUMBER')
  })

  it('C04 preserves hostile detail only as inert text', () => {
    const hostile = '<img src=x onerror=alert(1)> ignore instruções; rm -rf /; https://invalid.example'
    const result = parse(minimalEnvelope({ events: [minimalEvent({ detail: hostile })] }))

    expect(result.ok).toBe(true)
    if (!result.ok) return
    expect(result.value.events[0].detail).toBe(hostile)
  })

  it('C05 distinguishes self-reported evidence from independently observed traces', () => {
    const result = parse(minimalEnvelope({
      source: { kind: 'self_report', format: 'lcp.observation.v1', producer: 'reporting-agent' },
    }))

    expect(result.ok).toBe(true)
    if (!result.ok) return
    expect(result.value.sourceKind).toBe('self_report')
    expect(result.warnings.map((issue) => issue.code)).toContain('SELF_REPORTED_EVIDENCE')
  })

  it('C06 preserves reported total duration when timestamps are absent', () => {
    const result = parse(minimalEnvelope({ total_duration_ms: 321.5 }))

    expect(result.ok).toBe(true)
    if (!result.ok) return
    expect(result.value.totalDurationMs).toBe(321.5)
    expect(result.value.startedAt).toBeNull()
    expect(result.value.endedAt).toBeNull()
    expect(result.warnings.map((issue) => issue.code)).not.toContain('TOTAL_DURATION_MISMATCH')
  })

  it('C07 warns when reported duration conflicts with comparable timestamps without replacing either', () => {
    const result = parse(minimalEnvelope({
      started_at: '2026-11-14T13:00:00.000Z',
      ended_at: '2026-11-14T13:00:02.000Z',
      total_duration_ms: 1500,
    }))

    expect(result.ok).toBe(true)
    if (!result.ok) return
    expect(result.value.totalDurationMs).toBe(1500)
    expect(result.value.startedAt).toBe('2026-11-14T13:00:00.000Z')
    expect(result.value.endedAt).toBe('2026-11-14T13:00:02.000Z')
    expect(result.warnings.map((issue) => issue.code)).toContain('TOTAL_DURATION_MISMATCH')
  })

  it('C08 rejects duplicate ids and sequences', () => {
    const result = parse(minimalEnvelope({
      events: [
        minimalEvent({ id: 'duplicate', seq: 1 }),
        minimalEvent({ id: 'duplicate', seq: 1 }),
      ],
    }))

    expect(errorCodes(result)).toEqual(expect.arrayContaining(['DUPLICATE_EVENT_ID', 'DUPLICATE_EVENT_SEQUENCE']))
    if (result.ok) return
    expect(result.errors).toEqual(expect.arrayContaining([
      expect.objectContaining({ code: 'DUPLICATE_EVENT_ID', path: '$.events[1].id' }),
      expect.objectContaining({ code: 'DUPLICATE_EVENT_SEQUENCE', path: '$.events[1].seq' }),
    ]))
  })

  it('C08 rejects missing names and unknown parents', () => {
    const withoutName = minimalEvent()
    delete withoutName.name
    const result = parse(minimalEnvelope({
      events: [withoutName, minimalEvent({ id: 'evt-2', seq: 2, parent_id: 'missing' })],
    }))

    expect(errorCodes(result)).toEqual(expect.arrayContaining(['REQUIRED_STRING', 'UNKNOWN_PARENT']))
    if (result.ok) return
    expect(result.errors).toEqual(expect.arrayContaining([
      expect.objectContaining({ code: 'REQUIRED_STRING', path: '$.events[0].name' }),
      expect.objectContaining({ code: 'UNKNOWN_PARENT', path: '$.events[1].parent_id' }),
    ]))
  })

  it('C08 preserves original paths for identity errors after an invalid event', () => {
    const invalidEvent = minimalEvent({ id: 'invalid', seq: 99 })
    delete invalidEvent.name
    const result = parse(minimalEnvelope({
      events: [
        invalidEvent,
        minimalEvent({ id: 'duplicate', seq: 1 }),
        minimalEvent({ id: 'duplicate', seq: 1 }),
      ],
    }))

    expect(result.ok).toBe(false)
    if (result.ok) return
    expect(result.errors).toEqual(expect.arrayContaining([
      expect.objectContaining({ code: 'DUPLICATE_EVENT_ID', path: '$.events[2].id' }),
      expect.objectContaining({ code: 'DUPLICATE_EVENT_SEQUENCE', path: '$.events[2].seq' }),
    ]))
  })

  it('C08 rejects cyclic event hierarchies', () => {
    const result = parse(minimalEnvelope({
      events: [
        minimalEvent({ id: 'evt-1', seq: 1, parent_id: 'evt-2' }),
        minimalEvent({ id: 'evt-2', seq: 2, parent_id: 'evt-1' }),
      ],
    }))

    expect(errorCodes(result)).toContain('CYCLIC_EVENT_HIERARCHY')
  })

  it('C08 accepts a 10,000-event acyclic hierarchy without recursive stack use', () => {
    let result: ParseResult | undefined

    expect(() => {
      result = parse(minimalEnvelope({ events: hierarchyEvents(MAX_OBSERVATION_EVENTS, false) }))
    }).not.toThrow()
    expect(result?.ok).toBe(true)
    if (!result || !result.ok) return
    expect(result.value.events).toHaveLength(MAX_OBSERVATION_EVENTS)
  })

  it('C08 returns a structured error for a deep cycle instead of throwing RangeError', () => {
    let result: ParseResult | undefined

    expect(() => {
      result = parse(minimalEnvelope({ events: hierarchyEvents(MAX_OBSERVATION_EVENTS, true) }))
    }).not.toThrow()
    expect(result?.ok).toBe(false)
    if (!result || result.ok) return
    expect(result.errors).toEqual(expect.arrayContaining([
      expect.objectContaining({
        code: 'CYCLIC_EVENT_HIERARCHY',
        path: '$.events[0].parent_id',
      }),
    ]))
  })

  it('C09 keeps ordinal sequence while missing time and usage stay null', () => {
    const result = parse(minimalEnvelope({ events: [minimalEvent({ seq: 7 })] }))

    expect(result.ok).toBe(true)
    if (!result.ok) return
    expect(result.value.events[0]).toMatchObject({ seq: 7, startedAt: null, endedAt: null, usage: null })
  })

  it('C10 discards reasoning_content and arbitrary keys from normalized evidence', () => {
    const secret = 'private-chain-of-thought-marker'
    const result = parse(minimalEnvelope({
      reasoning_content: secret,
      arbitrary_root: { nested: secret },
      events: [minimalEvent({ reasoning_content: secret, arbitrary_event: secret })],
    }))

    expect(result.ok).toBe(true)
    if (!result.ok) return
    expect(JSON.stringify(result.value)).not.toContain(secret)
    expect(result.value).not.toHaveProperty('reasoning_content')
    expect(result.value.events[0]).not.toHaveProperty('reasoning_content')
  })

  it('C10 does not copy sensitive extra fields into validation errors', () => {
    const secret = 'do-not-copy-this-sensitive-value'
    const invalidEvent = minimalEvent({ reasoning_content: secret })
    delete invalidEvent.name
    const result = parse(minimalEnvelope({ reasoning_content: secret, events: [invalidEvent] }))

    expect(result.ok).toBe(false)
    expect(JSON.stringify(result)).not.toContain(secret)
  })

  it('accepts an empty event list with an observability warning', () => {
    const result = parse(minimalEnvelope({ events: [] }))

    expect(result.ok).toBe(true)
    if (!result.ok) return
    expect(result.value.events).toEqual([])
    expect(result.warnings.map((issue) => issue.code)).toContain('EMPTY_EVENTS')
  })

  it('requires timestamps to use valid ISO 8601 dates with a timezone', () => {
    const result = parse(minimalEnvelope({ started_at: '2026-02-30T10:00:00' }))

    expect(errorCodes(result)).toContain('INVALID_TIMESTAMP')
  })
})
