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
  await page.getByRole('button', { name: 'Executar comparação' }).click()

  await expect(page.getByRole('alert')).toContainText('Relatório indisponível')
  await expect(page.getByRole('alert')).toContainText('503')
  await expect(page.locator('tbody tr')).toHaveCount(0)
  await expect(page.getByText('2/6 aprovados')).toHaveCount(0)
})

test('apresenta a evidência CODE-001 como comparável, sem declarar vencedor', async ({ page }) => {
  await page.goto('/')
  await page.getByRole('button', { name: 'Código' }).click()

  await expect(page.getByText('COMPARÁVEL')).toBeVisible()
  await expect(page.getByText('SEM VENCEDOR')).toBeVisible()
  await expect(page.getByText('9/9', { exact: true })).toHaveCount(2)
  await expect(page.getByRole('heading', { name: 'Métricas do agente' })).toBeVisible()
  await expect(page.getByText('Resultados importados · não reexecutados')).toBeVisible()
})

test('remove slogans, banners e rodapé promocional', async ({ page }) => {
  await page.goto('/')
  await expect(page.getByRole('heading', { name: 'Comparação de classificadores' })).toBeVisible()
  await expect(page.getByText('Compare decisões.')).toHaveCount(0)
  await expect(page.getByText('Não invente confiança.')).toHaveCount(0)
  await expect(page.getByText('DEMONSTRAÇÃO', { exact: true })).toHaveCount(0)
  await expect(page.locator('footer')).toHaveCount(0)
  await expect(page.getByRole('button', { name: 'Ver estado de erro' })).toHaveCount(0)

  await page.getByRole('button', { name: 'Código' }).click()
  await expect(page.getByText('sem veredito inventado.')).toHaveCount(0)
  await expect(page.getByText('Resultados importados · não reexecutados')).toBeVisible()
})
