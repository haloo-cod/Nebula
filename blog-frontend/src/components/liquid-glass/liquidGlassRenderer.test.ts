import { afterEach, beforeEach, describe, expect, it, vi } from 'vitest'
import {
  loadImage,
  preloadTexture,
  preloadVideoTexture,
  resolveVideoSource,
  withCorsCacheKey,
} from './liquidGlassRenderer'

describe('liquidGlassRenderer 空 URL 防护与图片失败缓存逐出', () => {
  const originalFetch = globalThis.fetch
  const originalImage = globalThis.Image
  const originalCreateImageBitmap = globalThis.createImageBitmap

  beforeEach(() => {
    vi.restoreAllMocks()
  })

  afterEach(() => {
    globalThis.fetch = originalFetch
    globalThis.Image = originalImage
    globalThis.createImageBitmap = originalCreateImageBitmap
  })

  it('withCorsCacheKey 遇到空串不生成 ?_cors=2，正常 URL 保留参数拼接', () => {
    expect(withCorsCacheKey('')).toBe('')
    expect(withCorsCacheKey('   ')).toBe('')
    expect(withCorsCacheKey('/uploads/images/bg.webp')).toBe('/uploads/images/bg.webp?_cors=2')
    expect(withCorsCacheKey('/uploads/images/bg.webp?v=1')).toBe(
      '/uploads/images/bg.webp?v=1&_cors=2',
    )
  })

  it('空 URL 不会触发网络请求或 Image 加载', async () => {
    const fetchMock = vi.fn()
    const imageMock = vi.fn()
    globalThis.fetch = fetchMock as typeof fetch
    // 替换全局 Image 构造函数以确认空 URL 不会实例化 Image。
    globalThis.Image = imageMock as unknown as typeof Image

    await expect(loadImage('')).rejects.toThrow('Empty image URL')
    await expect(loadImage('   ')).rejects.toThrow('Empty image URL')
    await expect(resolveVideoSource('')).rejects.toThrow('Empty video URL')
    await expect(preloadTexture('')).resolves.toBe(false)
    await expect(preloadVideoTexture('')).resolves.toBe(false)

    expect(fetchMock).not.toHaveBeenCalled()
    expect(imageMock).not.toHaveBeenCalled()
  })

  it('loadImage 失败后逐出缓存，后续再次切换同一 URL 可重试并成功', async () => {
    const testUrl = '/uploads/images/retry-bg-test.webp'
    const fakeBitmap = { width: 1920, height: 1080 } as ImageBitmap

    let imageAttempt = 0
    class FakeImage {
      crossOrigin = ''
      onload: (() => void) | null = null
      onerror: (() => void) | null = null
      decode = vi.fn().mockResolvedValue(undefined)
      set src(_value: string) {
        imageAttempt += 1
        queueMicrotask(() => {
          this.onerror?.()
        })
      }
    }

    const fetchMock = vi
      .fn()
      .mockResolvedValueOnce({
        ok: false,
        status: 503,
        blob: vi.fn(),
      })
      .mockResolvedValueOnce({
        ok: true,
        status: 200,
        blob: vi.fn().mockResolvedValue(new Blob(['img'])),
      })

    globalThis.fetch = fetchMock as typeof fetch
    // 测试环境模拟 Image 回退路径失败。
    globalThis.Image = FakeImage as unknown as typeof Image
    globalThis.createImageBitmap = vi.fn().mockResolvedValue(fakeBitmap)

    await expect(loadImage(testUrl)).rejects.toThrow(`Failed to load image: ${testUrl}?_cors=2`)
    expect(imageAttempt).toBe(1)

    const retryResult = await loadImage(testUrl)
    expect(retryResult).toBe(fakeBitmap)
    expect(fetchMock).toHaveBeenCalledTimes(2)
  })
})
