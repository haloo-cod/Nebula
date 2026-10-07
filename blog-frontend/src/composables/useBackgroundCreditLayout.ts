import { onMounted, onUnmounted, ref, watch, type Ref } from 'vue'
import { useRoute } from 'vue-router'
import { calculateSignLayout, type HangingSignLayout } from '@/utils/hangingSign'

/** 根据当前路由的真实内容容器测量悬挂牌留白。 */
export function useBackgroundCreditLayout(enabled: Ref<boolean>) {
  const route = useRoute()
  const layout = ref<HangingSignLayout>(calculateSignLayout(0, 64, 0))
  const pageVisible = ref(true)
  let resizeObserver: ResizeObserver | undefined
  let mutationObserver: MutationObserver | undefined
  let frame = 0
  const observed = new Set<Element>()

  function measure() {
    frame = 0
    const navbar = document.querySelector<HTMLElement>('[data-background-credit-navbar]')
    const boundaries = [
      ...document.querySelectorAll<HTMLElement>('[data-background-credit-boundary]'),
    ]
    const elements = navbar ? [navbar, ...boundaries] : boundaries
    for (const element of observed) {
      if (!elements.some((current) => current === element)) {
        resizeObserver?.unobserve(element)
        observed.delete(element)
      }
    }
    for (const element of elements) {
      if (!observed.has(element)) {
        resizeObserver?.observe(element)
        observed.add(element)
      }
    }
    const rects = boundaries
      .map((element) => element.getBoundingClientRect())
      .filter((rect) => rect.width > 0 && rect.height > 0)
    const gutter = rects.length ? Math.min(...rects.map((rect) => rect.left)) : 0
    const navRect = navbar?.getBoundingClientRect()
    layout.value = calculateSignLayout(gutter, navRect?.bottom ?? 64, window.innerHeight)
    if (!enabled.value || window.innerWidth <= 768 || !navRect || navRect.height === 0)
      layout.value.visible = false
  }

  function scheduleMeasure() {
    if (!frame) frame = requestAnimationFrame(measure)
  }

  function onVisibility() {
    pageVisible.value = !document.hidden
    if (document.hidden && frame) {
      cancelAnimationFrame(frame)
      frame = 0
    } else scheduleMeasure()
  }

  watch(
    () => route.fullPath,
    () => {
      layout.value.visible = false
      scheduleMeasure()
    },
    { flush: 'post' },
  )
  watch(enabled, scheduleMeasure)

  onMounted(() => {
    pageVisible.value = !document.hidden
    resizeObserver = new ResizeObserver(scheduleMeasure)
    mutationObserver = new MutationObserver(scheduleMeasure)
    const content = document.querySelector('.app-content')
    if (content) mutationObserver.observe(content, { childList: true, subtree: true })
    window.addEventListener('resize', scheduleMeasure)
    document.addEventListener('visibilitychange', onVisibility)
    scheduleMeasure()
  })

  onUnmounted(() => {
    if (frame) cancelAnimationFrame(frame)
    resizeObserver?.disconnect()
    mutationObserver?.disconnect()
    observed.clear()
    window.removeEventListener('resize', scheduleMeasure)
    document.removeEventListener('visibilitychange', onVisibility)
  })

  return { layout, pageVisible }
}
