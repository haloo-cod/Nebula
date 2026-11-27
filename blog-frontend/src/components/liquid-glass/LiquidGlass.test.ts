import { afterEach, beforeEach, describe, expect, it, vi } from 'vitest'
import { computed, reactive, ref } from 'vue'
import { flushPromises, mount } from '@vue/test-utils'
import LiquidGlass from './LiquidGlass.vue'
import PageBackground from '@/components/PageBackground.vue'
import type { BackgroundItem } from '@/data/backgrounds'

const themeRef = ref<'dark' | 'light'>('dark')
const themeTransitioningRef = ref(false)
const backgroundBlurRef = ref(0)
const backgroundBlurEnabledRef = ref(false)
const currentBackgroundRef = ref<BackgroundItem>({ src: '', mediaType: 'image' })
const currentBgUrlRef = computed(() => currentBackgroundRef.value.src)

// 使用包含 ref/computed 的 reactive 模拟 Pinia store，同时兼容直接读取与 storeToRefs()。
const uiState = reactive({
  theme: themeRef,
  themeTransitioning: themeTransitioningRef,
  backgroundBlur: backgroundBlurRef,
  backgroundBlurEnabled: backgroundBlurEnabledRef,
  currentBgUrl: currentBgUrlRef,
  currentBackground: currentBackgroundRef,
})

vi.mock('@/stores/ui', () => ({
  useUIStore: () => uiState,
}))

const rendererMocks = vi.hoisted(() => ({
  registerInstance: vi.fn(() => 1),
  unregisterInstance: vi.fn(),
  markInstanceReady: vi.fn(),
  setInstanceBackground: vi.fn(),
  setInstanceFirstRenderCallback: vi.fn(),
  onContextLost: vi.fn(),
  onContextRestored: vi.fn(),
  offContextCallbacks: vi.fn(),
  loadImage: vi.fn(),
  uploadTexture: vi.fn(() => true),
  preloadTexture: vi.fn(async () => true),
  preloadVideoTexture: vi.fn(async () => true),
  resolveVideoSource: vi.fn(async (url: string) => `blob:${url}`),
  bindVideoElement: vi.fn(() => true),
  withCorsCacheKey: vi.fn((url: string) => (url ? `${url}?_cors=2` : '')),
  hasTexture: vi.fn(() => false),
  getTextureAspect: vi.fn(() => 16 / 9),
  getRenderScale: vi.fn(() => 1),
  getEdgeAaWidth: vi.fn(() => 1),
}))

vi.mock('@/components/liquid-glass/liquidGlassRenderer', () => ({
  ...rendererMocks,
  MAX_TRAIL_POINTS: 12,
}))

describe('LiquidGlass 与 PageBackground 背景切换竞态防护', () => {
  const originalGetContext = HTMLCanvasElement.prototype.getContext
  const originalMatchMedia = window.matchMedia

  beforeEach(() => {
    vi.clearAllMocks()
    uiState.theme = 'dark'
    uiState.themeTransitioning = false
    uiState.currentBackground = { src: '', mediaType: 'image' }
    // jsdom 未实现 2D Canvas，返回最小桩对象即可完成组件挂载。
    HTMLCanvasElement.prototype.getContext = vi.fn(
      () => ({}) as CanvasRenderingContext2D,
    ) as unknown as typeof HTMLCanvasElement.prototype.getContext
    window.matchMedia = vi.fn().mockReturnValue({
      matches: false,
      addEventListener: vi.fn(),
      removeEventListener: vi.fn(),
    }) as unknown as typeof window.matchMedia
  })

  afterEach(() => {
    HTMLCanvasElement.prototype.getContext = originalGetContext
    window.matchMedia = originalMatchMedia
  })

  it('首屏背景尚未返回时挂载 LiquidGlass 不触发空 URL 加载，数据到达后正常加载', async () => {
    const warnSpy = vi.spyOn(console, 'warn').mockImplementation(() => undefined)
    rendererMocks.loadImage.mockResolvedValue({ width: 1920, height: 1080 })

    const wrapper = mount(LiquidGlass, { props: { theme: 'dark' } })
    await flushPromises()

    expect(rendererMocks.loadImage).not.toHaveBeenCalled()
    expect(rendererMocks.preloadVideoTexture).not.toHaveBeenCalled()
    expect(warnSpy).not.toHaveBeenCalled()

    uiState.currentBackground = { src: '/uploads/images/bg-1.webp', mediaType: 'image' }
    await flushPromises()

    expect(rendererMocks.loadImage).toHaveBeenCalledTimes(1)
    expect(rendererMocks.loadImage).toHaveBeenCalledWith('/uploads/images/bg-1.webp')
    expect(rendererMocks.uploadTexture).toHaveBeenCalledWith(
      '/uploads/images/bg-1.webp',
      expect.any(Object),
    )
    expect(warnSpy).not.toHaveBeenCalled()

    wrapper.unmount()
    warnSpy.mockRestore()
  })

  it('快速切换背景时，已过期图片的失败不会输出误导告警', async () => {
    const warnSpy = vi.spyOn(console, 'warn').mockImplementation(() => undefined)
    let rejectFirst!: (reason?: unknown) => void
    rendererMocks.loadImage
      .mockImplementationOnce(
        () =>
          new Promise((_, reject) => {
            rejectFirst = reject
          }),
      )
      .mockResolvedValueOnce({ width: 1920, height: 1080 })

    uiState.currentBackground = { src: '/uploads/images/bg-a.webp', mediaType: 'image' }

    const wrapper = mount(LiquidGlass, { props: { theme: 'dark' } })
    await flushPromises()

    // 快速切换到第二张背景图，再让第一张过期请求失败
    uiState.currentBackground = { src: '/uploads/images/bg-b.webp', mediaType: 'image' }
    await flushPromises()

    rejectFirst(new Error('aborted'))
    await flushPromises()

    expect(rendererMocks.loadImage).toHaveBeenNthCalledWith(1, '/uploads/images/bg-a.webp')
    expect(rendererMocks.loadImage).toHaveBeenNthCalledWith(2, '/uploads/images/bg-b.webp')
    expect(warnSpy).not.toHaveBeenCalled()

    wrapper.unmount()
    warnSpy.mockRestore()
  })

  it('PageBackground 切换视频时不绑定空 src 属性，清空背景时不调用 preloadTexture', async () => {
    let resolveBlob!: (url: string) => void
    rendererMocks.resolveVideoSource.mockImplementationOnce(
      () =>
        new Promise((resolve) => {
          resolveBlob = resolve
        }),
    )

    uiState.currentBackground = { src: '/uploads/images/bg-1.webp', mediaType: 'image' }

    const wrapper = mount(PageBackground)
    await flushPromises()

    uiState.currentBackground = { src: '/api/v1/files/3/media', mediaType: 'video' }
    await flushPromises()

    const video = wrapper.find('video')
    expect(video.exists()).toBe(true)
    expect(video.attributes('src')).toBeUndefined()

    resolveBlob('blob:https://blog.starlitn.top/video-3')
    await flushPromises()
    expect(wrapper.get('video').attributes('src')).toBe('blob:https://blog.starlitn.top/video-3')

    rendererMocks.preloadTexture.mockClear()
    uiState.currentBackground = { src: '', mediaType: 'image' }
    await flushPromises()

    expect(rendererMocks.preloadTexture).not.toHaveBeenCalled()
    wrapper.unmount()
  })

  it('背景被清空时 LiquidGlass 会取消旧状态并停止渲染旧纹理', async () => {
    rendererMocks.loadImage.mockResolvedValue({ width: 1920, height: 1080 })
    uiState.currentBackground = { src: '/uploads/images/bg-1.webp', mediaType: 'image' }

    const wrapper = mount(LiquidGlass, { props: { theme: 'dark' } })
    await flushPromises()

    rendererMocks.setInstanceBackground.mockClear()
    rendererMocks.markInstanceReady.mockClear()

    uiState.currentBackground = { src: '', mediaType: 'image' }
    await flushPromises()

    expect(rendererMocks.setInstanceBackground).toHaveBeenCalledWith(1, '')
    expect(rendererMocks.markInstanceReady).toHaveBeenCalledWith(1, false)
    wrapper.unmount()
  })

  it('PageBackground 在两条视频背景之间直接切换时会重建 video 元素，避免复用旧帧状态', async () => {
    uiState.currentBackground = { src: '/api/v1/files/5/media', mediaType: 'video' }

    const wrapper = mount(PageBackground)
    await flushPromises()

    const firstVideoEl = wrapper.get('video').element

    uiState.currentBackground = { src: '/api/v1/files/6/media', mediaType: 'video' }
    await flushPromises()

    const secondVideoEl = wrapper.get('video').element
    expect(secondVideoEl).not.toBe(firstVideoEl)
    expect(wrapper.get('video').attributes('src')).toBe('blob:/api/v1/files/6/media')
    wrapper.unmount()
  })
})
