import { test, expect } from '@playwright/test'

test.describe('Author topic evolution workflow', () => {
  test('searches for an author and reaches the configuration step', async ({ page }) => {
    const authorName = 'Jason Priem'

    await page.goto('/author-topic-evolution/select')

    await page.getByPlaceholder('Ada Lovelace').fill(authorName)
    await page.getByRole('button', { name: 'Search' }).click()

    const authorOption = page.getByRole('button', { name: new RegExp(authorName, 'i') }).first()
    await expect(authorOption).toBeVisible({ timeout: 120_000 })
    await authorOption.click()

    const continueButton = page.getByRole('button', { name: 'Continue to configuration' })
    await expect(continueButton).toBeEnabled()
    await continueButton.click()

    await expect(page).toHaveURL(/author-topic-evolution\/configure/)
    await expect(page.getByText('Model configuration')).toBeVisible()
    await expect(page.getByText('Save as a permanent library')).toBeVisible()

    const runButton = page.getByRole('button', { name: 'Run analysis' })
    await expect(runButton).toBeVisible()
    await expect(runButton).toBeEnabled()
  })
})
