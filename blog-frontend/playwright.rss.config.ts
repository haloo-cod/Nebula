import { defineConfig } from '@playwright/test'
import baseConfig from './playwright.config'

// RSS 同时验证构建时写入的静态发现标签，使用生产预览避开开发依赖重载。
export default defineConfig({
  ...baseConfig,
  testMatch: 'rss.spec.ts',
  outputDir: '.playwright-mcp/rss-results',
  use: { ...baseConfig.use, baseURL: 'http://127.0.0.1:4173' },
  webServer: {
    command: 'pnpm preview --host 127.0.0.1 --port 4173 --strictPort',
    url: 'http://127.0.0.1:4173',
    reuseExistingServer: false,
  },
})
