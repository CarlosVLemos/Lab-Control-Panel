export interface ModelDescriptor { id: string; label: string }
export interface Verdict { output: { label?: string } | null; passed: boolean }
export interface ExperimentCase {
  id: string
  input: { text: string }
  expected: { label: string }
  baseline: Verdict
  candidate: Verdict
}
export interface ExperimentReport {
  experimentId: string
  synthetic: boolean
  dataset: { id: string; version: string }
  baseline: ModelDescriptor
  candidate: ModelDescriptor
  summary: { baseline: { passed: number; total: number }; candidate: { passed: number; total: number } }
  cases: ExperimentCase[]
}

export function displayOutput(output: Verdict['output']): string {
  return output?.label ?? 'Indisponível'
}

export type ModelKey = 'baseline' | 'candidate'

export function accuracy(passed: number, total: number): number {
  return total === 0 ? 0 : Math.round((passed / total) * 100)
}

export function evidenceState(item: ExperimentCase): 'improved' | 'regressed' | 'stable' {
  if (!item.baseline.passed && item.candidate.passed) return 'improved'
  if (item.baseline.passed && !item.candidate.passed) return 'regressed'
  return 'stable'
}
