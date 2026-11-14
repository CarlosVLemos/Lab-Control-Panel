import { readFileSync } from 'node:fs'
import { describe, expect, it } from 'vitest'
import realSampleText from '../data/evidence/obs-002-agenttrace-sample.json?raw'
import {
  classifyTraceStatus, collectionDiagnostics, collectionOverview, durationOutlierFence,
  parseAgentTraceCollection, resolveTraceSelection, traceCountLabel,
} from './observation-collection'

describe('OBS-002 real AgentTrace collection', () => {
  it('reports the observed overview and model comparison from 12 real traces', () => {
    const parsed = parseAgentTraceCollection(realSampleText)
    expect(parsed.ok).toBe(true)
    if (!parsed.ok) return

    expect(parsed.value.source.localSha256).toBe('b7aaff70cfa9e5e240b402c07641f442febd9d8c762f5d5ba50bc543be8c3b5f')
    expect(collectionOverview(parsed.value)).toEqual({
      traces: 12,
      durationP50Ms: 30760.982542,
      durationP95Ms: 2553495.658209,
      toolCalls: 14,
      failures: 9,
      models: [
        { model: 'Qwen/Qwen3-0.6B', traces: 6, durationP50Ms: 15910.931417, toolCalls: 4, failures: 2 },
        { model: 'Qwen/Qwen3-1.7B', traces: 6, durationP50Ms: 54636.437875, toolCalls: 10, failures: 7 },
      ],
    })
    expect(durationOutlierFence(parsed.value.traces)).toBeCloseTo(241829.55672975)
  })

  it('links deterministic diagnostics to trace and span evidence', () => {
    const parsed = parseAgentTraceCollection(realSampleText)
    if (!parsed.ok) throw new Error('Real derived collection must parse.')
    const diagnostics = collectionDiagnostics(parsed.value)

    expect(diagnostics.filter((item) => item.kind === 'tool_error')).toHaveLength(9)
    expect(diagnostics.filter((item) => item.kind === 'repeated_call')).toHaveLength(1)
    expect(diagnostics.filter((item) => item.kind === 'duration_outlier')).toHaveLength(2)
    expect(diagnostics.filter((item) => item.kind === 'top_contributor')).toHaveLength(5)
    expect(diagnostics.find((item) => item.kind === 'repeated_call')).toMatchObject({
      traceId: '2ff930d3-6a11-4735-a556-665b39fb1503',
      spanId: 'f118f268-e868-4074-a691-dd1a981f3f87',
    })
  })

  it('classifies a trace with any failed tool as error, even when another tool succeeds', () => {
    const parsed = parseAgentTraceCollection(realSampleText)
    if (!parsed.ok) throw new Error('Real derived collection must parse.')

    const mixed = parsed.value.traces.find((trace) => trace.traceId === '85f4513a-af6a-4bb9-b1ac-dd290613b85f')
    const successful = parsed.value.traces.find((trace) => trace.traceId === '525b7ff2-3dbe-4e8e-ad50-de19c0739a27')
    const unknown = parsed.value.traces.find((trace) => trace.traceId === 'dc797f46-d2f2-453c-b5d3-3d8e761b395b')

    expect(mixed && classifyTraceStatus(mixed)).toBe('error')
    expect(successful && classifyTraceStatus(successful)).toBe('success')
    expect(unknown && classifyTraceStatus(unknown)).toBe('unknown')
  })

  it('keeps a valid filtered selection, selects the first fallback, and clears an empty result', () => {
    const parsed = parseAgentTraceCollection(realSampleText)
    if (!parsed.ok) throw new Error('Real derived collection must parse.')
    const first = parsed.value.traces[0]!
    const second = parsed.value.traces[1]!

    expect(resolveTraceSelection([first, second], second.traceId)?.traceId).toBe(second.traceId)
    expect(resolveTraceSelection([first], second.traceId)?.traceId).toBe(first.traceId)
    expect(resolveTraceSelection([], second.traceId)).toBeNull()
  })

  it('derives singular and plural trace labels from the loaded collection size', () => {
    expect(traceCountLabel(1)).toBe('1 trace carregado')
    expect(traceCountLabel(12)).toBe('12 traces carregados')
  })
})

const localPath = process.env.AGENTTRACE_COLLECTION_PATH
describe.skipIf(!localPath)('operator-provided real AgentTrace JSONL', () => {
  it('parses every downloaded line through the existing AgentTrace adapter', () => {
    if (!localPath) throw new Error('AGENTTRACE_COLLECTION_PATH is required.')
    const parsed = parseAgentTraceCollection(readFileSync(localPath, 'utf8'))
    expect(parsed.ok).toBe(true)
    if (parsed.ok) expect(parsed.value.traces).toHaveLength(12)
  })
})
