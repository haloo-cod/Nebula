import { ref, watch, computed } from 'vue'
import { defineStore } from 'pinia'
import {
  waitForNextTextureUploadSettled,
  waitForTextureUploadQueueIdle,
} from '@/components/liquid-glass/liquidGlassQueue'
import {
  darkBackgrounds as defaultDarkBgs,
  lightBackgrounds as defaultLightBgs,
  mobileDarkBackgrounds as defaultMobileDarkBgs,
  mobileLightBackgrounds as defaultMobileLightBgs,
} from '@/data/backgrounds'
import type { BackgroundItem } from '@/data/backgrounds'
import { fetchBackgrounds } from '@/api/backgrounds'

/** 站点主题:dark=暗色(默认),light=亮色 */
export type Theme = 'dark' | 'light'

const THEME_KEY = 'blog-theme'
const BACKGROUND_BLUR_ENABLED_KEY = 'blog-background-blur-enabled'
const BACKGROUND_BLUR_KEY = 'blog-background-blur'
const LIQUID_GLASS_ENABLED_KEY = 'blog-liquid-glass-enabled'
const LIQUID_GLASS_BLUR_KEY = 'blog-liquid-glass-blur'
const DARK_BG_KEY = 'blog-dark-bg'
const LIGHT_BG_KEY = 'blog-light-bg'
const MOBILE_DARK_BG_KEY = 'blog-mobile-dark-bg'
const MOBILE_LIGHT_BG_KEY = 'blog-mobile-light-bg'
const RAIN_ENABLED_KEY = 'blog-rain-enabled'
const RAIN_INTENSITY_KEY = 'blog-rain-intensity'
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

/** 读取持久化的背景图索引 */
function readStoredBgIndex(key: string, maxIndex: number): number {
  if (typeof localStorage === 'undefined') return 0
  const saved = Number(localStorage.getItem(key))
  if (Number.isInteger(saved) && saved >= 0 && saved < maxIndex) return saved
  return 0
}

/** 读取持久化的雨量(0=轻,1=中,2=重),缺省回退到 1(中) */
function readStoredRainIntensity(): number {
  if (typeof localStorage === 'undefined') return 1
  const saved = Number(localStorage.getItem(RAIN_INTENSITY_KEY))
  if (saved >= 0 && saved <= 2) return saved
  return 1
}

/** 全局 UI 状态 — 控制导航栏显隐、站点主题等 */
export const useUIStore = defineStore('ui', () => {
  const showNavbar = ref(true)
  const theme = ref<Theme>(readStoredTheme())
  const backgroundBlurEnabled = ref(readStoredBoolean(BACKGROUND_BLUR_ENABLED_KEY, false))
  const backgroundBlur = ref(readStoredBackgroundBlur() ?? DEFAULT_BACKGROUND_BLUR)
  const liquidGlassEnabled = ref(readStoredBoolean(LIQUID_GLASS_ENABLED_KEY, false))
  const liquidGlassBlur = ref(readStoredLiquidGlassBlur())

  // 背景图动态列表（初始用静态 fallback，API 加载成功后替换）
  const darkBgs = ref<BackgroundItem[]>([...defaultDarkBgs])
  const lightBgs = ref<BackgroundItem[]>([...defaultLightBgs])
  const mobileDarkBgs = ref<BackgroundItem[]>([...defaultMobileDarkBgs])
  const mobileLightBgs = ref<BackgroundItem[]>([...defaultMobileLightBgs])

  const darkBgIndex = ref(readStoredBgIndex(DARK_BG_KEY, darkBgs.value.length))
  const lightBgIndex = ref(readStoredBgIndex(LIGHT_BG_KEY, lightBgs.value.length))
  const mobileDarkBgIndex = ref(readStoredBgIndex(MOBILE_DARK_BG_KEY, mobileDarkBgs.value.length))
  const mobileLightBgIndex = ref(readStoredBgIndex(MOBILE_LIGHT_BG_KEY, mobileLightBgs.value.length))
  const rainEnabled = ref(readStoredBoolean(RAIN_ENABLED_KEY, false))
  const rainIntensity = ref(readStoredRainIntensity())
  const isMobile = ref(typeof window !== 'undefined' && window.innerWidth <= 768)
  const themeTransitioning = ref(false)
  const themeTransitionRevealStarted = ref(false)

  /** 当前主题下选中的背景图 URL（桌面端/移动端自动切换） */
  const currentBgUrl = computed(() => {
    const darkGroup = isMobile.value ? mobileDarkBgs.value : darkBgs.value
    const lightGroup = isMobile.value ? mobileLightBgs.value : lightBgs.value
    const group = theme.value === 'dark' ? darkGroup : lightGroup
    const idx = theme.value === 'dark'
      ? (isMobile.value ? mobileDarkBgIndex.value : darkBgIndex.value)
      : (isMobile.value ? mobileLightBgIndex.value : lightBgIndex.value)
    return group[Math.min(idx, group.length - 1)]?.src ?? ''
  })

  // 视口变化时更新 isMobile
  if (typeof window !== 'undefined') {
    window.addEventListener('resize', () => {
      isMobile.value = window.innerWidth <= 768
    })
  }

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

  watch(darkBgIndex, (next) => {
    if (typeof localStorage !== 'undefined') {
      localStorage.setItem(DARK_BG_KEY, String(next))
    }
  })

  watch(lightBgIndex, (next) => {
    if (typeof localStorage !== 'undefined') {
      localStorage.setItem(LIGHT_BG_KEY, String(next))
    }
  })

  watch(mobileDarkBgIndex, (next) => {
    if (typeof localStorage !== 'undefined') {
      localStorage.setItem(MOBILE_DARK_BG_KEY, String(next))
    }
  })

  watch(mobileLightBgIndex, (next) => {
    if (typeof localStorage !== 'undefined') {
      localStorage.setItem(MOBILE_LIGHT_BG_KEY, String(next))
    }
  })

  watch(rainEnabled, (next) => {
    if (typeof localStorage !== 'undefined') {
      localStorage.setItem(RAIN_ENABLED_KEY, String(next))
    }
  })

  watch(rainIntensity, (next) => {
    if (typeof localStorage !== 'undefined') {
      localStorage.setItem(RAIN_INTENSITY_KEY, String(next))
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

  /** 设置 dark 主题背景图索引 */
  function setDarkBg(index: number) {
    if (index >= 0 && index < darkBgs.value.length) {
      darkBgIndex.value = index
    }
  }

  /** 设置 light 主题背景图索引 */
  function setLightBg(index: number) {
    if (index >= 0 && index < lightBgs.value.length) {
      lightBgIndex.value = index
    }
  }

  /** 设置移动端 dark 主题背景图索引 */
  function setMobileDarkBg(index: number) {
    if (index >= 0 && index < mobileDarkBgs.value.length) {
      mobileDarkBgIndex.value = index
    }
  }

  /** 设置移动端 light 主题背景图索引 */
  function setMobileLightBg(index: number) {
    if (index >= 0 && index < mobileLightBgs.value.length) {
      mobileLightBgIndex.value = index
    }
  }

  /** 设置下雨特效开关 */
  function setRainEnabled(enabled: boolean) {
    rainEnabled.value = enabled
  }

  /** 设置雨量(0=轻,1=中,2=重) */
  function setRainIntensity(level: number) {
    if (level >= 0 && level <= 2) {
      rainIntensity.value = level
    }
  }

  /** 在亮/暗主题之间切换 */
  async function toggleTheme() {
    if (themeTransitioning.value) return

    // 先拉起全屏主题遮罩,并等一帧让浏览器真正 paint 出遮罩。
    // 这样后续背景切换和 WebGL 纹理上传都发生在遮罩下面。
    themeTransitioning.value = true
    themeTransitionRevealStarted.value = false
    await waitForNextFrames(1)

    const firstTextureReady = liquidGlassEnabled.value ? waitForNextTextureUploadSettled() : null
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
    // 剩余面板继续按队列逐个淡入,保留"依次呈现"的动画感。
    await firstTextureReady
    themeTransitionRevealStarted.value = true

    // 队列全部排空后再等两帧,确保背景层 recomposite 与最后一帧渲染稳定。
    await waitForTextureUploadQueueIdle()
    await waitForNextFrames(2)
    themeTransitioning.value = false
    themeTransitionRevealStarted.value = false
  }

  /**
   * 从后端 API 加载背景图列表，替换静态 fallback
   * 应在 App.vue 的 onMounted 中调用
   */
  async function loadBackgrounds() {
    try {
      const [darkDesktop, lightDesktop, darkMobile, lightMobile] = await Promise.all([
        fetchBackgrounds('dark', 'desktop'),
        fetchBackgrounds('light', 'desktop'),
        fetchBackgrounds('dark', 'mobile'),
        fetchBackgrounds('light', 'mobile'),
      ])

      // 仅当 API 返回有效数据时替换（避免空数组导致页面无背景）
      if (darkDesktop.length > 0) darkBgs.value = darkDesktop.map((i) => ({ src: i.url }))
      if (lightDesktop.length > 0) lightBgs.value = lightDesktop.map((i) => ({ src: i.url }))
      if (darkMobile.length > 0) mobileDarkBgs.value = darkMobile.map((i) => ({ src: i.url }))
      if (lightMobile.length > 0) mobileLightBgs.value = lightMobile.map((i) => ({ src: i.url }))

      // 索引越界修正（API 返回的列表可能比 localStorage 存的索引短）
      if (darkBgIndex.value >= darkBgs.value.length) darkBgIndex.value = 0
      if (lightBgIndex.value >= lightBgs.value.length) lightBgIndex.value = 0
      if (mobileDarkBgIndex.value >= mobileDarkBgs.value.length) mobileDarkBgIndex.value = 0
      if (mobileLightBgIndex.value >= mobileLightBgs.value.length) mobileLightBgIndex.value = 0
    } catch {
      // API 失败时静默保留 fallback 静态图片，不影响用户体验
    }
  }

  return {
    showNavbar,
    theme,
    backgroundBlurEnabled,
    backgroundBlur,
    liquidGlassEnabled,
    liquidGlassBlur,
    darkBgIndex,
    lightBgIndex,
    mobileDarkBgIndex,
    mobileLightBgIndex,
    darkBgs,
    lightBgs,
    mobileDarkBgs,
    mobileLightBgs,
    isMobile,
    currentBgUrl,
    themeTransitioning,
    themeTransitionRevealStarted,
    setBackgroundBlurEnabled,
    setBackgroundBlur,
    setLiquidGlassEnabled,
    setLiquidGlassBlur,
    setDarkBg,
    setLightBg,
    setMobileDarkBg,
    setMobileLightBg,
    rainEnabled,
    rainIntensity,
    setRainEnabled,
    setRainIntensity,
    toggleTheme,
    loadBackgrounds,
  }
})
