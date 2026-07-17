import { ref, computed, onMounted, onUnmounted, watch, type Ref } from 'vue'
import type { Friend } from '@/types'

/** 游动模式：bounce 碰壁反弹，scroll 单向循环 */
export type FloatingMode = 'bounce' | 'scroll'

/** 单个游动头像的状态 */
export interface FloatingAvatar {
  name: string
  url: string
  avatar: string
  bio: string
  x: number
  y: number
  vx: number
  vy: number
  size: number
  paused: boolean
  style: { transform: string; width: string; height: string }
}

/** useFloatingAvatars 配置项 */
export interface UseFloatingAvatarsOptions {
  /** 友链源数据 */
  friends: Ref<Friend[]> | Friend[]
  /** 容器元素引用，用于计算边界 */
  containerRef: Ref<HTMLElement | null>
  /** 游动模式 */
  mode?: FloatingMode
  /** 头像基准直径(px) */
  avatarSize?: number
  /** 速度倍率 */
  speed?: number
}

const MAX_SPEED = 0.6
const MIN_SPEED = 0.15

/**
 * 让友链头像在容器内游动的物理引擎。
 *
 * - bounce 模式：随机位置与速度，碰壁反弹，适合少量头像。
 * - scroll 模式：统一向左侧移动，出界后从右侧重新进入，适合大量头像单行展示。
 * - 悬停时可通过 pause/resume 控制单个头像。
 * - 组件卸载、页面隐藏或 prefers-reduced-motion 时自动停止动画。
 */
export function useFloatingAvatars(options: UseFloatingAvatarsOptions) {
  const { containerRef, mode = 'bounce', avatarSize = 64, speed = 1 } = options
  const friendsSource = options.friends

  const width = ref(0)
  const height = ref(0)
  const reducedMotion = ref(false)
  const rafId = ref(0)
  const items = ref<FloatingAvatar[]>([])

  const sourceArray = computed<Friend[]>(() =>
    Array.isArray(friendsSource) ? friendsSource : friendsSource.value,
  )

  /** 初始化或重置所有头像状态 */
  function initItems() {
    const container = containerRef.value
    if (!container) return

    const rect = container.getBoundingClientRect()
    width.value = rect.width
    height.value = rect.height

    const size = getResponsiveSize()
    const list = sourceArray.value

    items.value = list.map((friend, index) => {
      const item = createAvatar(friend, index, size)
      // 避免初始位置重叠：按索引均匀分布，scroll 模式沿 Y 轴散开
      if (mode === 'scroll') {
        item.x = (width.value / Math.max(list.length, 1)) * index
        item.y = Math.random() * Math.max(1, height.value - size)
        item.vx = -(MIN_SPEED + Math.random() * 0.2) * speed
        item.vy = 0
      } else {
        item.x = Math.random() * Math.max(1, width.value - size)
        item.y = Math.random() * Math.max(1, height.value - size)
        item.vx = (Math.random() > 0.5 ? 1 : -1) * (MIN_SPEED + Math.random() * (MAX_SPEED - MIN_SPEED)) * speed
        item.vy = (Math.random() > 0.5 ? 1 : -1) * (MIN_SPEED + Math.random() * (MAX_SPEED - MIN_SPEED)) * speed
      }
      return item
    })
  }

  /** 根据视口返回头像尺寸 */
  function getResponsiveSize(): number {
    if (typeof window === 'undefined') return avatarSize
    return window.innerWidth <= 768 ? Math.max(40, avatarSize * 0.75) : avatarSize
  }

  /** 根据 Friend 创建游动项 */
  function createAvatar(friend: Friend, _index: number, size: number): FloatingAvatar {
    return {
      name: friend.name,
      url: friend.url,
      avatar: friend.avatar,
      bio: friend.bio,
      x: 0,
      y: 0,
      vx: 0,
      vy: 0,
      size,
      paused: false,
      style: { transform: 'translate3d(0,0,0)', width: `${size}px`, height: `${size}px` },
    }
  }

  /** 更新单个头像在 bounce 模式下的位置与速度 */
  function updateBounce(item: FloatingAvatar) {
    item.x += item.vx
    item.y += item.vy

    const maxX = width.value - item.size
    const maxY = height.value - item.size

    if (item.x <= 0) {
      item.x = 0
      item.vx = Math.abs(item.vx)
    } else if (item.x >= maxX) {
      item.x = maxX
      item.vx = -Math.abs(item.vx)
    }

    if (item.y <= 0) {
      item.y = 0
      item.vy = Math.abs(item.vy)
    } else if (item.y >= maxY) {
      item.y = maxY
      item.vy = -Math.abs(item.vy)
    }
  }

  /** 更新单个头像在 scroll 模式下的位置（单向循环） */
  function updateScroll(item: FloatingAvatar) {
    item.x += item.vx
    if (item.x < -item.size) {
      item.x = width.value + Math.random() * item.size
      item.y = Math.random() * Math.max(1, height.value - item.size)
    }
  }

  /** 将状态同步到 style */
  function syncStyle(item: FloatingAvatar) {
    item.style.transform = `translate3d(${item.x.toFixed(1)}px, ${item.y.toFixed(1)}px, 0)`
    item.style.width = `${item.size}px`
    item.style.height = `${item.size}px`
  }

  /** 动画主循环 */
  function tick() {
    if (!reducedMotion.value && !document.hidden) {
      const updater = mode === 'scroll' ? updateScroll : updateBounce
      for (const item of items.value) {
        if (!item.paused) {
          updater(item)
        }
        syncStyle(item)
      }
    }
    rafId.value = requestAnimationFrame(tick)
  }

  /** 暂停单个头像 */
  function pause(name: string) {
    const item = items.value.find((i) => i.name === name)
    if (item) item.paused = true
  }

  /** 恢复单个头像 */
  function resume(name: string) {
    const item = items.value.find((i) => i.name === name)
    if (item) item.paused = false
  }

  /** 监听容器尺寸变化 */
  let resizeObserver: ResizeObserver | null = null
  function observeSize() {
    if (typeof ResizeObserver === 'undefined' || !containerRef.value) return
    resizeObserver = new ResizeObserver(() => {
      initItems()
    })
    resizeObserver.observe(containerRef.value)
  }

  /** 监听 prefers-reduced-motion */
  let motionMedia: MediaQueryList | null = null
  function observeMotion() {
    if (typeof window === 'undefined') return
    motionMedia = window.matchMedia('(prefers-reduced-motion: reduce)')
    reducedMotion.value = motionMedia.matches
    const handler = (event: MediaQueryListEvent) => {
      reducedMotion.value = event.matches
    }
    motionMedia.addEventListener('change', handler)
    return () => motionMedia?.removeEventListener('change', handler)
  }

  /** 监听页面可见性 */
  function onVisibilityChange() {
    // 无需额外逻辑：tick 中已判断 document.hidden
  }

  onMounted(() => {
    initItems()
    observeSize()
    const cleanupMotion = observeMotion()
    document.addEventListener('visibilitychange', onVisibilityChange)
    rafId.value = requestAnimationFrame(tick)

    onUnmounted(() => {
      cancelAnimationFrame(rafId.value)
      resizeObserver?.disconnect()
      document.removeEventListener('visibilitychange', onVisibilityChange)
      cleanupMotion?.()
    })
  })

  // 源数据变化时重新初始化
  watch(sourceArray, initItems, { deep: true })

  return {
    items: computed(() => items.value),
    pause,
    resume,
  }
}
