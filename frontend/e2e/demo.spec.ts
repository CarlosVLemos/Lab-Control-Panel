import { expect, test } from '@playwright/test'

test('executa comparação pela API e apresenta os seis casos persistidos', async ({ page }) => {
  await page.goto('/')
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
  await expect(page.getByText('2 de 6 casos aprovados')).toBeVisible()
  await expect(page.getByText('6 de 6 casos aprovados')).toBeVisible()
  await expect(page.getByText(/FONTE · API PERSISTIDA/)).toBeVisible()
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
  await page.getByRole('button', { name: 'Executar comparação' }).click()

  await expect(page.getByRole('alert')).toContainText('Relatório indisponível')
  await expect(page.getByRole('alert')).toContainText('503')
  await expect(page.getByRole('alert')).toContainText('Nenhum resultado sintético é usado como fallback')
  await expect(page.locator('tbody tr')).toHaveCount(0)
  await expect(page.getByText('2 de 6 casos aprovados')).toHaveCount(0)
})

test('apresenta a evidência CODE-001 como comparável, sem declarar vencedor', async ({ page }) => {
  await page.goto('/')
  await page.getByRole('button', { name: 'Code Evaluation' }).click()

  await expect(page.getByText('COMPARÁVEL')).toBeVisible()
  await expect(page.getByText('SEM VENCEDOR')).toBeVisible()
  await expect(page.getByText('9/9', { exact: true })).toHaveCount(2)
  await expect(page.getByText('Não observadas')).toBeVisible()
  await expect(page.getByText('Fixture versionada da saída do importador offline')).toBeVisible()
})
