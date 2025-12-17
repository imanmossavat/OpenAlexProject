import { expect, test } from '@playwright/test'

test.describe('Crawler rerun actions', () => {
  test('loads an experiment for editing', async ({ page }) => {
    await page.goto('/')
    await page.getByText('Other workflows…').click()
    await expect(page).toHaveURL(/\/workflow\/other/, { timeout: 60_000 })
    await page.getByRole('button', { name: 'Browse experiments' }).click()

    await expect(page).toHaveURL(/\/crawler\/reruns/, { timeout: 60_000 })
    const experimentCard = page.locator('[role="button"]').first()
    await expect(experimentCard).toBeVisible({ timeout: 60_000 })
    await experimentCard.click()
    await page.getByRole('button', { name: 'Re-run with edits' }).click()

    await expect(page).toHaveURL(/\/crawler\/keywords/, { timeout: 120_000 })
    await expect(page.getByText('Define your keyword filters')).toBeVisible()
  })

  test('starts rerun immediately', async ({ page }) => {
    await page.goto('/')
    await page.getByText('Other workflows…').click()
    await expect(page).toHaveURL(/\/workflow\/other/, { timeout: 60_000 })
    await page.getByRole('button', { name: 'Browse experiments' }).click()

    await expect(page).toHaveURL(/\/crawler\/reruns/, { timeout: 60_000 })
    const experimentCard = page.locator('[role="button"]').first()
    await expect(experimentCard).toBeVisible({ timeout: 60_000 })
    await experimentCard.click()
    await page.getByRole('button', { name: 'Re-run now' }).click()

    await expect(page).toHaveURL(/\/crawler\/results/, { timeout: 120_000 })
    await expect(page.getByText('Crawler results')).toBeVisible()
  })
})
