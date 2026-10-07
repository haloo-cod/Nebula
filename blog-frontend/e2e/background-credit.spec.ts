import { expect, test, type Page } from '@playwright/test'

// 全部媒体和来源都是浏览器测试夹具，不写入开发或生产数据库。
const artwork = `<svg xmlns="http://www.w3.org/2000/svg" width="1920" height="1080"><defs><linearGradient id="bg" x2="1" y2="1"><stop stop-color="#a8bbb7"/><stop offset="1" stop-color="#5e7585"/></linearGradient><pattern id="grid" width="100" height="100" patternUnits="userSpaceOnUse"><path d="M100 0H0V100" fill="none" stroke="#e6e3ce" opacity=".25"/></pattern></defs><path fill="url(#bg)" d="M0 0h1920v1080H0z"/><circle cx="340" cy="330" r="180" fill="#e9dcc4" opacity=".6"/><path fill="url(#grid)" d="M0 0h1920v1080H0z"/></svg>`

/** 模拟背景接口与媒体，使测试不依赖私有媒体资源。 */
async function mockBackgrounds(
  page: Page,
  text = '演示来源 · 画师与作品名称',
  url = 'https://example.com/artwork',
) {
  await page.route('**/__credit-artwork.svg*', (route) =>
    route.fulfill({ contentType: 'image/svg+xml', body: artwork }),
  )
  await page.route('**/api/v1/backgrounds?*', (route) => {
    const params = new URL(route.request().url()).searchParams
    return route.fulfill({
      json: {
        total: 1,
        items: [
          {
            id: params.get('theme') === 'light' ? 2 : 1,
            url: 'http://127.0.0.1:5173/__credit-artwork.svg',
            media_type: 'image',
            theme: params.get('theme'),
            device: params.get('device'),
            sort_order: 0,
            created_at: '2026-10-07T00:00:00',
            source_text: text,
            source_url: url,
          },
        ],
      },
    })
  })
}

for (const theme of ['dark', 'light']) {
  for (const glass of [false, true]) {
    test(`${theme} / ${glass ? '液态玻璃' : '毛玻璃'}：布局、拖动与链接`, async ({ page }) => {
      const errors: string[] = []
      page.on('pageerror', (error) => errors.push(error.message))
      await page.addInitScript(
        ({ theme, glass }) => {
          localStorage.setItem('blog-theme', theme)
          localStorage.setItem('blog-liquid-glass-enabled', String(glass))
        },
        { theme, glass },
      )
      await mockBackgrounds(page)
      await page.goto('/moments')
      const card = page.locator('.background-credit-card')
      await expect(card).toBeVisible()
      await expect(card).toHaveAttribute('href', 'https://example.com/artwork')
      await expect(page.locator('.background-credit-text')).toHaveText('演示来源 · 画师与作品名称')
      const dimensions = await card.boundingBox()
      expect(dimensions?.width).toBe(240)
      expect(dimensions?.height).toBe(150)
      if (glass)
        await expect(page.locator('.background-credit .liquid-glass-canvas')).toHaveClass(
          /--visible/,
        )
      else await expect(page.locator('.background-credit .panel-fallback-glass')).toBeVisible()
      const anchor = await page.locator('.background-credit').boundingBox()
      const nav = await page.locator('[data-background-credit-navbar]').boundingBox()
      expect(anchor?.y).toBe((nav?.y ?? 0) + (nav?.height ?? 0))
      await expect(page.locator('[data-background-credit-navbar]')).toHaveCSS('box-shadow', 'none')
      await expect(page.locator('.background-credit-eyelet, .credit-rope-knot')).toHaveCount(0)

      // 防止外链导航，仅记录这次真实浏览器 click 是否被拖动处理器取消。
      await card.evaluate((element) => {
        element.addEventListener('click', (event) => {
          element.setAttribute('data-click-cancelled', String(event.defaultPrevented))
          event.preventDefault()
        })
      })
      const centerX = (dimensions?.x ?? 0) + 120
      const centerY = (dimensions?.y ?? 0) + 75
      await page.mouse.move(centerX, centerY)
      await page.mouse.down()
      await page.mouse.move(centerX + 400, centerY, { steps: 16 })
      await expect(page.locator('.background-credit-swing')).toHaveClass(/is-dragging/)
      const ropeCore = page.locator('.credit-rope-core')
      await expect(ropeCore).toHaveCSS(
        'stroke',
        theme === 'light' ? 'rgb(255, 255, 255)' : 'rgb(8, 9, 10)',
      )
      const ropeLength = await ropeCore.evaluate((element) =>
        element instanceof SVGPathElement ? element.getTotalLength() : 0,
      )
      expect(ropeLength).toBeCloseTo(100, 2)
      const draggedAngle = await page
        .locator('.background-credit')
        .evaluate((element) =>
          Math.abs(parseFloat(getComputedStyle(element).getPropertyValue('--credit-angle'))),
        )
      expect(draggedAngle).toBeCloseTo((40 * Math.PI) / 180, 5)
      const draggedBox = await card.boundingBox()
      expect(draggedBox?.x).toBeGreaterThanOrEqual(16)
      expect((draggedBox?.x ?? 0) + (draggedBox?.width ?? 0)).toBeLessThanOrEqual(
        (anchor?.x ?? 0) * 2 - 16,
      )
      if (glass && theme === 'dark') {
        await page.screenshot({ path: '.playwright-mcp/background-credit-dragged.png' })
      }
      await page.mouse.up()
      await expect(card).toHaveAttribute('data-click-cancelled', 'true')
      await expect
        .poll(
          async () =>
            page
              .locator('.background-credit')
              .evaluate((element) =>
                Math.abs(parseFloat(getComputedStyle(element).getPropertyValue('--credit-angle'))),
              ),
          { timeout: 10000 },
        )
        .toBeLessThan(0.002)
      await expect
        .poll(
          () =>
            ropeCore.evaluate((element) =>
              [...(element.getAttribute('d') ?? '').matchAll(/[ML](-?[\d.]+),/g)].every(
                (match) => Number(match[1]) === 0,
              ),
            ),
          { timeout: 10000 },
        )
        .toBe(true)
      await card.click()
      await expect(card).toHaveAttribute('data-click-cancelled', 'false')
      await card.focus()
      await page.keyboard.press('Enter')
      await expect(card).toHaveAttribute('data-click-cancelled', 'false')

      await card.evaluate((element) => {
        if (element instanceof HTMLElement) element.blur()
      })
      await page.screenshot({
        path: `.playwright-mcp/background-credit-rope-${theme}.png`,
        clip: { x: (anchor?.x ?? 312) - 170, y: (anchor?.y ?? 63) - 14, width: 340, height: 280 },
      })
      await page.screenshot({
        path: `.playwright-mcp/background-credit-${theme}-${glass ? 'liquid' : 'frosted'}.png`,
      })
      await page.setViewportSize({ width: 1920, height: 700 })
      const beforeScroll = await card.boundingBox()
      await page.evaluate(() => window.scrollTo(0, 300))
      expect((await card.boundingBox())?.y).toBeCloseTo(beforeScroll?.y ?? 0, 0)
      await page.setViewportSize({ width: 1200, height: 900 })
      await expect.poll(async () => (await card.boundingBox())?.width).toBeLessThan(240)
      await page.setViewportSize({ width: 1000, height: 900 })
      await expect(card).toHaveCount(0)
      await page.setViewportSize({ width: 390, height: 844 })
      await expect(card).toHaveCount(0)
      expect(errors).toEqual([])
    })
  }
}

test('空来源隐藏、无链接只显示文字、减少动态效果取消释放惯性', async ({ page }) => {
  await page.emulateMedia({ reducedMotion: 'reduce' })
  await mockBackgrounds(page, '仅显示画师', '')
  await page.goto('/moments')
  const card = page.locator('.background-credit-card')
  await expect(card).toBeVisible()
  await expect(card).not.toHaveAttribute('href')
  const box = await card.boundingBox()
  await page.mouse.move((box?.x ?? 0) + 120, (box?.y ?? 0) + 75)
  await page.mouse.down()
  await page.mouse.move((box?.x ?? 0) + 200, (box?.y ?? 0) + 75, { steps: 4 })
  await page.mouse.up()
  await expect(page.locator('.background-credit')).toHaveCSS('--credit-angle', '0rad')
  await page.unroute('**/api/v1/backgrounds?*')
  await mockBackgrounds(page, '', '')
  await page.reload()
  await expect(card).toHaveCount(0)
})

test('首页位置与路由切换按真实内容边界更新，后台隐藏', async ({ page }) => {
  await mockBackgrounds(page)
  await page.goto('/')
  await expect(page.locator('.home-panels')).toBeVisible({ timeout: 20000 })
  const anchorX = () =>
    page.locator('.background-credit').evaluate((element) => element.getBoundingClientRect().left)
  await expect.poll(anchorX).toBeCloseTo(205, 0)
  await expect(page.locator('.background-credit .liquid-glass-canvas')).toHaveClass(/--visible/)
  await page.screenshot({ path: '.playwright-mcp/background-credit-home.png' })
  await page.getByRole('link', { name: '关于', exact: true }).click()
  await expect(page.locator('.about-glass')).toBeVisible()
  await expect.poll(anchorX).toBeCloseTo((1920 - 52 * 16) / 4, 0)
  await page.goto('/admin/login')
  await expect(page.locator('.background-credit')).toHaveCount(0)
})

test('视频背景保持来源并完成液态玻璃纹理渲染', async ({ page }) => {
  await page.goto('/')
  // 在浏览器中生成短视频，避免读取生产媒体或提交二进制测试文件。
  const videoData = await page.evaluate(async () => {
    const canvas = document.createElement('canvas')
    canvas.width = 320
    canvas.height = 180
    const ctx = canvas.getContext('2d')!
    ctx.fillStyle = '#58777a'
    ctx.fillRect(0, 0, 320, 180)
    ctx.fillStyle = '#d9c9a6'
    ctx.fillRect(0, 40, 120, 80)
    const stream = canvas.captureStream(10)
    const recorder = new MediaRecorder(stream, { mimeType: 'video/webm' })
    const chunks: Blob[] = []
    recorder.ondataavailable = (event) => chunks.push(event.data)
    const data = new Promise<string>((resolve) => {
      recorder.onstop = () => {
        stream.getTracks().forEach((track) => track.stop())
        const reader = new FileReader()
        reader.onload = () => resolve(String(reader.result).split(',')[1])
        reader.readAsDataURL(new Blob(chunks, { type: 'video/webm' }))
      }
    })
    recorder.start()
    let frame = 0
    const timer = setInterval(() => {
      ctx.fillStyle = frame++ % 2 ? '#d9c9a6' : '#c0bca2'
      ctx.fillRect(0, 40, 120, 80)
    }, 50)
    await new Promise((resolve) => setTimeout(resolve, 800))
    clearInterval(timer)
    recorder.stop()
    return data
  })
  await page.route('**/__credit-video.webm*', (route) =>
    route.fulfill({
      contentType: 'video/webm',
      body: Buffer.from(videoData, 'base64'),
    }),
  )
  await page.route('**/api/v1/backgrounds?*', (route) =>
    route.fulfill({
      json: {
        total: 1,
        items: [
          {
            id: 15,
            url: 'http://127.0.0.1:5173/__credit-video.webm',
            media_type: 'video',
            mime_type: 'video/webm',
            theme: 'dark',
            device: 'desktop',
            sort_order: 0,
            created_at: '',
            source_text: '视频背景来源',
            source_url: 'https://example.com/video',
          },
        ],
      },
    }),
  )
  await page.goto('/moments')
  await expect(page.locator('.background-credit-text')).toHaveText('视频背景来源')
  await expect(page.locator('.background-credit .liquid-glass-canvas')).toHaveClass(/--visible/)
  await expect
    .poll(() =>
      page
        .locator('.bg-video')
        .evaluate((element) => element instanceof HTMLVideoElement && element.readyState >= 2),
    )
    .toBe(true)
})

test('后台来源表单编辑、校验、清空和排序同步', async ({ page }) => {
  const mediaUrl = 'http://127.0.0.1:5173/__credit-artwork.svg'
  const rows = [7, 8].map((id, index) => ({
    id,
    url: mediaUrl,
    theme: 'dark',
    device: 'desktop',
    media_type: 'image',
    sort_order: index,
    created_at: '2026-10-07T00:00:00',
    source_text: `原始来源${id}`,
    source_url: '',
  }))
  const patches: unknown[] = []
  const creations: Array<{ image_id: number; source_text: string; source_url: string }> = []
  await page.addInitScript(() => {
    localStorage.setItem('blog_admin_token', 'browser-test-fixture')
    localStorage.setItem('blog-dark-bg-id', '7')
  })
  await page.route('**/__credit-artwork.svg*', (route) =>
    route.fulfill({ contentType: 'image/svg+xml', body: artwork }),
  )
  await page.route('**/api/v1/auth/me', (route) =>
    route.fulfill({
      json: {
        id: 1,
        username: 'admin',
        is_admin: true,
        email: null,
        display_name: '测试管理员',
        avatar_url: '',
        email_verified: false,
      },
    }),
  )
  await page.route('**/api/v1/r2-migration/storage-config', (route) =>
    route.fulfill({ json: { r2_enabled: false } }),
  )
  await page.route('**/api/v1/files?*', (route) => route.fulfill({ json: { items: [], total: 0 } }))
  await page.route('**/api/v1/images?*', (route) =>
    route.fulfill({
      json: {
        total: 2,
        items: [14, 15].map((id) => ({
          id,
          original_name: `测试图片${id}`,
          url: mediaUrl,
          file_size: 10,
          width: 1920,
          height: 1080,
          mime_type: 'image/svg+xml',
          created_at: '',
        })),
      },
    }),
  )
  await page.route('**/api/v1/backgrounds**', async (route) => {
    const method = route.request().method()
    const url = new URL(route.request().url())
    if (method === 'POST') {
      const payload = route.request().postDataJSON()
      creations.push(payload)
      const row = { ...rows[0], ...payload, id: 20 + creations.length, url: mediaUrl }
      rows.push(row)
      return route.fulfill({ status: 201, json: row })
    }
    if (method === 'PATCH') {
      const payload = route.request().postDataJSON()
      patches.push(payload)
      const row = rows.find((item) => item.id === Number(url.pathname.split('/').at(-2)))!
      Object.assign(row, payload)
      return route.fulfill({ json: row })
    }
    if (method === 'PUT') {
      const { ids } = route.request().postDataJSON()
      rows.sort((a, b) => ids.indexOf(a.id) - ids.indexOf(b.id))
      rows.forEach((row, index) => {
        row.sort_order = index
      })
      return route.fulfill({ status: 204 })
    }
    const selected = rows.filter(
      (row) =>
        (!url.searchParams.get('theme') || row.theme === url.searchParams.get('theme')) &&
        (!url.searchParams.get('device') || row.device === url.searchParams.get('device')),
    )
    return route.fulfill({ json: { items: selected, total: selected.length } })
  })
  await page.goto('/admin/backgrounds')
  await expect(page.locator('.bg-item')).toHaveCount(2)
  await page.locator('.bg-item').first().getByRole('button', { name: '来源', exact: true }).click()
  const dialog = page.getByRole('dialog', { name: '编辑背景来源' })
  await dialog.getByPlaceholder('例如：画师名字 · 作品名称').fill('更新来源')
  await dialog.getByPlaceholder('https://…（点击来源牌后打开）').fill('javascript:alert(1)')
  await dialog.getByRole('button', { name: '保存', exact: true }).click()
  await expect(dialog.getByText('来源链接必须是完整的 HTTP 或 HTTPS 地址')).toBeVisible()
  expect(patches).toHaveLength(0)
  await dialog.getByPlaceholder('https://…（点击来源牌后打开）').fill('https://example.com/work')
  await dialog.getByRole('button', { name: '保存', exact: true }).click()
  await expect(dialog).not.toBeVisible()
  expect(patches).toEqual([{ source_text: '更新来源', source_url: 'https://example.com/work' }])
  await page.locator('.bg-item').nth(1).getByRole('button', { name: '来源', exact: true }).click()
  await dialog.getByPlaceholder('例如：画师名字 · 作品名称').fill('')
  await dialog.getByRole('button', { name: '保存', exact: true }).click()
  await expect(dialog).not.toBeVisible()
  expect(rows.find((row) => row.id === 8)?.source_text).toBe('')
  await page.locator('.filter-row .el-select').nth(0).click()
  await page.getByRole('option', { name: '暗色', exact: true }).click()
  await page.locator('.filter-row .el-select').nth(1).click()
  await page.getByRole('option', { name: '桌面', exact: true }).click()
  await page.locator('.bg-item').nth(1).dragTo(page.locator('.bg-item').first())
  await page.getByRole('button', { name: '保存顺序' }).click()
  await expect.poll(() => rows[0].id).toBe(8)
  expect(await page.evaluate(() => localStorage.getItem('blog-dark-bg-id'))).toBe('7')
  await page.getByRole('button', { name: '添加背景图' }).click()
  const upload = page.getByRole('dialog', { name: '添加背景图' })
  await upload.getByPlaceholder('例如：画师名字 · 作品名称').fill('批量图片共同来源')
  await upload
    .getByPlaceholder('https://…（点击来源牌后打开）')
    .fill('https://example.com/collection')
  await upload.getByRole('button', { name: '从媒体库选择' }).click()
  const picker = page.getByRole('dialog', { name: '选择背景图' })
  await picker.locator('.image-option').nth(0).click()
  await picker.locator('.image-option').nth(1).click()
  await picker.getByRole('button', { name: /确认选择/ }).click()
  await expect(upload.getByText(/批量添加的图片共用此来源/)).toBeVisible()
  await upload.getByRole('button', { name: '确认上传' }).click()
  await expect(upload).not.toBeVisible()
  expect(
    creations.map(({ image_id, source_text, source_url }) => ({
      image_id,
      source_text,
      source_url,
    })),
  ).toEqual([
    { image_id: 14, source_text: '批量图片共同来源', source_url: 'https://example.com/collection' },
    { image_id: 15, source_text: '批量图片共同来源', source_url: 'https://example.com/collection' },
  ])
  await page.screenshot({ path: '.playwright-mcp/background-credit-admin.png' })
  await page.goto('/moments')
  await expect(page.locator('.background-credit-text')).toHaveText('更新来源')
})
