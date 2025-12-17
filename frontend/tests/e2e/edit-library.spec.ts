import { expect, test } from '@playwright/test'

test.describe('Edit library workflow', () => {
  test('loads an existing library into staging', async ({ page }) => {
    await page.goto('/')

    await page.getByRole('button', { name: 'Open editor' }).click()
    await expect(page).toHaveURL(/\/libraries\/edit/)
    await expect(page.getByText('Pick a library to edit')).toBeVisible({ timeout: 60_000 })

    const libraryCards = page.locator('[role="button"][aria-disabled="false"]')
    await expect(libraryCards.first()).toBeVisible({ timeout: 60_000 })

    await Promise.all([
      page.waitForURL(/\/create\/staging/, { timeout: 120_000 }),
      libraryCards.first().click(),
    ])

    await expect(page.getByText('Unified staging')).toBeVisible({ timeout: 60_000 })
    await expect(page.locator('table tbody tr').first()).toBeVisible({ timeout: 60_000 })
  })
})
