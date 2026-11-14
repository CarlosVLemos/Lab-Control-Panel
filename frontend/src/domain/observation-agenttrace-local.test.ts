import { createHash } from 'node:crypto'
import { readFileSync } from 'node:fs'
import { describe, expect, it } from 'vitest'
import { parseAgentTrace } from './observation-agenttrace'

const samplePath = process.env.AGENTTRACE_SAMPLE_PATH

describe.skipIf(!samplePath)('local sanitized AgentTrace sample', () => {
  it('E11 matches the operator-provided sample hash and frozen 2+2 mapping', () => {
    if (!samplePath) throw new Error('AGENTTRACE_SAMPLE_PATH is required for this operator-controlled test.')
    const input = readFileSync(samplePath, 'utf8')
    expect(createHash('sha256').update(input).digest('hex')).toBe(
      'f765bdef22eaed2c7e7e054cd2d3f8c4fbc58d69e3fd05a7bfb5c8fec0977974',
    )

    const result = parseAgentTrace(input)
    expect(result.ok).toBe(true)
    if (!result.ok) return
    expect(result.value).toMatchObject({
      agent: { name: null, model: 'Qwen/Qwen3-0.6B' },
      totalDurationMs: 15910.931417,
    })
    expect(result.value.events).toHaveLength(4)
    expect(result.value.events.map((event) => [event.kind, event.name, event.status])).toEqual([
      ['model', 'llm_step', 'unknown'],
      ['model', 'llm_step', 'unknown'],
      ['tool', 'bash', 'error'],
      ['message', 'final_answer', 'unknown'],
    ])
    expect(result.value.events.slice(0, 2).map((event) => event.usage)).toEqual([
      { inputTokens: 1510, outputTokens: 944, durationMs: null, costUsd: null },
      { inputTokens: 1612, outputTokens: 495, durationMs: null, costUsd: null },
    ])
    expect(result.warnings.map((issue) => issue.code)).toEqual(expect.arrayContaining([
      'PARTIAL_ORDER_ONLY',
      'SOURCE_NOT_AUTHENTICATED',
      'TELEMETRY_IGNORED',
      'SANITIZATION_SELF_DECLARED',
    ]))
  })
})
