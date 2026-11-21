import { describe, expect, it, vi } from 'vitest'

vi.hoisted(() => {
  vi.stubEnv('VITE_API_BASE_URL', '')
})

import { resolveUrl } from './client'

describe('资源 URL 解析', () => {
  it('编码原始空格并保留已编码路径，避免图片名双重编码', () => {
    expect(resolveUrl('/uploads/images/a b.png')).toBe('/uploads/images/a%20b.png')
    expect(resolveUrl('/uploads/images/a%20b.png')).toBe('/uploads/images/a%20b.png')
    expect(resolveUrl('/uploads/images/100% done.png')).toBe('/uploads/images/100%25%20done.png')
  })
})
