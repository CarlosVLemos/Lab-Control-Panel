import type { ObservationEvent, ObservationRun } from './observation'

export interface KnownNumber {
  readonly value: number | null
  readonly known: number
  readonly eligible: number
}

export interface DurationMetric {
  readonly valueMs: number | null
  readonly basis: 'reported' | 'derived' | 'unavailable'
}

export interface TokenPoint {
  readonly eventId: string
  readonly ordinal: number | null
  readonly inputTokens: number | null
  readonly outputTokens: number | null
  readonly cumulativeInputTokens: number | null
  readonly cumulativeOutputTokens: number | null
  readonly cumulativeTotalTokens: number | null
}

export interface ObservationMetrics {
  readonly summary: {
    readonly eventCount: number
    readonly modelStepCount: number
    readonly toolCallCount: number
    readonly messageCount: number
    readonly explicitErrorCount: number
    readonly unknownStatusCount: number
    readonly duration: DurationMetric
    readonly inputTokens: KnownNumber
    readonly outputTokens: KnownNumber
    readonly totalTokens: number | null
    readonly reportedCostUsd: string | null
  }
  readonly tokenSeries: readonly TokenPoint[]
  readonly warnings: readonly string[]
}

interface DimensionAggregate {
  readonly metric: KnownNumber
  readonly unsafe: boolean
}

function safeTokenSum(left: number, right: number): number | null {
  if (!Number.isSafeInteger(left) || !Number.isSafeInteger(right) || left < 0 || right < 0) return null
  const sum = left + right
  return Number.isSafeInteger(sum) && sum >= 0 ? sum : null
}

function aggregateDimension(values: readonly (number | null)[], ambiguous: boolean): DimensionAggregate {
  const known = values.filter((value) => value !== null).length
  if (values.length === 0) {
    return { metric: { value: null, known: 0, eligible: 0 }, unsafe: false }
  }

  let sum = 0
  let unsafe = false
  for (const value of values) {
    if (value === null) continue
    const next = safeTokenSum(sum, value)
    if (next === null) {
      unsafe = true
      break
    }
    sum = next
  }

  const complete = known === values.length
  return {
    metric: {
      value: complete && !ambiguous && !unsafe ? sum : null,
      known,
      eligible: values.length,
    },
    unsafe,
  }
}

function durationMetric(run: ObservationRun): DurationMetric {
  if (run.totalDurationMs !== null) {
    return { valueMs: run.totalDurationMs, basis: 'reported' }
  }
  if (run.startedAt === null || run.endedAt === null) {
    return { valueMs: null, basis: 'unavailable' }
  }

  const intervalMs = Date.parse(run.endedAt) - Date.parse(run.startedAt)
  return Number.isFinite(intervalMs) && intervalMs >= 0
    ? { valueMs: intervalMs, basis: 'derived' }
    : { valueMs: null, basis: 'unavailable' }
}

function hasModelUsageHierarchy(events: readonly ObservationEvent[]): boolean {
  const eventsById = new Map(events.map((event) => [event.id, event] as const))
  const modelIds = new Set(events.filter((event) => event.kind === 'model').map((event) => event.id))
  const memo = new Map<string, boolean>()

  for (const event of events) {
    if (event.kind !== 'model' || event.parentId === null) continue
    const traversed: string[] = []
    let currentId: string | null = event.parentId
    let hasModelAncestor = false

    while (currentId !== null) {
      if (modelIds.has(currentId)) {
        hasModelAncestor = true
        break
      }
      const memoized = memo.get(currentId)
      if (memoized !== undefined) {
        hasModelAncestor = memoized
        break
      }
      traversed.push(currentId)
      currentId = eventsById.get(currentId)?.parentId ?? null
    }
    for (const id of traversed) memo.set(id, hasModelAncestor)
    memo.set(event.id, hasModelAncestor)
    if (hasModelAncestor) return true
  }
  return false
}

function orderModelEvents(events: readonly ObservationEvent[]): {
  readonly events: readonly ObservationEvent[]
  readonly usesSerializationOrder: boolean
} {
  const modelEvents = events.filter((event) => event.kind === 'model')
  const ordinals = modelEvents.map((event) => event.position?.basis === 'ordinal' ? event.position.ordinal : null)
  const allOrdinal = ordinals.every((ordinal): ordinal is number => ordinal !== null)
  const uniqueOrdinal = allOrdinal && new Set(ordinals).size === ordinals.length

  if (uniqueOrdinal) {
    return {
      events: [...modelEvents].sort((left, right) => {
        const leftOrdinal = left.position?.basis === 'ordinal' ? left.position.ordinal : 0
        const rightOrdinal = right.position?.basis === 'ordinal' ? right.position.ordinal : 0
        return leftOrdinal - rightOrdinal
      }),
      usesSerializationOrder: false,
    }
  }
  return {
    events: [...modelEvents].sort((left, right) => left.seq - right.seq),
    usesSerializationOrder: modelEvents.length > 0,
  }
}

function buildTokenSeries(
  events: readonly ObservationEvent[],
  ambiguous: boolean,
): { readonly points: readonly TokenPoint[]; readonly inputUnsafe: boolean; readonly outputUnsafe: boolean; readonly totalUnsafe: boolean } {
  let inputCumulative = 0
  let outputCumulative = 0
  let inputAvailable = !ambiguous
  let outputAvailable = !ambiguous
  let totalAvailable = !ambiguous
  let inputUnsafe = false
  let outputUnsafe = false
  let totalUnsafe = false

  const points = events.map((event): TokenPoint => {
    const inputTokens = event.usage?.inputTokens ?? null
    const outputTokens = event.usage?.outputTokens ?? null

    if (inputAvailable) {
      if (inputTokens === null) inputAvailable = false
      else {
        const next = safeTokenSum(inputCumulative, inputTokens)
        if (next === null) {
          inputAvailable = false
          inputUnsafe = true
        } else inputCumulative = next
      }
    }
    if (outputAvailable) {
      if (outputTokens === null) outputAvailable = false
      else {
        const next = safeTokenSum(outputCumulative, outputTokens)
        if (next === null) {
          outputAvailable = false
          outputUnsafe = true
        } else outputCumulative = next
      }
    }

    const cumulativeInputTokens = inputAvailable ? inputCumulative : null
    const cumulativeOutputTokens = outputAvailable ? outputCumulative : null
    let cumulativeTotalTokens: number | null = null
    if (totalAvailable && cumulativeInputTokens !== null && cumulativeOutputTokens !== null) {
      const next = safeTokenSum(cumulativeInputTokens, cumulativeOutputTokens)
      if (next === null) {
        totalAvailable = false
        totalUnsafe = true
      } else cumulativeTotalTokens = next
    } else {
      totalAvailable = false
    }

    return {
      eventId: event.id,
      ordinal: event.position?.basis === 'ordinal' ? event.position.ordinal : null,
      inputTokens,
      outputTokens,
      cumulativeInputTokens,
      cumulativeOutputTokens,
      cumulativeTotalTokens,
    }
  })

  return { points, inputUnsafe, outputUnsafe, totalUnsafe }
}

export function computeObservationMetrics(run: ObservationRun): ObservationMetrics {
  const warnings: string[] = []
  const addWarning = (code: string): void => {
    if (!warnings.includes(code)) warnings.push(code)
  }
  for (const issue of run.warnings) addWarning(issue.code)
  if (run.sourceKind === 'self_report') addWarning('SELF_REPORTED_EVIDENCE')

  const ordered = orderModelEvents(run.events)
  if (ordered.usesSerializationOrder) addWarning('TOKEN_SERIES_SERIALIZATION_ORDER')
  const ambiguous = hasModelUsageHierarchy(run.events)
  if (ambiguous) addWarning('AMBIGUOUS_MODEL_USAGE_HIERARCHY')

  const inputValues = ordered.events.map((event) => event.usage?.inputTokens ?? null)
  const outputValues = ordered.events.map((event) => event.usage?.outputTokens ?? null)
  const inputAggregate = aggregateDimension(inputValues, ambiguous)
  const outputAggregate = aggregateDimension(outputValues, ambiguous)

  if (ordered.events.length === 0) addWarning('TOKEN_USAGE_UNAVAILABLE')
  else {
    if (inputAggregate.metric.known < inputAggregate.metric.eligible) addWarning('INPUT_TOKEN_COVERAGE_PARTIAL')
    if (outputAggregate.metric.known < outputAggregate.metric.eligible) addWarning('OUTPUT_TOKEN_COVERAGE_PARTIAL')
  }
  if (inputAggregate.unsafe) addWarning('INPUT_TOKEN_SUM_UNSAFE')
  if (outputAggregate.unsafe) addWarning('OUTPUT_TOKEN_SUM_UNSAFE')

  const series = buildTokenSeries(ordered.events, ambiguous)
  if (series.inputUnsafe) addWarning('INPUT_TOKEN_SUM_UNSAFE')
  if (series.outputUnsafe) addWarning('OUTPUT_TOKEN_SUM_UNSAFE')
  if (series.totalUnsafe) addWarning('TOTAL_TOKEN_SUM_UNSAFE')

  let totalTokens: number | null = null
  if (inputAggregate.metric.value !== null && outputAggregate.metric.value !== null) {
    totalTokens = safeTokenSum(inputAggregate.metric.value, outputAggregate.metric.value)
    if (totalTokens === null) addWarning('TOTAL_TOKEN_SUM_UNSAFE')
  }

  const duration = durationMetric(run)
  if (duration.basis === 'unavailable') addWarning('DURATION_UNAVAILABLE')
  if (run.events.some((event) => event.usage?.costUsd !== null && event.usage?.costUsd !== undefined)) {
    addWarning('COST_AGGREGATION_UNAVAILABLE')
  }

  return {
    summary: {
      eventCount: run.events.length,
      modelStepCount: ordered.events.length,
      toolCallCount: run.events.filter((event) => event.kind === 'tool').length,
      messageCount: run.events.filter((event) => event.kind === 'message').length,
      explicitErrorCount: run.events.filter((event) => event.status === 'error').length,
      unknownStatusCount: run.events.filter((event) => event.status === 'unknown').length,
      duration,
      inputTokens: inputAggregate.metric,
      outputTokens: outputAggregate.metric,
      totalTokens,
      reportedCostUsd: null,
    },
    tokenSeries: series.points,
    warnings,
  }
}
