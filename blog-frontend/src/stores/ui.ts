import { ref, watch } from 'vue'
import { defineStore } from 'pinia'
import {
  waitForFirstTextureUploadSettled,
  waitForTextureUploadQueueIdle,
} from '@/components/liquidGlassQueue'

/** 站点主题:dark=暗色(默认),light=亮色 */
export type Theme = 'dark' | 'light'

const THEME_KEY = 'blog-theme'

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
  const themeTransitioning = ref(false)
  const themeTransitionRevealStarted = ref(false)

  // 初始化即应用一次,保证刷新后样式与状态一致
  applyTheme(theme.value)

  // 主题变化时同步到 DOM 与 localStorage
  watch(theme, (next) => {
    applyTheme(next)
    if (typeof localStorage !== 'undefined') localStorage.setItem(THEME_KEY, next)
  })

  /** 在亮/暗主题之间切换 */
  async function toggleTheme() {
    if (themeTransitioning.value) return

    // 先拉起全屏主题遮罩,并等一帧让浏览器真正 paint 出遮罩。
    // 这样后续背景切换和 WebGL 纹理上传都发生在遮罩下面。
    themeTransitioning.value = true
    themeTransitionRevealStarted.value = false
    await waitForNextFrames(1)

    theme.value = theme.value === 'dark' ? 'light' : 'dark'

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

  return { showNavbar, theme, themeTransitioning, themeTransitionRevealStarted, toggleTheme }
})
