export interface ExperimentToolCall {
  readonly id: string | null
  readonly name: string
  readonly arguments: unknown
}

export interface ExperimentEvent {
  readonly index: number
  readonly role: 'system' | 'user' | 'assistant' | 'tool'
  readonly content: string | null
  readonly tool_calls: readonly unknown[]
  readonly tool_call_id?: string | null
}

export interface ExperimentRun {
  readonly model: string
  readonly instance_id: string
  readonly published_resolved: boolean
  readonly exit_status: string
  readonly patch: string | null
  readonly patch_status: 'provided' | 'not_recorded'
  readonly reported_cost_usd: number | null
  readonly reported_api_calls: number | null
  readonly assistant_turns: number
  readonly message_count: number
  readonly events: readonly ExperimentEvent[]
  readonly source: {
    readonly dataset: string
    readonly revision: string
    readonly path: string
    readonly url: string
    readonly local_sha256: string
    readonly source_authenticity_verified: boolean
  }
}

export interface ExperimentComparison {
  readonly schema_version: 'exp-001/v1'
  readonly kind: 'published_external_evidence'
  readonly benchmark_usage: 'case_study_only_not_model_ranking'
  readonly instance_id: string
  readonly comparability: 'same_instance_only'
  readonly re_evaluated_locally: false
  readonly runs: readonly [ExperimentRun, ExperimentRun]
}

export interface DiffFile {
  readonly path: string
  readonly additions: number
  readonly removals: number
  readonly lines: readonly string[]
}

function isRecord(value: unknown): value is Record<string, unknown> {
  return typeof value === 'object' && value !== null && !Array.isArray(value)
}

export function parseExperimentComparison(input: string): ExperimentComparison {
  const value = JSON.parse(input) as unknown
  if (!isRecord(value) || value.schema_version !== 'exp-001/v1' || !Array.isArray(value.runs) || value.runs.length !== 2) {
    throw new Error('Artefato EXP-001 inválido.')
  }
  const runs = value.runs
  for (const run of runs) {
    if (!isRecord(run) || typeof run.model !== 'string' || !Array.isArray(run.events) || !isRecord(run.source)) {
      throw new Error('Tentativa EXP-001 inválida.')
    }
  }
  if (runs[0]?.instance_id !== value.instance_id || runs[1]?.instance_id !== value.instance_id || runs[0]?.model === runs[1]?.model) {
    throw new Error('O par deve conter a mesma issue e modelos diferentes.')
  }
  return value as unknown as ExperimentComparison
}

export function issueContext(comparison: ExperimentComparison): string {
  const content = comparison.runs[0].events.find((event) => event.role === 'user')?.content ?? ''
  const match = content.match(/<pr_description>\s*([\s\S]*?)\s*<\/pr_description>/)
  return (match?.[1] ?? content).trim()
}

export function toolCalls(run: ExperimentRun): readonly ExperimentToolCall[] {
  const calls: ExperimentToolCall[] = []
  for (const event of run.events) {
    for (const value of event.tool_calls) {
      if (!isRecord(value)) continue
      const directName = typeof value.function === 'string' ? value.function : null
      const nested = isRecord(value.function) ? value.function : null
      const name = directName ?? (typeof nested?.name === 'string' ? nested.name : 'ferramenta não identificada')
      calls.push({
        id: typeof value.id === 'string' ? value.id : null,
        name,
        arguments: value.arguments ?? nested?.arguments ?? null,
      })
    }
  }
  return calls
}

export function parseUnifiedDiff(patch: string | null): readonly DiffFile[] {
  if (!patch) return []
  const files: DiffFile[] = []
  let current: { path: string; additions: number; removals: number; lines: string[] } | null = null
  for (const line of patch.split('\n')) {
    if (line.startsWith('diff --git ')) {
      if (current) files.push(current)
      const match = line.match(/^diff --git a\/(.+) b\/(.+)$/)
      current = { path: match?.[2] ?? line.slice(11), additions: 0, removals: 0, lines: [line] }
      continue
    }
    if (!current) continue
    current.lines.push(line)
    if (line.startsWith('+') && !line.startsWith('+++')) current.additions += 1
    if (line.startsWith('-') && !line.startsWith('---')) current.removals += 1
  }
  if (current) files.push(current)
  return files
}

export function formatToolArguments(value: unknown): string {
  if (value === null || value === undefined) return '—'
  if (typeof value === 'string') return value
  try {
    return JSON.stringify(value, null, 2)
  } catch {
    return 'Argumentos indisponíveis.'
  }
}

export function publishedOutcomeLabel(resolved: boolean): string {
  return resolved ? 'Resolvido · publicado' : 'Não resolvido · publicado'
}
