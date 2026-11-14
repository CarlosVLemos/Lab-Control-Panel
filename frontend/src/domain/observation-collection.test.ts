import { readFileSync } from 'node:fs'
import { describe, expect, it } from 'vitest'
import realSampleText from '../data/evidence/obs-002-agenttrace-sample.json?raw'
import {
  collectionDiagnostics, collectionOverview, durationOutlierFence, parseAgentTraceCollection,
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
