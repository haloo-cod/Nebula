import { computed, onMounted, onUnmounted, ref, watch, type Ref } from 'vue'
import { SIGN_CARD_ANGLE_RATIO, stepSignPendulum } from '@/utils/hangingSign'
import { buildSignRope } from '@/utils/signRope'

/** 指针拖动固定长度悬挂牌，松手后保留角速度并阻尼回摆。 */
export function useHangingSign(
  active: Ref<boolean>,
  limit: Ref<number>,
  anchor: Ref<{ x: number; y: number }>,
) {
  const angle = ref(0)
  const cardAngle = ref(0)
  const bend = ref(0)
  const rope = computed(() => buildSignRope(angle.value, bend.value))
  const dragging = ref(false)
  const reducedMotion = ref(false)
  let velocity = 0
  let cardVelocity = 0
  let bendVelocity = 0
  let frame = 0
  let previousTime = 0
  let pointerId: number | null = null
  let captured: HTMLElement | null = null
  let startX = 0
  let startY = 0
  let grabAngle = 0
  let startAngle = 0
  let lastMoveTime = 0
  let moved = false
  let suppressClick = false
  let motionQuery: MediaQueryList | undefined

  function stop() {
    if (frame) cancelAnimationFrame(frame)
    frame = 0
  }

  function reset() {
    stop()
    if (pointerId !== null && captured?.hasPointerCapture(pointerId))
      captured.releasePointerCapture(pointerId)
    pointerId = null
    captured = null
    dragging.value = false
    angle.value = 0
    cardAngle.value = 0
    bend.value = 0
    velocity = 0
    cardVelocity = 0
    bendVelocity = 0
    moved = false
    suppressClick = false
  }

  function tick(time: number) {
    frame = 0
    if (!active.value || reducedMotion.value) return
    const dt = Math.min((time - previousTime) / 1000, 0.032)
    previousTime = time
    if (!dragging.value) {
      const next = stepSignPendulum(angle.value, velocity, dt, limit.value)
      angle.value = next.angle
      velocity = next.velocity
    }
    // 牌子有独立转动惯性，绳子受拉扯后弯曲并逐渐回正。
    const targetCardAngle = angle.value * SIGN_CARD_ANGLE_RATIO
    const cardLimit = limit.value * SIGN_CARD_ANGLE_RATIO
    cardVelocity += ((targetCardAngle - cardAngle.value) * 145 - cardVelocity * 17) * dt
    const nextCardAngle = cardAngle.value + cardVelocity * dt
    cardAngle.value = Math.max(-cardLimit, Math.min(cardLimit, nextCardAngle))
    if (cardAngle.value !== nextCardAngle) cardVelocity = 0
    const movingVelocity = dragging.value && time - lastMoveTime > 80 ? 0 : velocity
    const targetBend = Math.max(
      -10,
      Math.min(10, -movingVelocity * 2.2 + (targetCardAngle - cardAngle.value) * 24),
    )
    bendVelocity += ((targetBend - bend.value) * 95 - bendVelocity * 15) * dt
    bend.value = Math.max(-10, Math.min(10, bend.value + bendVelocity * dt))
    if (
      !dragging.value &&
      Math.abs(angle.value) < 0.0005 &&
      Math.abs(velocity) < 0.003 &&
      Math.abs(cardAngle.value) < 0.001 &&
      Math.abs(cardVelocity) < 0.003 &&
      Math.abs(bend.value) < 0.01 &&
      Math.abs(bendVelocity) < 0.03
    ) {
      angle.value = 0
      cardAngle.value = 0
      bend.value = 0
      velocity = 0
      cardVelocity = 0
      bendVelocity = 0
      return
    }
    frame = requestAnimationFrame(tick)
  }

  function pointerAngle(event: PointerEvent) {
    // CSS 正角度向左摆，保持向下的固定长度绳子方向。
    return Math.atan2(anchor.value.x - event.clientX, event.clientY - anchor.value.y)
  }

  function onPointerDown(event: PointerEvent) {
    if (!active.value || event.button !== 0 || pointerId !== null) return
    stop()
    pointerId = event.pointerId
    captured = event.currentTarget instanceof HTMLElement ? event.currentTarget : null
    captured?.setPointerCapture(event.pointerId)
    startX = event.clientX
    startY = event.clientY
    grabAngle = pointerAngle(event)
    startAngle = angle.value
    lastMoveTime = event.timeStamp
    velocity = 0
    moved = false
    suppressClick = false
    dragging.value = true
    if (!reducedMotion.value) {
      previousTime = performance.now()
      frame = requestAnimationFrame(tick)
    }
  }

  function onPointerMove(event: PointerEvent) {
    if (event.pointerId !== pointerId) return
    if (Math.hypot(event.clientX - startX, event.clientY - startY) > 6) moved = true
    if (!moved) return
    const next = Math.max(
      -limit.value,
      Math.min(limit.value, startAngle + pointerAngle(event) - grabAngle),
    )
    const dt = Math.max((event.timeStamp - lastMoveTime) / 1000, 0.008)
    velocity = Math.max(-4, Math.min(4, (next - angle.value) / dt))
    angle.value = next
    if (reducedMotion.value) cardAngle.value = next * SIGN_CARD_ANGLE_RATIO
    lastMoveTime = event.timeStamp
    event.preventDefault()
  }

  function onPointerUp(event: PointerEvent) {
    if (event.pointerId !== pointerId) return
    suppressClick = moved || event.type !== 'pointerup'
    if (event.timeStamp - lastMoveTime > 100) velocity = 0
    const id = pointerId
    pointerId = null
    dragging.value = false
    stop()
    if (captured?.hasPointerCapture(id)) captured.releasePointerCapture(id)
    captured = null
    if (reducedMotion.value) {
      angle.value = 0
      cardAngle.value = 0
      bend.value = 0
      velocity = 0
      cardVelocity = 0
      bendVelocity = 0
    } else if (active.value) {
      previousTime = performance.now()
      frame = requestAnimationFrame(tick)
    }
  }

  function onClick(event: MouseEvent) {
    if (suppressClick && event.detail !== 0) {
      event.preventDefault()
      event.stopPropagation()
    }
    suppressClick = false
  }

  function onMotionChange() {
    reducedMotion.value = motionQuery?.matches ?? false
    if (reducedMotion.value) reset()
  }

  watch(active, (value) => {
    if (!value) reset()
  })
  watch(limit, (value) => {
    angle.value = Math.max(-value, Math.min(value, angle.value))
    const cardLimit = value * SIGN_CARD_ANGLE_RATIO
    cardAngle.value = Math.max(-cardLimit, Math.min(cardLimit, cardAngle.value))
    velocity = 0
    cardVelocity = 0
  })
  onMounted(() => {
    motionQuery = window.matchMedia('(prefers-reduced-motion: reduce)')
    onMotionChange()
    motionQuery.addEventListener('change', onMotionChange)
  })
  onUnmounted(() => {
    reset()
    motionQuery?.removeEventListener('change', onMotionChange)
  })

  return {
    angle,
    cardAngle,
    rope,
    dragging,
    onPointerDown,
    onPointerMove,
    onPointerUp,
    onClick,
    reset,
  }
}
