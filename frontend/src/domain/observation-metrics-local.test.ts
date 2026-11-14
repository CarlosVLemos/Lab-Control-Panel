import { createHash } from 'node:crypto'
import { readFileSync } from 'node:fs'
import { describe, expect, it } from 'vitest'
import { parseAgentTrace } from './observation-agenttrace'
import { computeObservationMetrics } from './observation-metrics'

const samplePath = process.env.AGENTTRACE_SAMPLE_PATH

describe.skipIf(!samplePath)('local AgentTrace metrics oracle', () => {
  it('M05 matches the operator-provided sanitized sample and frozen Stage C totals', () => {
    if (!samplePath) throw new Error('AGENTTRACE_SAMPLE_PATH is required for this operator-controlled test.')
    const input = readFileSync(samplePath, 'utf8')
    expect(createHash('sha256').update(input).digest('hex')).toBe(
      'f765bdef22eaed2c7e7e054cd2d3f8c4fbc58d69e3fd05a7bfb5c8fec0977974',
    )

    const adapted = parseAgentTrace(input)
    expect(adapted.ok).toBe(true)
    if (!adapted.ok) return

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
    expect(metrics.tokenSeries).toMatchObject([
      {
        ordinal: 1,
        inputTokens: 1510,
        outputTokens: 944,
        cumulativeInputTokens: 1510,
        cumulativeOutputTokens: 944,
        cumulativeTotalTokens: 2454,
      },
      {
        ordinal: 2,
        inputTokens: 1612,
        outputTokens: 495,
        cumulativeInputTokens: 3122,
        cumulativeOutputTokens: 1439,
        cumulativeTotalTokens: 4561,
      },
    ])
  })
})
