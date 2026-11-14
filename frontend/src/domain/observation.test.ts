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
      usage: null,
      detail: null,
    })
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
  })

  it('C08 rejects missing names and unknown parents', () => {
    const withoutName = minimalEvent()
    delete withoutName.name
    const result = parse(minimalEnvelope({
      events: [withoutName, minimalEvent({ id: 'evt-2', seq: 2, parent_id: 'missing' })],
    }))

    expect(errorCodes(result)).toEqual(expect.arrayContaining(['REQUIRED_STRING', 'UNKNOWN_PARENT']))
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
