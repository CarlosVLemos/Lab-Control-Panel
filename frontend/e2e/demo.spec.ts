import { expect, test } from '@playwright/test'
import { MAX_OBSERVATION_BYTES } from '../src/domain/observation'

test('executa comparação pela API e apresenta os seis casos persistidos', async ({ page }) => {
  await page.goto('/')
  await page.getByRole('button', { name: 'Classificação sintética' }).click()
  await expect(page.getByText('Nenhuma comparação executada')).toBeVisible()

  const posted = page.waitForResponse((response) =>
    response.url().endsWith('/api/demo/experiments') &&
    response.request().method() === 'POST',
  )
  await page.getByRole('button', { name: 'Executar comparação' }).click()
  const response = await posted
  expect(response.status()).toBe(201)
  const payload = await response.json()
  expect(payload.synthetic).toBe(true)
  expect(payload.cases).toHaveLength(6)

  await expect(page.locator('tbody tr')).toHaveCount(6)
  await expect(page.getByText('2/6 aprovados')).toBeVisible()
  await expect(page.getByText('6/6 aprovados')).toBeVisible()
  await expect(page.getByText('Fonte: API')).toBeVisible()
  await expect(page.getByText('dados sintéticos')).toBeVisible()
})

test('exibe 503 sem substituir a falha por fixture sintética', async ({ page }) => {
  await page.route('**/api/demo/experiments', async (route) => {
    if (route.request().method() === 'POST') {
      await route.fulfill({
        status: 503,
        contentType: 'application/json',
        body: JSON.stringify({ detail: 'Demo database is unavailable' }),
      })
      return
    }
    await route.continue()
  })

  await page.goto('/')
  await page.getByRole('button', { name: 'Classificação sintética' }).click()
  await page.getByRole('button', { name: 'Executar comparação' }).click()

  await expect(page.getByRole('alert')).toContainText('Relatório indisponível')
  await expect(page.getByRole('alert')).toContainText('503')
  await expect(page.locator('tbody tr')).toHaveCount(0)
  await expect(page.getByText('2/6 aprovados')).toHaveCount(0)
})

test('apresenta a evidência CODE-001 como comparável, sem declarar vencedor', async ({ page }) => {
  await page.goto('/')
  await page.getByRole('button', { name: 'CODE-001' }).click()

  await expect(page.getByText('COMPARÁVEL')).toBeVisible()
  await expect(page.getByText('SEM VENCEDOR')).toBeVisible()
  await expect(page.getByText('9/9', { exact: true })).toHaveCount(2)
  await expect(page.getByRole('heading', { name: 'Métricas do agente' })).toBeVisible()
  await expect(page.getByText('Resultados importados · não reexecutados')).toBeVisible()
})

test('remove slogans, banners e rodapé promocional em todas as telas', async ({ page }) => {
  await page.goto('/')
  await expect(page.getByRole('heading', { name: 'Comparação de agentes' })).toBeVisible()
  await expect(page.getByText('Compare decisões.')).toHaveCount(0)
  await expect(page.getByText('Não invente confiança.')).toHaveCount(0)
  await expect(page.getByText('DEMONSTRAÇÃO', { exact: true })).toHaveCount(0)
  await expect(page.locator('footer')).toHaveCount(0)
  await expect(page.getByRole('button', { name: 'Ver estado de erro' })).toHaveCount(0)

  await page.getByRole('button', { name: 'CODE-001' }).click()
  await expect(page.getByText('sem veredito inventado.')).toHaveCount(0)
  await expect(page.getByText('Resultados importados · não reexecutados')).toBeVisible()

  await page.getByRole('button', { name: 'Observabilidade' }).click()
  await expect(page.getByRole('heading', { name: 'Observabilidade' })).toBeVisible()
  await expect(page.getByText('Somente o que foi registrado.')).toHaveCount(0)
  await expect(page.getByText('EVIDÊNCIA LOCAL · SEM UPLOAD')).toHaveCount(0)
  await expect(page.getByText('12 traces carregados · AgentTrace JSONL · coleção · análise determinística')).toBeVisible()
})

test('apresenta EXP-002 real sem reconstruir patches ausentes', async ({ page }) => {
  await page.goto('/')
  await expect(page.getByRole('heading', { name: 'gpt-5.2-codex' })).toBeVisible()
  await expect(page.getByRole('heading', { name: 'gpt-5-mini' })).toBeVisible()
  await expect(page.getByText('Resolvido · publicado')).toHaveCount(2)
  await expect(page.locator('.patch-card')).toContainText('info.submission está vazio nas duas trajetórias')
})

test('investiga a coleção OBS-002 real e abre evidência diagnóstica', async ({ page }) => {
  await page.goto('/')
  await page.getByRole('button', { name: 'Observabilidade' }).click()
  await expect(page.getByText('Evidência validada.')).toBeVisible()
  await expect(page.getByText('12', { exact: true }).first()).toBeVisible()
  await expect(page.getByRole('heading', { name: 'Diagnósticos determinísticos' })).toBeVisible()
  await page.getByText('Chamada idêntica repetida 2 vezes').click()
  await expect(page.getByText('f118f268-e868-4074-a691-dd1a981f3f87', { exact: true })).toBeVisible()
})

test('limpa evidência anterior quando uma nova importação é inválida ou ilegível', async ({ page }) => {
  await page.goto('/')
  await page.getByRole('button', { name: 'Observabilidade' }).click()
  const input = page.locator('#observation-file')
  const restore = page.getByRole('button', { name: 'Restaurar amostra real' })

  await expect(page.locator('.overview-kpis')).toBeVisible()
  await input.setInputFiles({ name: 'empty.json', mimeType: 'application/json', buffer: Buffer.from('') })
  await expect(page.getByRole('alert')).toContainText('EMPTY_FILE')
  await expect(page.locator('.overview-kpis')).toHaveCount(0)
  await expect(page.locator('.lane-card')).toHaveCount(0)

  await restore.click()
  await input.setInputFiles({ name: 'large.json', mimeType: 'application/json', buffer: Buffer.alloc(MAX_OBSERVATION_BYTES + 1, 32) })
  await expect(page.getByRole('alert')).toContainText('INPUT_TOO_LARGE')
  await expect(page.locator('.overview-kpis')).toHaveCount(0)

  await restore.click()
  await input.setInputFiles({ name: 'malformed.json', mimeType: 'application/json', buffer: Buffer.from('{') })
  await expect(page.getByRole('alert')).toContainText('INVALID_COLLECTION')
  await expect(page.locator('.overview-kpis')).toHaveCount(0)

  await restore.click()
  await page.evaluate(() => { File.prototype.text = async () => { throw new Error('read failed') } })
  await input.setInputFiles({ name: 'unreadable.json', mimeType: 'application/json', buffer: Buffer.from('{}') })
  await expect(page.getByRole('alert')).toContainText('FILE_READ_FAILED')
  await expect(page.locator('.overview-kpis')).toHaveCount(0)
})


test('aplica status por trace e limpa a seleção quando os filtros não retornam execuções', async ({ page }) => {
  await page.goto('/')
  await page.getByRole('button', { name: 'Observabilidade' }).click()

  // Ordem dos campos na interface: Modelo, Ferramenta, Status
  const filters = page.locator('.trace-filters select')

  await expect(filters).toHaveCount(3)

  const modelFilter = filters.nth(0)
  const toolFilter = filters.nth(1)
  const statusFilter = filters.nth(2)

  // Verifica que execuções com falhas não são classificadas como sucesso
  await modelFilter.selectOption('Qwen/Qwen3-1.7B')
  await statusFilter.selectOption('success')

  await expect(page.locator('.trace-list')).not.toContainText('nl2bash/1')

  // Verifica o estado vazio quando os filtros não encontram resultados
  await modelFilter.selectOption('Qwen/Qwen3-0.6B')
  await toolFilter.selectOption('python_interpreter')

  await expect(
    page.getByText('Nenhuma execução corresponde aos filtros selecionados.')
  ).toBeVisible()

  await expect(page.locator('.trace-list button.selected')).toHaveCount(0)
  await expect(page.locator('.lane-card')).toHaveCount(0)

  // Verifica que uma seleção válida é restaurada quando há resultados
  await statusFilter.selectOption('error')

  await expect(page.locator('.trace-list button.selected')).toHaveCount(1)
  await expect(page.locator('.lane-card')).toBeVisible()
})

