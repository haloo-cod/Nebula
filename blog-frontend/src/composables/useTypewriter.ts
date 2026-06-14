import { ref, onMounted, onUnmounted, type Ref } from 'vue'

/** useTypewriter 的可选配置 */
export interface TypewriterOptions {
  speed?: number // 每个字符间隔(ms)
  startDelay?: number // 开始前延迟(ms)
  instant?: boolean // 直接显示完整文本,跳过动画
}

/** useTypewriter 的返回值 */
export interface TypewriterResult {
  displayed: Ref<string> // 当前已显示的文本
  done: Ref<boolean> // 动画是否完成
}

/**
 * 可复用打字机效果
 * @param text 要逐字显示的完整文本
 * @param options 配置项
 * @returns 响应式的已显示文本与完成状态
 */
export function useTypewriter(text: string, options: TypewriterOptions = {}): TypewriterResult {
  const { speed = 120, startDelay = 300, instant = false } = options
  const displayed = ref(instant ? text : '')
  const done = ref(instant)
  let timer: ReturnType<typeof setTimeout> | null = null
  let i = 0

  function tick() {
    if (i <= text.length) {
      displayed.value = text.slice(0, i)
      i += 1
      timer = setTimeout(tick, speed)
    } else {
      done.value = true
    }
  }

  onMounted(() => {
    if (instant) return
    timer = setTimeout(tick, startDelay)
  })

  onUnmounted(() => {
    if (timer) clearTimeout(timer)
  })

  return { displayed, done }
}
