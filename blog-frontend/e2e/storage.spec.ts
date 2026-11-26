import { expect, test, type Page } from '@playwright/test'

/** 浏览器测试文件元数据，覆盖 R2 独有文件、本地副本与缺失状态。 */
function file(path: string, overrides: Record<string, unknown> = {}) {
  return {
    path,
    name: path.split('/').pop(),
    title: '',
    file_size: 2048,
    modified_at: '2026-10-20T10:00:00',
    local_exists: true,
    storage_backend: 'local',
    record_kind: null,
    record_id: null,
    r2_key: null,
    r2_url: null,
    url: null,
    manage_url: null,
    ...overrides,
  }
}

/** 使用完整生产页面配合独立接口夹具，不接触开发数据库和真实对象存储。 */
async function prepare(
  page: Page,
  options: { dark?: boolean; delayImages?: Promise<void>; failOnce?: boolean } = {},
) {
  await page.addInitScript(
    ({ dark }) => {
      localStorage.setItem('blog_admin_token', 'storage-browser-fixture-only')
      localStorage.setItem('admin_dark_mode', String(dark))
      localStorage.setItem('blog-theme', dark ? 'dark' : 'light')
    },
    { dark: options.dark ?? false },
  )
  let failed = false
  await page.route('**/api/v1/**', async (route) => {
    const url = new URL(route.request().url())
    const path = url.pathname
    if (path === '/api/v1/auth/me')
      return route.fulfill({
        json: { id: 1, username: 'fixture', is_admin: true, is_active: true },
      })
    if (path === '/api/v1/r2-migration/storage-config')
      return route.fulfill({
        json: { r2_enabled: true, r2_configured: true, default_storage: 'local' },
      })
    if (path === '/api/v1/storage/browse') {
      const root = url.searchParams.get('root') || 'uploads'
      const directory = url.searchParams.get('path') || ''
      const currentPage = Number(url.searchParams.get('page') || 1)
      const pageSize = Number(url.searchParams.get('page_size') || 50)
      if (options.failOnce && !failed && pageSize === 50) {
        failed = true
        return route.fulfill({ status: 503, json: { detail: '目录暂时不可用' } })
      }
      if (options.delayImages && directory === 'images' && pageSize === 50)
        await options.delayImages
      const folders: Record<string, string[]> = {
        'uploads/': ['images', 'files', 'books', 'backgrounds', 'book-archives', 'post-archives'],
        'uploads/images': ['2026'],
        'uploads/images/2026': ['10', '11'],
        'content/': ['posts', 'gallery'],
      }
      const entries: Record<string, ReturnType<typeof file>[]> = {
        'uploads/images/2026/10': [
          file('images/2026/10/本地与R2.png', {
            storage_backend: 'r2',
            record_kind: 'image',
            record_id: 1,
            r2_key: 'images/2026/10/本地与R2.png',
            r2_url: 'https://r2.example.com/images/2026/10/本地与R2.png',
            url: '/uploads/images/2026/10/本地与R2.png',
            manage_url: '/admin/files?view=library&tab=images',
          }),
          file('images/2026/10/未登记.png'),
        ],
        'uploads/images/2026/11': [
          file('images/2026/11/仅R2.png', {
            storage_backend: 'r2',
            local_exists: false,
            record_kind: 'image',
            record_id: 2,
            r2_key: 'images/2026/11/仅R2.png',
            manage_url: '/admin/files?view=library&tab=images',
          }),
        ],
        'uploads/files': Array.from({ length: 51 }, (_, index) =>
          file(`files/${String(index).padStart(2, '0')}.zip`),
        ),
        'uploads/books': [
          file('books/丢失的书.epub', {
            local_exists: false,
            record_kind: 'book',
            record_id: 3,
            manage_url: '/admin/books',
          }),
        ],
        'content/posts': [
          file('posts/中文博文.md', {
            record_kind: 'post',
            record_id: 4,
            title: '中文博文标题',
            manage_url: '/admin/posts',
          }),
        ],
      }
      const items = entries[`${root}/${directory}`] || []
      return route.fulfill({
        json: {
          root,
          path: directory,
          directories: (folders[`${root}/${directory}`] || []).map((name) => ({
            name,
            path: directory ? `${directory}/${name}` : name,
          })),
          items: items.slice((currentPage - 1) * pageSize, currentPage * pageSize),
          total: items.length,
          page: currentPage,
          page_size: pageSize,
          r2_enabled: true,
        },
      })
    }
    if (path === '/api/v1/images')
      return route.fulfill({
        json: {
          items: [
            {
              id: 1,
              filename: 'images/2026/10/本地与R2.png',
              original_name: '本地与R2.png',
              url: '/uploads/images/2026/10/本地与R2.png',
              file_size: 2048,
              width: 100,
              height: 100,
              mime_type: 'image/png',
              created_at: '2026-10-20T10:00:00',
            },
          ],
          total: 1,
        },
      })
    if (path === '/api/v1/analytics/events') return route.fulfill({ status: 204 })
    return route.fulfill({ json: { items: [], total: 0 } })
  })
}

async function openFolder(page: Page, name: string) {
  await page.locator('.storage-subdirectories').getByRole('button', { name, exact: true }).click()
  await expect(page.getByLabel('当前目录')).toContainText(name)
}

for (const dark of [false, true]) {
  test(`${dark ? '暗色' : '亮色'}目录、R2 副本、展开详情和原文件库管理`, async ({ page }) => {
    const errors: string[] = []
    page.on('pageerror', (error) => errors.push(error.message))
    await prepare(page, { dark })
    await page.goto('/admin/files')
    await expect(page.getByLabel('目录树')).toBeVisible()
    await openFolder(page, 'images')
    await openFolder(page, '2026')
    await openFolder(page, '10')
    const row = page
      .locator('.storage-file-table .el-table__body tr')
      .filter({ hasText: '本地与R2.png' })
      .first()
    await expect(row).toContainText('R2')
    await expect(row).toContainText('存在')
    await row.locator('.el-table__expand-icon').click()
    await expect(page.locator('.storage-file-details')).toContainText('images/2026/10/本地与R2.png')
    await expect(page.locator('.storage-file-details')).toContainText('https://r2.example.com/')
    await row.getByRole('button', { name: '管理', exact: true }).click()
    await expect(page.getByRole('tab', { name: '图片', exact: true })).toHaveAttribute(
      'aria-selected',
      'true',
    )
    await expect(page.getByRole('button', { name: '上传图片', exact: true })).toBeVisible()
    await page
      .getByRole('radiogroup', { name: '文件展示方式' })
      .getByText('目录浏览', { exact: true })
      .click()
    await expect(page.getByLabel('当前目录')).toContainText('10')
    await page.getByRole('button', { name: '上一级', exact: true }).click()
    await openFolder(page, '11')
    await expect(page.locator('.storage-file-table')).toContainText('仅R2.png')
    await expect(page.locator('.storage-file-table')).toContainText('无')
    await page.screenshot({
      path: `.playwright-mcp/storage-${dark ? 'dark' : 'light'}.png`,
      animations: 'disabled',
      fullPage: true,
    })
    expect(errors).toEqual([])
  })
}

test('内容目录、本地缺失、分页及手机布局', async ({ page }) => {
  await prepare(page)
  await page.goto('/admin/files')
  await openFolder(page, 'files')
  await expect(page.locator('.storage-directory-footer')).toContainText('51 个文件')
  await page.getByRole('button', { name: 'Go to next page' }).click()
  await expect(page.locator('.storage-file-table')).toContainText('50.zip')
  await page.getByRole('button', { name: '上一级', exact: true }).click()
  await openFolder(page, 'books')
  await expect(page.locator('.storage-file-table')).toContainText('本地缺失')
  await page.getByLabel('目录树').getByText('content · 内容原文件', { exact: true }).click()
  await openFolder(page, 'posts')
  await expect(page.locator('.storage-file-table')).toContainText('中文博文.md')
  await page.setViewportSize({ width: 390, height: 844 })
  await expect(page.getByLabel('目录树')).toBeVisible()
  const fits = await page.evaluate(() => document.documentElement.scrollWidth <= window.innerWidth)
  expect(fits).toBe(true)
  await page.screenshot({
    path: '.playwright-mcp/storage-mobile.png',
    fullPage: true,
    animations: 'disabled',
  })
})

test('较早的目录响应不会覆盖较新的选择，错误可重试', async ({ page }) => {
  let release: () => void = () => {}
  const pending = new Promise<void>((resolve) => {
    release = resolve
  })
  await prepare(page, { delayImages: pending, failOnce: true })
  await page.goto('/admin/files')
  await expect(page.getByRole('alert').filter({ hasText: '目录暂时不可用' })).toBeVisible()
  await page.getByRole('button', { name: '重试', exact: true }).click()
  await openFolder(page, 'images')
  await page.getByLabel('目录树').getByText('files', { exact: true }).click()
  await expect(page.locator('.storage-file-table')).toContainText('00.zip')
  release()
  await expect(page.getByLabel('当前目录')).toContainText('files')
  await expect(page.locator('.storage-file-table')).toContainText('00.zip')
})
