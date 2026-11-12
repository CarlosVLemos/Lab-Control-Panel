export type Strategy = 'WITH_SPEC' | 'WITHOUT_SPEC'
export type EvaluationState = 'valid' | 'missing' | 'invalid' | 'inconclusive'

export interface CodeArtifact {
  task_id: string
  repository: string
  base_commit: string
  agent: string
  model: string
  strategy: Strategy
  provenance: string
  tests: { total: number; passed: number; failed: number; errors: number; skipped: number }
  diff: { added_lines: number; removed_lines: number }
  source_hashes: { manifest_sha256: string; junit_sha256: string; diff_sha256: string }
  usage: Record<string, number | string> | null
}

export interface CodeEvaluation {
  status: 'COMPARABLE' | 'INCONCLUSIVE'
  reasons: string[]
  interpretation: string
  observed: CodeArtifact[]
}

export type EvaluationLoad =
  | { state: 'valid'; evaluation: CodeEvaluation }
  | { state: 'inconclusive'; evaluation: CodeEvaluation }
  | { state: 'missing'; message: string }
  | { state: 'invalid'; message: string }

const strategies: readonly Strategy[] = ['WITH_SPEC', 'WITHOUT_SPEC']

function isRecord(value: unknown): value is Record<string, unknown> {
  return typeof value === 'object' && value !== null && !Array.isArray(value)
}

function isCount(value: unknown): value is number {
  return typeof value === 'number' && Number.isInteger(value) && value >= 0
}

function isArtifact(value: unknown): value is CodeArtifact {
  if (!isRecord(value) || !strategies.includes(value.strategy as Strategy)) return false
  const strings = ['task_id', 'repository', 'base_commit', 'agent', 'model', 'provenance']
  if (!strings.every((key) => typeof value[key] === 'string' && value[key])) return false
  const tests = value.tests
  const diff = value.diff
  const sourceHashes = value.source_hashes
  if (!isRecord(tests) || !['total', 'passed', 'failed', 'errors', 'skipped'].every((key) => isCount(tests[key]))) return false
  if (!isRecord(diff) || !isCount(diff.added_lines) || !isCount(diff.removed_lines)) return false
  if (!isRecord(sourceHashes) || !['manifest_sha256', 'junit_sha256', 'diff_sha256'].every((key) => typeof sourceHashes[key] === 'string' && sourceHashes[key])) return false
  return value.usage === null || isRecord(value.usage)
}

export function loadCodeEvaluation(value: unknown): EvaluationLoad {
  if (value === null || value === undefined) return { state: 'missing', message: 'Nenhum arquivo de avaliação foi fornecido.' }
  if (!isRecord(value) || (value.status !== 'COMPARABLE' && value.status !== 'INCONCLUSIVE') || !Array.isArray(value.reasons) || !value.reasons.every((item) => typeof item === 'string') || typeof value.interpretation !== 'string' || !Array.isArray(value.observed) || value.observed.length !== 2 || !value.observed.every(isArtifact)) {
    return { state: 'invalid', message: 'A exportação v1a não atende ao contrato esperado.' }
  }
  const evaluation: CodeEvaluation = {
    status: value.status,
    reasons: value.reasons as string[],
    interpretation: value.interpretation,
    observed: value.observed as CodeArtifact[],
  }
  const observedStrategies = new Set(evaluation.observed.map((item) => item.strategy))
  if (observedStrategies.size !== 2 || !strategies.every((strategy) => observedStrategies.has(strategy))) {
    return { state: 'invalid', message: 'A comparação deve conter exatamente um candidato de cada estratégia.' }
  }
  return evaluation.status === 'COMPARABLE'
    ? { state: 'valid', evaluation }
    : { state: 'inconclusive', evaluation }
}

export function candidateCommit(artifact: CodeArtifact): string | null {
  const match = artifact.provenance.match(/candidate=([0-9a-f]{7,40})/)
  return match?.[1] ?? null
}

export function metricLabel(artifact: CodeArtifact, metric: 'input_tokens' | 'output_tokens' | 'duration_ms' | 'cost_usd'): string {
  const value = artifact.usage?.[metric]
  return value === undefined ? 'Desconhecida' : String(value)
}
