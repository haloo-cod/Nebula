import { SIGN_ROPE_LENGTH } from './hangingSign'

/** 恒定弧长的柔绳中心线和连接点。 */
export interface SignRopeGeometry {
  core: string
  end: { x: number; y: number }
}

/** 生成柔绳，按实际弧长归一化；仅在运动时弯曲，静止时垂直。 */
export function buildSignRope(angle: number, bend: number): SignRopeGeometry {
  const count = 64
  const points = Array.from({ length: count + 1 }, (_, index) => ({
    x: bend * Math.sin((Math.PI * index) / count),
    y: (SIGN_ROPE_LENGTH * index) / count,
  }))
  let arcLength = 0
  for (let index = 1; index <= count; index++) {
    arcLength += Math.hypot(
      points[index].x - points[index - 1].x,
      points[index].y - points[index - 1].y,
    )
  }
  const scale = SIGN_ROPE_LENGTH / arcLength
  const c = Math.cos(angle),
    s = Math.sin(angle)
  const centerline = points.map(({ x, y }) => ({
    x: (x * c - y * s) * scale,
    y: (x * s + y * c) * scale,
  }))
  const toPath = (path: Array<{ x: number; y: number }>) =>
    path
      .map((point, index) => `${index ? 'L' : 'M'}${point.x.toFixed(3)},${point.y.toFixed(3)}`)
      .join(' ')
  return { core: toPath(centerline), end: centerline[count] }
}
