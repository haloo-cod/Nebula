import { describe, expect, it } from 'vitest'
import {
  calculateSignLayout,
  SIGN_CARD_ANGLE_RATIO,
  signHorizontalReach,
  stepSignPendulum,
} from './hangingSign'
import { backgroundSourceError, isBackgroundSourceUrl } from './backgroundSource'
import { getGlassCanvasOffset } from '@/components/liquid-glass/rendererMetrics'

describe('悬挂牌的空间约束', () => {
  it('宽屏为 240×150，窄留白缩小并始终保留 16px 间距', () => {
    for (const gutter of [208, 230, 300, 410, 800]) {
      const layout = calculateSignLayout(gutter, 64, 900)
      expect(layout.visible).toBe(true)
      expect(layout.width).toBeGreaterThanOrEqual(144)
      expect(layout.width).toBeLessThanOrEqual(240)
      expect(signHorizontalReach(layout.width, layout.height, layout.maxAngle)).toBeLessThanOrEqual(
        gutter / 2 - 16,
      )
      expect(layout.maxAngle).toBeLessThanOrEqual((40 * Math.PI) / 180)
    }
    expect(calculateSignLayout(410, 64, 900)).toMatchObject({ width: 240, height: 150 })
    expect(calculateSignLayout(410, 64, 900).maxAngle).toBeGreaterThan((23 * Math.PI) / 180)
    expect(calculateSignLayout(800, 64, 900).maxAngle).toBeCloseTo((40 * Math.PI) / 180, 6)
    expect(calculateSignLayout(200, 64, 900).visible).toBe(false)
    expect(calculateSignLayout(410, 64, 250).visible).toBe(false)
    const short = calculateSignLayout(800, 64, 335)
    const cardAngle = short.maxAngle * SIGN_CARD_ANGLE_RATIO
    const reach = 100 + 150 * Math.cos(cardAngle) + 120 * Math.sin(cardAngle)
    expect(short.anchorY + reach).toBeLessThanOrEqual(335 - 16)
  })

  it('释放后回到平衡，边界上不继续向外移动', () => {
    let state = { angle: 0.3, velocity: 1.2 }
    for (let i = 0; i < 1200; i++)
      state = stepSignPendulum(state.angle, state.velocity, 1 / 60, 0.4)
    expect(Math.abs(state.angle)).toBeLessThan(0.001)
    expect(Math.abs(state.velocity)).toBeLessThan(0.001)
    expect(stepSignPendulum(0.4, 3, 1 / 60, 0.4)).toEqual({ angle: 0.4, velocity: 0 })
  })

  it('旋转玻璃以实际中心采样，默认零角度保持原位置', () => {
    const rect = { left: 50, top: 100, width: 280, height: 220 }
    expect(getGlassCanvasOffset(rect, 240, 150, 2)).toEqual([100, 200])
    expect(getGlassCanvasOffset(rect, 240, 150, 2, 0.3)).toEqual([140, 270])
  })

  it('来源链接仅接受完整 HTTP(S) 并校验长度', () => {
    expect(isBackgroundSourceUrl('https://example.com/work?a=1')).toBe(true)
    for (const url of [
      'javascript:alert(1)',
      '//example.com',
      'https:example.com',
      'http://',
      'https://example.com/a b',
    ]) {
      expect(isBackgroundSourceUrl(url)).toBe(false)
    }
    expect(backgroundSourceError({ source_text: '字'.repeat(121), source_url: '' })).toBeTruthy()
    expect(backgroundSourceError({ source_text: '画师', source_url: '' })).toBe('')
  })
})
