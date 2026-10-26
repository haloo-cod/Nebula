import { describe, expect, it } from 'vitest'
import { getPasswordError } from './password'

describe('密码 UTF-8 长度边界', () => {
  it('接受恰好 72 字节，拒绝相同前缀的超长密码', () => {
    for (const password of ['a'.repeat(72), '汉'.repeat(24), '😀'.repeat(18)]) {
      expect(getPasswordError(password)).toBe('')
      expect(getPasswordError(`${password}x`)).not.toBe('')
    }
  })

  it('最小长度按 Unicode 字符计数，避免七个 emoji 被当成十四个字符', () => {
    expect(getPasswordError('😀'.repeat(7))).not.toBe('')
    expect(getPasswordError('😀'.repeat(8))).toBe('')
  })
})
