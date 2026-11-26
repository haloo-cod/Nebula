import { defineConfig } from '@playwright/test'
import previewConfig from './playwright.rss.config'

// 目录浏览同样检查生产构建，沿用已有的 Chrome 与预览服务配置。
export default defineConfig({
  ...previewConfig,
  testMatch: 'storage.spec.ts',
  outputDir: '.playwright-mcp/storage-results',
})
