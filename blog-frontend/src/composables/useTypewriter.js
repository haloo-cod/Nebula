import { ref, onMounted, onUnmounted } from 'vue'

/**
 * 可复用打字机效果
 * @param {string} text 要逐字显示的完整文本
 * @param {object} options
 * @param {number} options.speed 每个字符间隔(ms)
 * @param {number} options.startDelay 开始前延迟(ms)
 * @param {boolean} options.instant 直接显示完整文本，跳过动画
 * @returns {{ displayed: import('vue').Ref<string>, done: import('vue').Ref<boolean> }}
 */
export function useTypewriter(text, options = {}) {
  const { speed = 120, startDelay = 300, instant = false } = options
  const displayed = ref(instant ? text : '')
  const done = ref(instant)
  let timer = null
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
