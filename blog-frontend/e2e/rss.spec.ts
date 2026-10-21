import { expect, test, type Page } from '@playwright/test'

/** 浏览器夹具选项；全部请求使用测试数据，不修改开发或生产数据库。 */
interface RssFixtureOptions {
  rssUrl?: string
  failConfig?: boolean
  holdRelatedRequests?: boolean
}

/** 模拟公开数据和管理员保存，使两个页面实际使用同一个配置接口。 */
async function mockRss(page: Page, options: RssFixtureOptions = {}) {
  await page.route('**/__rss-art.svg*', (route) =>
    route.fulfill({
      contentType: 'image/svg+xml',
      headers: { 'Access-Control-Allow-Origin': '*' },
      body: '<svg xmlns="http://www.w3.org/2000/svg" width="1920" height="1080"><path fill="#8caaa7" d="M0 0h1920v1080H0z"/><circle cx="500" cy="300" r="260" fill="#ede5d2"/><path fill="#6c8195" d="M0 750 900 400 1920 900v180H0Z"/></svg>',
    }),
  )
  let rssUrl = options.rssUrl ?? ''
  let defaultUrl = ''
  const saved: Record<string, unknown>[] = []
  const exchange = {
    name: "Starlitn'blog",
    url: 'https://blog.example.com/',
    avatar: '/__rss-art.svg',
    bio: '躺在星夜的草地上，做一个安静的梦。',
    requirements: ['原创内容优先'],
    contact: 'hello@example.com',
  }
  await page.route('**/api/v1/**', async (route) => {
    const request = route.request()
    const url = new URL(request.url())
    const path = url.pathname
    if (path === '/api/v1/backgrounds') {
      return route.fulfill({
        json: {
          total: 1,
          items: [
            {
              id: url.searchParams.get('theme') === 'light' ? 2 : 1,
              url: `${url.origin}/__rss-art.svg`,
              media_type: 'image',
              theme: url.searchParams.get('theme'),
              device: url.searchParams.get('device'),
              sort_order: 0,
              created_at: '2026-10-20T00:00:00',
              source_text: '',
              source_url: '',
            },
          ],
        },
      })
    }
    if (path === '/api/v1/analytics/public-summary') {
      return route.fulfill({
        json: { total_pv: 10, total_uv: 3, today_pv: 2, today_uv: 1, trend: [] },
      })
    }
    if (path === '/api/v1/friends/exchange-info') {
      defaultUrl = `${url.origin}/api/v1/rss.xml`
      if (options.failConfig) return route.fulfill({ status: 503, json: { detail: '配置不可用' } })
      if (request.method() === 'PUT') {
        const payload = request.postDataJSON()
        saved.push(payload)
        rssUrl = payload.rss_url.trim()
      }
      return route.fulfill({ json: { ...exchange, rss_url: rssUrl } })
    }
    if (options.holdRelatedRequests && ['/api/v1/friends', '/api/v1/profile'].includes(path)) {
      // 保持请求未完成，验证 RSS 配置无需等待其他接口。
      return
    }
    if (path === '/api/v1/profile') {
      return route.fulfill({
        json: {
          name: 'Starlit',
          bio: exchange.bio,
          avatar_url: '/__rss-art.svg',
          cover_url: '',
          social_links: [
            { id: 1, label: 'GitHub', icon: 'github', url: 'https://example.com', sort_order: 0 },
          ],
        },
      })
    }
    if (path === '/api/v1/auth/me') {
      return route.fulfill({
        json: {
          id: 1,
          username: 'browser-admin',
          is_admin: true,
          is_active: true,
          email_verified: true,
        },
      })
    }
    if (path === '/api/v1/content-stats') {
      return route.fulfill({ json: { posts: 1, moments: 0, gallery_projects: 0, active_days: 1 } })
    }
    if (path === '/api/v1/analytics/events') return route.fulfill({ status: 204 })
    return route.fulfill({ json: { items: [], total: 0 } })
  })
  return { defaultUrl: () => defaultUrl, saved }
}

/** 使用现有主题设置并跳过首页文字动画，稳定检查实际布局。 */
async function prepare(page: Page, theme = 'dark', glass = false) {
  await page.addInitScript(
    ({ theme, glass }) => {
      localStorage.setItem('blog-theme', theme)
      localStorage.setItem('blog-liquid-glass-enabled', String(glass))
      localStorage.setItem('blog_admin_token', 'browser-fixture-only')
      history.replaceState({ ...history.state, showContent: true }, '')
    },
    { theme, glass },
  )
}

for (const theme of ['dark', 'light']) {
  for (const glass of [false, true]) {
    test(`${theme} / ${glass ? '液态玻璃' : '毛玻璃'}：默认 RSS 和首页图标一致`, async ({
      page,
    }) => {
      const errors: string[] = []
      page.on('pageerror', (error) => errors.push(error.message))
      await prepare(page, theme, glass)
      const fixture = await mockRss(page)
      await page.goto('/friends')
      const link = page.locator('.exchange-site-rss a')
      await expect(link).toBeVisible()
      await expect(link).toHaveAttribute('href', fixture.defaultUrl())
      await expect(link).toHaveText(fixture.defaultUrl())
      await page.context().route('**/api/v1/rss.xml', (route) =>
        route.fulfill({
          contentType: 'application/rss+xml',
          body: '<rss version="2.0"><channel><title>Browser RSS</title><link>https://example.com/</link><description>测试订阅</description></channel></rss>',
        }),
      )
      await link.scrollIntoViewIfNeeded()
      if (glass)
        await expect(page.locator('.exchange-glass .liquid-glass-canvas')).toHaveClass(/--visible/)
      else await expect(page.locator('.exchange-card-fallback')).toBeVisible()
      await page.screenshot({
        path: `.playwright-mcp/rss-friends-${theme}-${glass ? 'liquid' : 'frosted'}.png`,
      })
      const popupPromise = page.waitForEvent('popup')
      await link.click()
      const popup = await popupPromise
      await expect(popup).toHaveURL(fixture.defaultUrl())
      await popup.close()
      const staticHtml = await (await page.request.get('/')).text()
      expect(staticHtml).toMatch(/<link[^>]+rel="alternate"[^>]+type="application\/rss\+xml"/)
      await expect(page.locator('head link[type="application/rss+xml"]')).toHaveAttribute(
        'href',
        /\/api\/v1\/rss\.xml$/,
      )
      await page.goto('/')
      const homeLink = page.getByRole('link', { name: 'RSS 订阅', exact: true })
      await expect(homeLink).toBeVisible()
      await expect(homeLink).toHaveAttribute('href', fixture.defaultUrl())
      await expect(homeLink).toHaveAttribute('target', '_blank')
      await expect(homeLink.locator('.svg-icon')).not.toHaveCSS('mask-image', 'none')
      expect(errors).toEqual([])
    })
  }
}

test('后台保存、刷新与清空 RSS 地址，两处入口同步且保留其余交换信息', async ({ page }) => {
  await prepare(page)
  const fixture = await mockRss(page)
  const custom = 'https://feeds.example.com/rss.xml?a=1&b=2'
  for (const value of [custom, '']) {
    await page.goto('/admin/friends')
    await expect(page.getByPlaceholder('展示在交换友链区域的站点名称')).toHaveValue("Starlitn'blog")
    await page.getByPlaceholder('留空自动使用本站 RSS').fill(value)
    await page.getByRole('button', { name: '保存设置', exact: true }).click()
    await expect(page.getByText('交换友链信息已保存', { exact: true })).toBeVisible()
    expect(fixture.saved.at(-1)).toMatchObject({
      name: "Starlitn'blog",
      contact: 'hello@example.com',
      requirements: ['原创内容优先'],
      rss_url: value,
    })
    await page.reload()
    await expect(page.getByPlaceholder('留空自动使用本站 RSS')).toHaveValue(value)
    const expected = value || fixture.defaultUrl()
    await expect(page.locator('.rss-address-hint a')).toHaveAttribute('href', expected)
    await page.goto('/friends')
    await expect(page.locator('.exchange-site-rss a')).toHaveAttribute('href', expected)
    await page.goto('/')
    await expect(page.getByRole('link', { name: 'RSS 订阅', exact: true })).toHaveAttribute(
      'href',
      expected,
    )
  }
})

for (const glass of [false, true]) {
  test(`移动端长链接换行 / ${glass ? '液态玻璃' : '毛玻璃'}`, async ({ page }) => {
    await prepare(page, 'light', glass)
    await page.setViewportSize({ width: 390, height: 844 })
    const custom = 'https://feeds.example.com/' + 'long-path-'.repeat(25) + '/rss.xml'
    await mockRss(page, { rssUrl: custom })
    await page.goto('/friends')
    const link = page.locator('.exchange-site-rss a')
    await expect(link).toHaveText(custom)
    await link.scrollIntoViewIfNeeded()
    expect(await page.evaluate(() => document.documentElement.scrollWidth)).toBeLessThanOrEqual(390)
    const box = await link.boundingBox()
    expect(box?.height).toBeGreaterThan(30)
    await page.screenshot({
      path: `.playwright-mcp/rss-mobile-${glass ? 'liquid' : 'frosted'}.png`,
    })
  })
}

test('其他接口尚未完成时 RSS 配置仍能独立显示', async ({ page }) => {
  await prepare(page)
  await mockRss(page, { holdRelatedRequests: true })
  await page.goto('/friends', { waitUntil: 'domcontentloaded' })
  await expect(page.locator('.exchange-site-rss a')).toBeVisible()
  await page.goto('/', { waitUntil: 'domcontentloaded' })
  await expect(page.getByRole('link', { name: 'RSS 订阅', exact: true })).toBeVisible()
})

test('配置加载失败时其他内容可用，RSS 入口保持隐藏', async ({ page }) => {
  await prepare(page)
  await mockRss(page, { failConfig: true })
  await page.goto('/friends')
  await expect(page.getByRole('heading', { name: '交换友链', exact: true })).toBeVisible()
  await expect(page.locator('.exchange-site-rss')).toHaveCount(0)
  await page.goto('/')
  await expect(page.locator('.hp-name')).toHaveText('Starlit')
  await expect(page.locator('.hp-social a[title="GitHub"]')).toBeVisible()
  await expect(page.getByRole('link', { name: 'RSS 订阅', exact: true })).toHaveCount(0)
})

for (const glass of [false, true]) {
  test(`${glass ? '液态玻璃' : '毛玻璃'}：本站信息标签与逐行复制`, async ({ page, context }) => {
    await context.grantPermissions(['clipboard-read', 'clipboard-write'])
    await prepare(page, 'light', glass)
    const custom = glass ? 'https://feeds.example.com/rss?a=1&b=2' : ''
    const fixture = await mockRss(page, { rssUrl: custom })
    await page.goto('/friends')
    await expect(page.locator('.exchange-site-url')).toContainText('站点：')
    await expect(page.locator('.exchange-site-bio')).toContainText('简介：')
    await expect(page.locator('.exchange-site-rss a')).toBeVisible()
    const rows = [
      ['复制站点名称', "Starlitn'blog"],
      ['复制站点地址', 'https://blog.example.com/'],
      ['复制简介', '躺在星夜的草地上，做一个安静的梦。'],
      ['复制头像地址', '/__rss-art.svg'],
      ['复制RSS 地址', custom || fixture.defaultUrl()],
    ]
    for (const [label, value] of rows) {
      await page.getByRole('button', { name: label, exact: true }).click()
      await expect.poll(() => page.evaluate(() => navigator.clipboard.readText())).toBe(value)
      await expect(page.getByRole('button', { name: label, exact: true })).toHaveAttribute(
        'title',
        '已复制',
      )
    }
    await page.evaluate(() => {
      Object.defineProperty(navigator.clipboard, 'writeText', {
        configurable: true,
        value: async () => {
          throw new Error('模拟剪贴板权限拒绝')
        },
      })
    })
    await page.getByRole('button', { name: '复制简介', exact: true }).click()
    await expect(page.getByRole('alert')).toContainText('复制失败')
    await expect(page.locator('.exchange-site-bio')).toContainText('躺在星夜的草地上')
  })
}

for (const glass of [false, true]) {
  test(`复制等待期间按钮保持稳定 / ${glass ? '液态玻璃' : '毛玻璃'}`, async ({ page, context }) => {
    await context.grantPermissions(['clipboard-read', 'clipboard-write'])
    await prepare(page, 'light', glass)
    await mockRss(page)
    await page.goto('/friends')
    await expect(page.locator('.exchange-site-rss a')).toBeVisible()

    let finishWrite = () => {}
    const writePending = new Promise<void>((resolve) => {
      finishWrite = resolve
    })
    await page.route('**/__clipboard-write-wait', async (route) => {
      await writePending
      await route.fulfill({ status: 204 })
    })
    await page.evaluate(() => {
      const writeText = navigator.clipboard.writeText.bind(navigator.clipboard)
      Object.defineProperty(navigator.clipboard, 'writeText', {
        configurable: true,
        value: async (value: string) => {
          await fetch('/__clipboard-write-wait')
          await writeText(value)
        },
      })
    })
    const buttons = page.locator('.exchange-copy-button')
    const before = await buttons.evaluateAll((nodes) =>
      nodes.map((node) => getComputedStyle(node).opacity),
    )
    const button = page.getByRole('button', { name: '复制站点名称', exact: true })
    try {
      await button.click()
      const pending = await buttons.evaluateAll((nodes) =>
        nodes.map((node) => getComputedStyle(node).opacity),
      )
      expect(pending).toEqual(before)
      await expect(button).toBeEnabled()
    } finally {
      finishWrite()
    }
    await expect(button).toHaveAttribute('title', '已复制')
    await expect
      .poll(() => page.evaluate(() => navigator.clipboard.readText()))
      .toBe("Starlitn'blog")
  })
}
