import { test, expect, Page } from '@playwright/test'

test.describe('Library creation via Zotero flow', () => {
  test('imports Zotero seeds, filters, and creates a library', async ({ page }) => {
    const libraryName = `E2E Zotero Library ${Date.now()}`

    await page.goto('/')

    await page.getByRole('button', { name: 'Start' }).click()
    await expect(page).toHaveURL(/\/create\/library-start/)

    await page.getByRole('button', { name: 'Start staging seeds' }).click()
    await expect(page).toHaveURL(/\/create\/staging/)

    await expect(page.getByText('Bring in papers to get started')).toBeVisible()
    await page.getByRole('button', { name: 'Zotero collections' }).click()

    const zoteroModal = page.getByRole('dialog', { name: 'Import from Zotero' })
    const collectionRows = zoteroModal.locator('label:has(input[type="checkbox"])')
    await expect(collectionRows.first()).toBeVisible({ timeout: 60_000 })

    const collectionCount = await collectionRows.count()
    expect(collectionCount).toBeGreaterThanOrEqual(2)
    for (let i = 0; i < Math.min(2, collectionCount); i += 1) {
      await collectionRows.nth(i).locator('input[type="checkbox"]').check()
    }

    await zoteroModal.getByRole('button', { name: 'Import selected' }).click()
    await zoteroModal.waitFor({ state: 'hidden' })

    await waitForTableRows(page)

    const retractionsButton = page.getByRole('button', { name: 'Check retractions' })
    await retractionsButton.click()
    await expect(page.getByText(/Last checked/i)).toBeVisible({ timeout: 120_000 })

    const yearFromInput = page.getByPlaceholder('From')
    await yearFromInput.fill('2021')
    await yearFromInput.blur()
    await waitForTableRows(page)

    await page.getByRole('button', { name: 'Select visible' }).click()

    const nextButton = page
      .locator('header')
      .filter({ hasText: 'Unified staging' })
      .getByRole('button', { name: 'Next' })
    await expect(nextButton).toBeEnabled({ timeout: 30_000 })
    const matchResponsePromise = page.waitForResponse((response) => {
      const url = response.url()
      return (
        response.request().method() === 'POST' &&
        url.includes('/api/v1/seeds/session') &&
        url.endsWith('/staging/match')
      )
    }, { timeout: 180_000 })
    await nextButton.click()
    const matchResponse = await matchResponsePromise
    let matchBody: unknown
    try {
      matchBody = await matchResponse.json()
    } catch {
      matchBody = { detail: 'Failed to parse response body' }
    }
    expect(
      matchResponse.ok(),
      `Matching request failed: ${matchResponse.status()} ${matchResponse.statusText()} ${JSON.stringify(matchBody)}`
    ).toBeTruthy()
    await page.waitForURL(/\/create\/staging\/matched/, { timeout: 120_000 })
    await expect(page.getByText('Review matched seed papers')).toBeVisible({ timeout: 120_000 })

    const confirmButton = page.getByRole('button', { name: 'Confirm & continue' })
    await expect(confirmButton).toBeEnabled({ timeout: 120_000 })
    await confirmButton.click()

    await expect(page).toHaveURL(/\/create\/details/)

    await page.getByLabel('Library Name').fill(libraryName)
    await page
      .locator('textarea#description')
      .fill('Automated test library generated via Playwright end-to-end scenario.')

    await page.getByRole('button', { name: 'Continue' }).click()
    await expect(page).toHaveURL(/\/create\/review/)

    const createButton = page.getByRole('button', { name: 'Create Library' })
    await expect(createButton).toBeEnabled({ timeout: 60_000 })
    await createButton.click()

    await expect(page).toHaveURL(/\/$/)
    await expect(page.getByText('How would you like to work today?')).toBeVisible()
  })
})

async function waitForTableRows(page: Page, minRows = 1, timeout = 60_000) {
  await page.waitForFunction(
    (expected: number) => document.querySelectorAll('table tbody tr').length >= expected,
    minRows,
    { timeout }
  )
}
