import { describe, expect, it } from 'vitest'
import {
  buildStaticUniformKey,
  countActiveTrailPoints,
  shouldBlurBackground,
} from './rendererMetrics'

describe('liquid glass renderer metrics helpers', () => {
  it('only enables blur for positive radius', () => {
    expect(shouldBlurBackground(0)).toBe(false)
    expect(shouldBlurBackground(0.5)).toBe(true)
  })

  it('counts active trail points', () => {
    expect(
      countActiveTrailPoints([
        [0, 0, 0.2, 1],
        [0, 0, 1, 1],
        [0, 0, 0.4, 0],
      ]),
    ).toBe(1)
  })

  it('keeps array values in the static key', () => {
    expect(buildStaticUniformKey([1, [0.2, 0.3]])).toBe('1|0.2,0.3')
  })
})
