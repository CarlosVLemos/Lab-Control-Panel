import { afterEach, describe, expect, it, vi } from 'vitest'
import { fixtureSource } from './synthetic-fixture'
import { HttpReportSource } from './report-source'

describe('report sources', () => {
  afterEach(() => vi.unstubAllGlobals())

  it('exposes the explicitly selected synthetic fixture', async () => {
    await expect(fixtureSource.load()).resolves.toMatchObject({ synthetic: true, experimentId: 'demo-support-intents-v1' })
  })

  it('rejects an HTTP failure instead of returning fixture data', async () => {
    vi.stubGlobal('fetch', vi.fn().mockResolvedValue({ ok: false, status: 503 }))
    await expect(new HttpReportSource('/api/report').load()).rejects.toThrow('503')
  })
})
