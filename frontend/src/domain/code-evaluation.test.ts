import { describe, expect, it } from 'vitest'
import rawCode001Import from '../data/code-001-import.json'
import { candidateCommit, loadCodeEvaluation, metricLabel } from './code-evaluation'

describe('v1a code evaluation presentation adapter', () => {
  it('accepts the real CODE-001 importer export without fabricating usage', () => {
    const loaded = loadCodeEvaluation(rawCode001Import)
    expect(loaded.state).toBe('valid')
    if (loaded.state !== 'valid') return
    expect(loaded.evaluation.observed.map((item) => item.strategy).sort()).toEqual(['WITHOUT_SPEC', 'WITH_SPEC'].sort())
    expect(metricLabel(loaded.evaluation.observed[0], 'cost_usd')).toBe('Desconhecida')
    expect(candidateCommit(loaded.evaluation.observed[0])).toBe('97cdd3ef6fcbb36c1945d58c2be64ffd2d952540')
  })

  it('renders a missing export as missing evidence', () => {
    expect(loadCodeEvaluation(null)).toMatchObject({ state: 'missing' })
  })

  it('rejects an invalid export instead of treating it as comparable', () => {
    expect(loadCodeEvaluation({ status: 'COMPARABLE', observed: [] })).toMatchObject({ state: 'invalid' })
  })

  it('keeps an importer inconclusive result distinct from invalid evidence', () => {
    const inconclusive = { ...rawCode001Import, status: 'INCONCLUSIVE', reasons: ['Different base_commit'] }
    expect(loadCodeEvaluation(inconclusive)).toMatchObject({ state: 'inconclusive' })
  })
})
