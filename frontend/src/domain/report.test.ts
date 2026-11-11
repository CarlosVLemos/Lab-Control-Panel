import { describe, expect, it } from 'vitest'
import { accuracy, displayOutput, evidenceState } from './report'
import { syntheticReport } from '../data/synthetic-fixture'

describe('report transformations', () => {
  it('calculates an accuracy from the executed fixture cases', () => {
    expect(accuracy(syntheticReport.summary.baseline.passed, syntheticReport.summary.baseline.total)).toBe(60)
    expect(accuracy(syntheticReport.summary.candidate.passed, syntheticReport.summary.candidate.total)).toBe(80)
  })

  it('displays unavailable outputs safely without inventing a pass', () => {
    expect(displayOutput({})).toBe('Indisponível')
    expect(displayOutput(null)).toBe('Indisponível')
    expect(displayOutput({ label: 'complaint' })).toBe('complaint')
  })

  it('identifies improvement, regression, and stable evidence', () => {
    expect(evidenceState(syntheticReport.cases[0])).toBe('improved')
    expect(evidenceState(syntheticReport.cases[3])).toBe('regressed')
    expect(evidenceState(syntheticReport.cases[1])).toBe('stable')
  })
})
