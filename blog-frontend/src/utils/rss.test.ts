import { describe, expect, it } from 'vitest'
import { resolveRssUrl } from './rss'

describe('RSS 订阅地址', () => {
  it('同域入口生成可复制的完整地址，静态自动发现保留相对地址', () => {
    expect(resolveRssUrl('', '', 'https://blog.example.com')).toBe(
      'https://blog.example.com/api/v1/rss.xml',
    )
    expect(resolveRssUrl()).toBe('/api/v1/rss.xml')
  })

  it('跨域开发和生产使用现有 API 基址，清除多余尾斜杠', () => {
    expect(resolveRssUrl(' ', 'http://localhost:8000///', 'http://localhost:5173')).toBe(
      'http://localhost:8000/api/v1/rss.xml',
    )
  })

  it('自定义地址同时覆盖可见入口的默认值，并完整保留参数', () => {
    expect(
      resolveRssUrl(' https://feeds.example.com/rss?a=1&b=2 ', 'https://api.example.com'),
    ).toBe('https://feeds.example.com/rss?a=1&b=2')
  })
})
