/** 悬挂牌布局及摆动范围。 */
export interface HangingSignLayout {
  anchorX: number
  anchorY: number
  width: number
  height: number
  maxAngle: number
  visible: boolean
}

export const SIGN_ROPE_LENGTH = 100
/** 柔绳摆动时牌子的转角较小，为平移和惯性留出更多空间。 */
export const SIGN_CARD_ANGLE_RATIO = 0.5
const MAX_ANGLE = (40 * Math.PI) / 180

/** 计算独立转动的绳子和牌子的最大横向占用。 */
export function signHorizontalReach(width: number, height: number, angle: number): number {
  const cardAngle = Math.abs(angle) * SIGN_CARD_ANGLE_RATIO
  return (
    SIGN_ROPE_LENGTH * Math.sin(Math.abs(angle)) +
    (width / 2) * Math.cos(cardAngle) +
    height * Math.sin(cardAngle)
  )
}

/** 在真实内容左边界内缩放牌子并限制摆角，保留两侧 16px 间距。 */
export function calculateSignLayout(
  gutter: number,
  anchorY: number,
  viewportHeight: number,
): HangingSignLayout {
  const width = Math.min(240, gutter - 64)
  const height = width * 0.625
  const visible = width >= 144 && anchorY + SIGN_ROPE_LENGTH + height <= viewportHeight - 16
  let low = 0
  let high = MAX_ANGLE
  const available = gutter / 2 - 16
  const verticalAvailable = viewportHeight - 16 - anchorY
  for (let i = 0; i < 24; i++) {
    const mid = (low + high) / 2
    // 牌子与绳子独立转动，使用绳子垂直时的最保守底边。
    const peak = Math.min(mid * SIGN_CARD_ANGLE_RATIO, Math.atan2(width / 2, height))
    const verticalReach = SIGN_ROPE_LENGTH + height * Math.cos(peak) + (width / 2) * Math.sin(peak)
    if (signHorizontalReach(width, height, mid) <= available && verticalReach <= verticalAvailable)
      low = mid
    else high = mid
  }
  return { anchorX: gutter / 2, anchorY, width, height, maxAngle: low, visible }
}

/** 固定长度单摆的一步积分；衰减速度，碰到边界时消除向外速度。 */
export function stepSignPendulum(angle: number, velocity: number, dt: number, limit: number) {
  const nextVelocity = (velocity - 22 * Math.sin(angle) * dt) * Math.exp(-2.6 * dt)
  const rawAngle = angle + nextVelocity * dt
  const nextAngle = Math.max(-limit, Math.min(limit, rawAngle))
  return { angle: nextAngle, velocity: rawAngle === nextAngle ? nextVelocity : 0 }
}
