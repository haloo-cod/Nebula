import { beforeEach, describe, expect, it } from 'vitest'
import { ref } from 'vue'
import { createBackgroundSelection } from './backgroundSelection'
import type { BackgroundItem } from '@/data/backgrounds'

const row = (id: number): BackgroundItem => ({
  id,
  src: `/background/${id}`,
  sourceText: `画师${id}`,
})

describe('背景身份选择', () => {
  beforeEach(() => localStorage.clear())

  it('等待 API 数据后迁移旧下标，包括初始空列表', () => {
    localStorage.setItem('test-bg', '1')
    const items = ref<BackgroundItem[]>([])
    const selection = createBackgroundSelection(items, 'test-bg')
    selection.replace([row(10), row(20)])
    expect(items.value[selection.index.value]?.id).toBe(20)
    expect(localStorage.getItem('test-bg-id')).toBe('20')
    selection.replace([row(20), row(10)])
    expect(selection.index.value).toBe(0)
    expect(items.value[selection.index.value]?.sourceText).toBe('画师20')
  })

  it('分别持久化各组，重排保留 ID，删除当前记录回退第一张', () => {
    const items = ref<BackgroundItem[]>([])
    const selection = createBackgroundSelection(items, 'dark')
    selection.replace([row(1), row(2)])
    selection.index.value = 1
    selection.replace([row(2), row(1), row(3)])
    expect(items.value[selection.index.value]?.id).toBe(2)
    selection.replace([row(3), row(1)])
    expect(items.value[selection.index.value]?.id).toBe(3)
    const other = createBackgroundSelection(ref<BackgroundItem[]>([]), 'light')
    other.replace([row(8), row(9)])
    expect(localStorage.getItem('dark-id')).toBe('3')
    expect(localStorage.getItem('light-id')).toBe('8')
    selection.replace([])
    expect(items.value).toEqual([])
    expect(localStorage.getItem('dark-id')).toBeNull()
  })

  it('API 尚未成功加载时静态背景选择不会覆盖服务器 ID', () => {
    localStorage.setItem('test-id', '40')
    const items = ref<BackgroundItem[]>([{ src: 'a' }, { src: 'b' }])
    const selection = createBackgroundSelection(items, 'test')
    selection.index.value = 1
    expect(localStorage.getItem('test-id')).toBe('40')
    expect(localStorage.getItem('test-src')).toBe('b')
    selection.replace([row(30), row(40)])
    expect(items.value[selection.index.value]?.id).toBe(40)
  })

  it('无效旧下标回退第一张，静态资源按地址保持选择', () => {
    localStorage.setItem('test', '99')
    const items = ref<BackgroundItem[]>([{ src: 'a' }, { src: 'b' }])
    const selection = createBackgroundSelection(items, 'test')
    selection.index.value = 1
    items.value.reverse()
    expect(selection.index.value).toBe(0)
    selection.replace([row(6), row(7)])
    expect(items.value[selection.index.value]?.id).toBe(6)
  })
})
