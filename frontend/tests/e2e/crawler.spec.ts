import { expect, test } from '@playwright/test'

test.describe('Crawler wizard', () => {
  test('runs crawler with two keywords and minimal config', async ({ page }) => {
    await page.goto('/')
    await page.getByRole('button', { name: 'Browse libraries' }).click()
    await expect(page).toHaveURL(/\/libraries/, { timeout: 60_000 })
    await expect(page.getByText('Browse your saved libraries')).toBeVisible({ timeout: 30_000 })

    const libraryCard = page.locator('[role="button"][aria-disabled="false"]').first()
    await expect(libraryCard).toBeVisible({ timeout: 60_000 })
    await libraryCard.click()

    const workflowDialogButton = page.getByRole('button', { name: 'Crawler workflow' })
    await expect(workflowDialogButton).toBeVisible({ timeout: 30_000 })

    await Promise.all([
      page.waitForURL(/\/crawler\/keywords/, { timeout: 120_000 }),
      workflowDialogButton.click(),
    ])

    const input = page.getByLabel('Keyword or boolean expression')
    await input.fill('fake news')
    await page.getByRole('button', { name: 'Add keyword' }).click()
    await input.fill('misinformation')
    await page.getByRole('button', { name: 'Add keyword' }).click()

    await page.getByRole('button', { name: 'Continue to configuration' }).click()
    await expect(page).toHaveURL(/\/crawler\/configuration/)

    await page.getByRole('button', { name: 'Continue to run' }).click()
    await expect(page).toHaveURL(/\/crawler\/run/)

    await page.getByRole('button', { name: 'Start crawler' }).click()
    await expect(page).toHaveURL(/\/crawler\/results/)

    await expect(page.getByText('Crawler results')).toBeVisible({ timeout: 120_000 })
  })
})
