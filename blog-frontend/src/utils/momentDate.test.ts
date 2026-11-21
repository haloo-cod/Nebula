import { describe, expect, it } from 'vitest'
import { formatMomentDate, formatMomentRelativeTime, parseMomentDate } from './momentDate'

describe('说说时间', () => {
  it('将 UTC 和迁移前无时区时间都转换为上海时间', () => {
    expect(formatMomentDate('2026-11-21T19:15:41Z')).toBe('2026-11-22 03:15:41')
    expect(formatMomentDate('2026-11-21T19:15:41')).toBe('2026-11-22 03:15:41')
  })

  it('尊重显式偏移量，并为无效日期回退原始字符串', () => {
    expect(formatMomentDate('2026-11-21T19:15:41+08:00')).toBe('2026-11-21 19:15:41')
    expect(formatMomentDate('not-a-date')).toBe('not-a-date')
  })

  it('相对时间基于绝对时刻计算', () => {
    const now = Date.parse('2026-11-21T20:15:41Z')
    expect(formatMomentRelativeTime('2026-11-21T19:15:41Z', now)).toBe('1小时前')
    expect(parseMomentDate('2026-11-21T19:15:41')?.toISOString()).toBe('2026-11-21T19:15:41.000Z')
  })
})
