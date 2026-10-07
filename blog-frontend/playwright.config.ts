import { defineConfig } from '@playwright/test'

export default defineConfig({
  testDir: './e2e',
  outputDir: '.playwright-mcp/test-results',
  workers: 1,
  use: {
    baseURL: 'http://127.0.0.1:5173',
    channel: 'chrome',
    viewport: { width: 1920, height: 1080 },
    trace: 'retain-on-failure',
  },
  webServer: {
    command: 'pnpm dev --host 127.0.0.1',
    url: 'http://127.0.0.1:5173',
    reuseExistingServer: true,
  },
})
