import { expect, Page, test } from '@playwright/test'

test.describe('Unified staging filters', () => {
  test('react to user input', async ({ page }) => {
    await startStagingWithZotero(page)
    await waitForTableRows(page, 2)

    const tableRows = page.locator('table tbody tr')
    const sidebar = page.locator('aside')
    const yearFromInput = page.getByPlaceholder('From')
    
    // Test year filter
    await yearFromInput.fill('2100')
    await yearFromInput.blur()
    await expect(page.getByText('No papers match your current filters')).toBeVisible({ timeout: 20_000 })

    // Clear filters and wait for results
    await sidebar.getByRole('button', { name: 'Clear filters' }).click()
    await waitForTableRows(page, 1)

    const sourceCheckboxes = sidebar.locator('label:has(input[type="checkbox"])')
    const sourceCount = await sourceCheckboxes.count()
    
    // Check all unchecked checkboxes
    for (let i = 0; i < sourceCount; i += 1) {
      const label = sourceCheckboxes.nth(i)
      const input = label.locator('input[type="checkbox"]')
      
      if (!(await input.isChecked())) {
        await label.click()
        await expect(input).toBeChecked({ timeout: 5_000 })
      }
    }

    // Wait for table to stabilize after checking all boxes
    await page.waitForTimeout(1000)

    const firstSourceLabel = sourceCheckboxes.first()
    const firstSourceInput = firstSourceLabel.locator('input[type="checkbox"]')
    const firstSourceText = (await firstSourceLabel.textContent())?.trim() || ''
    
    // Uncheck the first source
    await firstSourceLabel.click()
    await expect(firstSourceInput).not.toBeChecked({ timeout: 5_000 })
    
    // Wait for filter to apply - either no matching rows or the filtered rows appear
    if (firstSourceText) {
      await expect(tableRows.filter({ hasText: firstSourceText })).toHaveCount(0, { timeout: 20_000 })
    }
    
    // Re-check the first source to restore the original list, then reset everything
    await firstSourceLabel.click()
    await expect(firstSourceInput).toBeChecked({ timeout: 5_000 })
    await sidebar.getByRole('button', { name: 'Clear filters' }).click()
    await waitForTableRows(page, 1)
  })
})

async function startStagingWithZotero(page: Page) {
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

  const count = await collectionRows.count()
  expect(count).toBeGreaterThanOrEqual(1)
  const toImport = Math.min(2, count)
  for (let i = 0; i < toImport; i += 1) {
    await collectionRows.nth(i).locator('input[type="checkbox"]').check()
  }

  await zoteroModal.getByRole('button', { name: 'Import selected' }).click()
  await zoteroModal.waitFor({ state: 'hidden' })
  await waitForTableRows(page)
}

async function waitForTableRows(page: Page, minRows = 1, timeout = 60_000) {
  await page.waitForFunction(
    (expected: number) => document.querySelectorAll('table tbody tr').length >= expected,
    minRows,
    { timeout }
  )
}
