import { beforeEach, describe, expect, it, vi } from 'vitest'
import { createPinia, setActivePinia } from 'pinia'
import { useUIStore } from './ui'
import { fetchBackgrounds, type ApiBgItem } from '@/api/backgrounds'

vi.mock('@/api/backgrounds', () => ({ fetchBackgrounds: vi.fn() }))

const row = (id: number): ApiBgItem => ({
  id,
  url: `/api/v1/files/${id}/media`,
  theme: 'dark',
  device: 'desktop',
  sort_order: 0,
  created_at: '',
  media_type: 'video',
  source_text: `画师${id}`,
  source_url: 'https://example.com',
})

describe('公共背景数据加载', () => {
  beforeEach(() => {
    localStorage.clear()
    setActivePinia(createPinia())
    vi.mocked(fetchBackgrounds).mockReset()
  })

  it('完整映射视频和来源元数据，修改来源及排序后保持当前 ID', async () => {
    vi.mocked(fetchBackgrounds).mockResolvedValue([row(1), row(2)])
    const ui = useUIStore()
    await ui.loadBackgrounds()
    ui.setDarkBg(1)
    vi.mocked(fetchBackgrounds).mockResolvedValue([{ ...row(2), source_text: '更新来源' }, row(1)])
    await ui.loadBackgrounds()
    expect(ui.darkBgIndex).toBe(0)
    expect(ui.currentBackground).toMatchObject({
      id: 2,
      mediaType: 'video',
      sourceText: '更新来源',
      sourceUrl: 'https://example.com',
    })
  })

  it('较旧请求完成后不会覆盖较新的数据', async () => {
    let release: (items: ApiBgItem[]) => void = () => undefined
    const old = new Promise<ApiBgItem[]>((resolve) => {
      release = resolve
    })
    vi.mocked(fetchBackgrounds)
      .mockImplementationOnce(() => old)
      .mockImplementationOnce(() => old)
      .mockImplementationOnce(() => old)
      .mockImplementationOnce(() => old)
      .mockResolvedValue([row(9)])
    const ui = useUIStore()
    const first = ui.loadBackgrounds()
    await ui.loadBackgrounds()
    release([row(1)])
    await first
    expect(ui.currentBackground.id).toBe(9)
    expect(localStorage.getItem('blog-dark-bg-id')).toBe('9')
  })

  it('失败保留已保存 ID，成功空列表清除当前背景和来源', async () => {
    localStorage.setItem('blog-dark-bg-id', '2')
    vi.mocked(fetchBackgrounds).mockRejectedValue(new Error('offline'))
    const ui = useUIStore()
    const error = vi.spyOn(console, 'error').mockImplementation(() => undefined)
    await ui.loadBackgrounds()
    expect(localStorage.getItem('blog-dark-bg-id')).toBe('2')
    vi.mocked(fetchBackgrounds).mockResolvedValue([row(1), row(2)])
    await ui.loadBackgrounds()
    expect(ui.currentBackground.id).toBe(2)
    vi.mocked(fetchBackgrounds).mockResolvedValue([])
    await ui.loadBackgrounds()
    expect(ui.currentBackground.src).toBe('')
    expect(ui.currentBackground.sourceText).toBeUndefined()
    error.mockRestore()
  })
})
