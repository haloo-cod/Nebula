import { describe, expect, it } from 'vitest'
import { buildSignRope } from './signRope'

describe('柔绳长度与连接点', () => {
  it('弯曲与扩大后的摆动均保持弧长 100px，连接点始终位于绳子末端', () => {
    for (const angle of [-0.7, 0, 0.7]) {
      for (const bend of [-10, 0, 10]) {
        const rope = buildSignRope(angle, bend)
        const points = [...rope.core.matchAll(/[ML](-?[\d.]+),(-?[\d.]+)/g)].map((match) => ({
          x: Number(match[1]),
          y: Number(match[2]),
        }))
        const length = points
          .slice(1)
          .reduce(
            (sum, point, index) =>
              sum + Math.hypot(point.x - points[index].x, point.y - points[index].y),
            0,
          )
        expect(length).toBeCloseTo(100, 2)
        expect(Math.hypot(rope.end.x, rope.end.y)).toBeLessThanOrEqual(100)
        const endpoint = points.at(-1)!
        expect(endpoint.x).toBeCloseTo(rope.end.x, 2)
        expect(endpoint.y).toBeCloseTo(rope.end.y, 2)
      }
    }
  })

  it('静止时中心线完全垂直，没有预设的微弯', () => {
    const rope = buildSignRope(0, 0)
    const horizontalPositions = [...rope.core.matchAll(/[ML](-?[\d.]+),/g)].map((match) =>
      Number(match[1]),
    )
    expect(horizontalPositions.every((x) => x === 0)).toBe(true)
    expect(rope.end).toEqual({ x: 0, y: 100 })
  })
})
