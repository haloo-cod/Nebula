import { ref, watch } from 'vue'
import { defineStore } from 'pinia'
import {
  waitForFirstTextureUploadSettled,
  waitForTextureUploadQueueIdle,
} from '@/components/liquidGlassQueue'

/** 站点主题:dark=暗色(默认),light=亮色 */
export type Theme = 'dark' | 'light'

const THEME_KEY = 'blog-theme'
const BACKGROUND_BLUR_ENABLED_KEY = 'blog-background-blur-enabled'
const BACKGROUND_BLUR_KEY = 'blog-background-blur'
const LIQUID_GLASS_ENABLED_KEY = 'blog-liquid-glass-enabled'
const LIQUID_GLASS_BLUR_KEY = 'blog-liquid-glass-blur'
const MIN_BACKGROUND_BLUR = 0
const MAX_BACKGROUND_BLUR = 24
const DEFAULT_BACKGROUND_BLUR = 5
const MIN_LIQUID_GLASS_BLUR = 0
const MAX_LIQUID_GLASS_BLUR = 12
const DEFAULT_LIQUID_GLASS_BLUR = 0

/** 读取持久化的主题,缺省回退到 dark */
function readStoredTheme(): Theme {
  if (typeof localStorage === 'undefined') return 'dark'
  const saved = localStorage.getItem(THEME_KEY)
  return saved === 'light' || saved === 'dark' ? saved : 'dark'
}

/** 把主题写到根节点的 data-theme 上,供 CSS 变量切换 */
function applyTheme(theme: Theme) {
  if (typeof document === 'undefined') return
  document.documentElement.setAttribute('data-theme', theme)
}

/** 读取持久化的背景模糊值,缺省回退到 0 */
function readStoredBackgroundBlur(): number {
  if (typeof localStorage === 'undefined') return MIN_BACKGROUND_BLUR
  const saved = Number(localStorage.getItem(BACKGROUND_BLUR_KEY))
  if (Number.isNaN(saved)) return MIN_BACKGROUND_BLUR
  return Math.min(MAX_BACKGROUND_BLUR, Math.max(MIN_BACKGROUND_BLUR, saved))
}

/** 约束背景模糊值,避免越界 */
function clampBackgroundBlur(value: number): number {
  return Math.min(MAX_BACKGROUND_BLUR, Math.max(MIN_BACKGROUND_BLUR, value))
}

/** 读取持久化的布尔开关,缺省回退到 fallback */
function readStoredBoolean(key: string, fallback: boolean): boolean {
  if (typeof localStorage === 'undefined') return fallback
  const saved = localStorage.getItem(key)
  if (saved === 'true') return true
  if (saved === 'false') return false
  return fallback
}

/** 读取持久化的液态玻璃模糊值,缺省回退到默认值 */
function readStoredLiquidGlassBlur(): number {
  if (typeof localStorage === 'undefined') return DEFAULT_LIQUID_GLASS_BLUR
  const saved = Number(localStorage.getItem(LIQUID_GLASS_BLUR_KEY))
  if (Number.isNaN(saved)) return DEFAULT_LIQUID_GLASS_BLUR
  return Math.min(MAX_LIQUID_GLASS_BLUR, Math.max(MIN_LIQUID_GLASS_BLUR, saved))
}

/** 约束液态玻璃模糊值,避免越界 */
function clampLiquidGlassBlur(value: number): number {
  return Math.min(MAX_LIQUID_GLASS_BLUR, Math.max(MIN_LIQUID_GLASS_BLUR, value))
}

/** 等待两帧,给背景层 recomposite 与首帧渲染留缓冲 */
function waitForNextFrames(count = 2): Promise<void> {
  return new Promise((resolve) => {
    const step = () => {
      if (count <= 0) {
        resolve()
        return
      }
      count -= 1
      requestAnimationFrame(step)
    }
    requestAnimationFrame(step)
  })
}

/** 全局 UI 状态 — 控制导航栏显隐、站点主题等 */
export const useUIStore = defineStore('ui', () => {
  const showNavbar = ref(true)
  const theme = ref<Theme>(readStoredTheme())
  const backgroundBlurEnabled = ref(readStoredBoolean(BACKGROUND_BLUR_ENABLED_KEY, false))
  const backgroundBlur = ref(readStoredBackgroundBlur() || DEFAULT_BACKGROUND_BLUR)
  const liquidGlassEnabled = ref(readStoredBoolean(LIQUID_GLASS_ENABLED_KEY, true))
  const liquidGlassBlur = ref(readStoredLiquidGlassBlur())
  const themeTransitioning = ref(false)
  const themeTransitionRevealStarted = ref(false)

  // 初始化即应用一次,保证刷新后样式与状态一致
  applyTheme(theme.value)

  // 主题变化时同步到 DOM 与 localStorage
  watch(theme, (next) => {
    applyTheme(next)
    if (typeof localStorage !== 'undefined') localStorage.setItem(THEME_KEY, next)
  })

  watch(backgroundBlurEnabled, (next) => {
    if (typeof localStorage !== 'undefined') {
      localStorage.setItem(BACKGROUND_BLUR_ENABLED_KEY, String(next))
    }
  })

  // 背景模糊变化时同步到 localStorage,保证刷新后设置保留
  watch(backgroundBlur, (next) => {
    const value = clampBackgroundBlur(next)
    if (backgroundBlur.value !== value) {
      backgroundBlur.value = value
      return
    }
    if (typeof localStorage !== 'undefined') {
      localStorage.setItem(BACKGROUND_BLUR_KEY, String(value))
    }
  })

  watch(liquidGlassEnabled, (next) => {
    if (typeof localStorage !== 'undefined') {
      localStorage.setItem(LIQUID_GLASS_ENABLED_KEY, String(next))
    }
  })

  watch(liquidGlassBlur, (next) => {
    const value = clampLiquidGlassBlur(next)
    if (liquidGlassBlur.value !== value) {
      liquidGlassBlur.value = value
      return
    }
    if (typeof localStorage !== 'undefined') {
      localStorage.setItem(LIQUID_GLASS_BLUR_KEY, String(value))
    }
  })

  /** 设置背景模糊是否启用 */
  function setBackgroundBlurEnabled(enabled: boolean) {
    backgroundBlurEnabled.value = enabled
    if (enabled && backgroundBlur.value <= 0) {
      backgroundBlur.value = DEFAULT_BACKGROUND_BLUR
    }
  }

  /** 设置背景图模糊强度(px) */
  function setBackgroundBlur(value: number) {
    backgroundBlur.value = clampBackgroundBlur(value)
  }

  /** 设置液态玻璃是否启用 */
  function setLiquidGlassEnabled(enabled: boolean) {
    liquidGlassEnabled.value = enabled
  }

  /** 设置液态玻璃内部模糊强度(px) */
  function setLiquidGlassBlur(value: number) {
    liquidGlassBlur.value = clampLiquidGlassBlur(value)
  }

  /** 在亮/暗主题之间切换 */
  async function toggleTheme() {
    if (themeTransitioning.value) return

    // 先拉起全屏主题遮罩,并等一帧让浏览器真正 paint 出遮罩。
    // 这样后续背景切换和 WebGL 纹理上传都发生在遮罩下面。
    themeTransitioning.value = true
    themeTransitionRevealStarted.value = false
    await waitForNextFrames(1)

    theme.value = theme.value === 'dark' ? 'light' : 'dark'

    if (!liquidGlassEnabled.value) {
      await waitForNextFrames(2)
      themeTransitionRevealStarted.value = true
      await waitForNextFrames(2)
      themeTransitioning.value = false
      themeTransitionRevealStarted.value = false
      return
    }

    // 首个 LiquidGlass 面板已画入新纹理后,开始撤掉遮罩;
    // 剩余面板继续按队列逐个淡入,保留“依次呈现”的动画感。
    await waitForFirstTextureUploadSettled()
    themeTransitionRevealStarted.value = true

    // 队列全部排空后再等两帧,确保背景层 recomposite 与最后一帧渲染稳定。
    await waitForTextureUploadQueueIdle()
    await waitForNextFrames(2)
    themeTransitioning.value = false
    themeTransitionRevealStarted.value = false
  }

  return {
    showNavbar,
    theme,
    backgroundBlurEnabled,
    backgroundBlur,
    liquidGlassEnabled,
    liquidGlassBlur,
    themeTransitioning,
    themeTransitionRevealStarted,
    setBackgroundBlurEnabled,
    setBackgroundBlur,
    setLiquidGlassEnabled,
    setLiquidGlassBlur,
    toggleTheme,
  }
})
