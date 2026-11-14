import { describe, expect, it } from 'vitest'
import comparisonText from '../data/evidence/exp-002-astropy-12907.json?raw'
import { issueContext, parseExperimentComparison, parseUnifiedDiff, publishedOutcomeLabel, toolCalls } from './experiment-comparison'

describe('EXP-002 real SWE-bench evidence', () => {
  it('loads the two verified local trajectories without inventing patches', () => {
    const comparison = parseExperimentComparison(comparisonText)

    expect(comparison.instance_id).toBe('astropy__astropy-12907')
    expect(comparison.runs.map((run) => run.model)).toEqual(['gpt-5.2-codex', 'gpt-5-mini'])
    expect(comparison.runs.map((run) => run.published_resolved)).toEqual([true, true])
    expect(comparison.runs.map((run) => run.patch)).toEqual([null, null])
    expect(comparison.runs.map((run) => toolCalls(run).length)).toEqual([25, 12])
    expect(comparison.runs.map((run) => run.source.local_sha256)).toEqual([
      'b30bc72319e656d8583c36f8e55a0285ff4a903c870e428a26135ebf7de6d7cd',
      'c55885c7fa27a9879582a2243849f0896da4ea687569741e40ca4459fd17cabf',
    ])
    expect(issueContext(comparison)).toContain('nested CompoundModels')
  })

  it('counts changed lines in a unified diff when a source provides one', () => {
    const files = parseUnifiedDiff('diff --git a/a.py b/a.py\n--- a/a.py\n+++ b/a.py\n-old\n+new\n+next')
    expect(files).toMatchObject([{ path: 'a.py', additions: 2, removals: 1 }])
  })

  it('derives the published outcome label from each run result', () => {
    expect(publishedOutcomeLabel(true)).toBe('Resolvido · publicado')
    expect(publishedOutcomeLabel(false)).toBe('Não resolvido · publicado')
  })
})
