import { defineConfig, devices } from '@playwright/test'

const PORT = process.env.VITE_DEV_SERVER_PORT || '5173'
const HOST = process.env.VITE_DEV_SERVER_HOST || 'localhost'
const BASE_URL = `http://${HOST}:${PORT}`
const API_URL = process.env.VITE_API_URL || 'http://localhost:8000'

export default defineConfig({
  testDir: './tests',
  fullyParallel: false,
  workers: 1,
  timeout: 5 * 60 * 1000,
  expect: {
    timeout: 20_000,
  },
  retries: process.env.CI ? 1 : 0,
  reporter: process.env.CI ? 'github' : 'list',
  use: {
    baseURL: process.env.PLAYWRIGHT_BASE_URL || BASE_URL,
    trace: process.env.CI ? 'retain-on-failure' : 'on-first-retry',
    screenshot: 'only-on-failure',
    video: 'retain-on-failure',
    viewport: { width: 1440, height: 900 },
  },
  projects: [
    {
      name: 'chromium',
      use: { ...devices['Desktop Chrome'] },
    },
  ],
  webServer: {
    command: `npm run dev -- --host ${HOST} --port ${PORT} --strictPort`,
    url: BASE_URL,
    reuseExistingServer: !process.env.CI,
    stdout: 'pipe',
    stderr: 'pipe',
    env: {
      VITE_API_URL: API_URL,
    },
    timeout: 120 * 1000,
  },
})
