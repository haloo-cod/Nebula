import { afterEach, beforeEach, describe, expect, it, vi } from 'vitest'
import { defineComponent, h, nextTick, ref } from 'vue'
import { mount } from '@vue/test-utils'
import { useHangingSign } from './useHangingSign'

describe('悬挂牌指针和动画生命周期', () => {
  const cancelFrame = vi.fn()
  const releaseCapture = vi.fn()
  const removeMotionListener = vi.fn()
  let reduce = false

  beforeEach(() => {
    reduce = false
    vi.stubGlobal(
      'requestAnimationFrame',
      vi.fn(() => 42),
    )
    vi.stubGlobal('cancelAnimationFrame', cancelFrame)
    vi.stubGlobal('matchMedia', () => ({
      matches: reduce,
      addEventListener: vi.fn(),
      removeEventListener: removeMotionListener,
    }))
    cancelFrame.mockClear()
    releaseCapture.mockClear()
    removeMotionListener.mockClear()
  })
  afterEach(() => vi.unstubAllGlobals())

  function setup() {
    const active = ref(true)
    const limit = ref(0.4)
    const anchor = ref({ x: 200, y: 64 })
    let sign: ReturnType<typeof useHangingSign>
    const wrapper = mount(
      defineComponent({
        setup() {
          sign = useHangingSign(active, limit, anchor)
          return () =>
            h('a', {
              href: 'https://example.com',
              onPointerdown: sign.onPointerDown,
              onPointermove: sign.onPointerMove,
              onPointerup: sign.onPointerUp,
              onClick: sign.onClick,
            })
        },
      }),
    )
    Object.assign(wrapper.element, {
      setPointerCapture: vi.fn(),
      hasPointerCapture: () => true,
      releasePointerCapture: releaseCapture,
    })
    function pointer(type: string, x: number) {
      const event = new MouseEvent(type, {
        clientX: x,
        clientY: 200,
        button: 0,
        bubbles: true,
        cancelable: true,
      })
      Object.defineProperty(event, 'pointerId', { value: 1 })
      wrapper.element.dispatchEvent(event)
    }
    let preventedBySign = false
    wrapper.element.addEventListener('click', (event: Event) => {
      preventedBySign = event.defaultPrevented
      event.preventDefault()
    })
    function click(detail = 1) {
      const event = new MouseEvent('click', { bubbles: true, cancelable: true, detail })
      wrapper.element.dispatchEvent(event)
      return preventedBySign
    }
    return {
      wrapper,
      active,
      pointer,
      click,
      get sign() {
        return sign!
      },
    }
  }

  it('超过 6px 的拖动取消外链，普通点击和键盘激活可用', () => {
    const test = setup()
    test.pointer('pointerdown', 200)
    test.pointer('pointermove', 230)
    expect(test.sign.angle.value).not.toBe(0)
    test.pointer('pointerup', 230)
    expect(test.click()).toBe(true)
    test.pointer('pointerdown', 200)
    test.pointer('pointermove', 204)
    test.pointer('pointerup', 204)
    expect(test.click()).toBe(false)
    expect(test.click(0)).toBe(false)
    test.wrapper.unmount()
  })

  it('隐藏和卸载取消 RAF、释放指针捕获并移除媒体监听', async () => {
    const test = setup()
    test.pointer('pointerdown', 200)
    test.pointer('pointermove', 230)
    test.pointer('pointerup', 230)
    test.active.value = false
    await nextTick()
    expect(cancelFrame).toHaveBeenCalledWith(42)
    expect(test.sign.angle.value).toBe(0)
    test.active.value = true
    await nextTick()
    test.pointer('pointerdown', 200)
    test.wrapper.unmount()
    expect(releaseCapture).toHaveBeenCalledWith(1)
    expect(removeMotionListener).toHaveBeenCalledWith('change', expect.any(Function))
  })

  it('减少动态效果时释放立即归位且不调度回摆', () => {
    reduce = true
    const test = setup()
    test.pointer('pointerdown', 200)
    test.pointer('pointermove', 230)
    expect(test.sign.angle.value).not.toBe(0)
    test.pointer('pointerup', 230)
    expect(test.sign.angle.value).toBe(0)
    expect(requestAnimationFrame).not.toHaveBeenCalled()
    test.wrapper.unmount()
  })
})
