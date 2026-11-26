import { afterEach, beforeEach, describe, expect, it, vi } from 'vitest'
import { defineComponent, reactive } from 'vue'
import { flushPromises, mount } from '@vue/test-utils'
import PostView from './post/post.vue'
import ProjectView from './gallery/project.vue'
import ImagesView from './images/images.vue'
import { fetchPost } from '@/api/posts'
import { fetchGalleryProject } from '@/api/gallery'
import { fetchAlbumDetail, fetchAlbums } from '@/api/albums'
import { getPost, renderMarkdown, renderPost } from '@/data/posts'
import { getGalleryProject, renderGalleryProject } from '@/data/gallery'
import type { Album } from '@/types'
import type { PostDetail } from '@/api/posts'
import type { GalleryDetail } from '@/api/gallery'
import type * as VueRouter from 'vue-router'

vi.mock('vue-router', async (importOriginal) => ({
  ...(await importOriginal<typeof VueRouter>()),
  useRoute: () => route,
  useRouter: () => ({ push: vi.fn() }),
}))
vi.mock('@/api/posts', () => ({ fetchPost: vi.fn() }))
vi.mock('@/api/gallery', () => ({ fetchGalleryProject: vi.fn() }))
vi.mock('@/api/albums', () => ({ fetchAlbums: vi.fn(), fetchAlbumDetail: vi.fn() }))
vi.mock('@/data/posts', () => ({
  getPost: vi.fn(),
  renderPost: vi.fn(),
  renderMarkdown: vi.fn(),
}))
vi.mock('@/data/gallery', () => ({
  getGalleryProject: vi.fn(),
  renderGalleryProject: vi.fn(),
}))
vi.mock('@/views/about/AboutComments.vue', () => ({
  default: { props: ['pageKey'], template: '<div class="comments">{{ pageKey }}</div>' },
}))
vi.mock('@/components/panels/GlassPanel.vue', () => ({
  default: { template: '<div><slot /></div>' },
}))

const route = reactive({ params: { slug: 'older' }, path: '/post/older' })

function deferred<T>() {
  return Promise.withResolvers<T>()
}

// 两种详情使用相同的正文测试输入，补全各自 API 的必填字段。
function detail(slug: string) {
  return {
    id: 1, slug, title: `${slug} title`, description: '', date: '2026-10-26',
    cover_url: '', category: '', tags: [], is_draft: false, is_pinned: false,
    status: '完成', year: '2026', is_featured: false,
    content_md: `${slug} body`, content_html: '', created_at: '', updated_at: '',
  }
}

function fallback(slug: string) {
  return {
    slug, title: `${slug} local`, description: '', date: '2026-10-26', cover: '',
    category: '', tags: [], draft: false, pinned: false, content: `${slug} local body`,
    status: '完成', year: '2026', featured: false,
  }
}

const detailCases = [
  {
    name: '文章', component: PostView, fetch: vi.mocked(fetchPost),
    getFallback: vi.mocked(getPost), renderFallback: vi.mocked(renderPost),
    bodySelector: '.prose', loadingText: '加载中...',
  },
  {
    name: '项目', component: ProjectView, fetch: vi.mocked(fetchGalleryProject),
    getFallback: vi.mocked(getGalleryProject), renderFallback: vi.mocked(renderGalleryProject),
    bodySelector: '.markdown-body', loadingText: '文档加载中...',
  },
]

beforeEach(() => {
  vi.resetAllMocks()
  route.params.slug = 'older'
  vi.mocked(renderMarkdown).mockImplementation(async (markdown) => `<p>${markdown}</p>`)
  vi.mocked(getPost).mockReturnValue(null)
  vi.mocked(getGalleryProject).mockReturnValue(null)
  vi.mocked(renderPost).mockResolvedValue(null)
  vi.mocked(renderGalleryProject).mockResolvedValue(null)
  vi.stubGlobal('scrollTo', vi.fn())
})
afterEach(() => vi.unstubAllGlobals())

describe.each(detailCases)('$name详情请求生命周期', (testCase) => {
  function open() {
    return mount(testCase.component, { global: { stubs: { RouterLink: true } } })
  }

  it('旧请求成功不能结束新请求的加载或覆盖新内容', async () => {
    const oldRequest = deferred<PostDetail & GalleryDetail>()
    const latestRequest = deferred<PostDetail & GalleryDetail>()
    testCase.fetch.mockReturnValueOnce(oldRequest.promise).mockReturnValueOnce(latestRequest.promise)
    const wrapper = open()
    route.params.slug = 'latest'
    await flushPromises()
    oldRequest.resolve(detail('older'))
    await flushPromises()
    expect(wrapper.text()).toContain(testCase.loadingText)
    expect(wrapper.text()).not.toContain('older title')
    latestRequest.resolve(detail('latest'))
    await flushPromises()
    expect(wrapper.text()).toContain('latest title')
    expect(wrapper.get(testCase.bodySelector).html()).toContain('latest body')
    if (testCase.name === '文章') expect(wrapper.get('.comments').text()).toBe('post:latest')
    wrapper.unmount()
  })

  it('旧请求失败不触发 fallback，也不能清除最新加载状态', async () => {
    const oldRequest = deferred<PostDetail & GalleryDetail>()
    const latestRequest = deferred<PostDetail & GalleryDetail>()
    testCase.fetch.mockReturnValueOnce(oldRequest.promise).mockReturnValueOnce(latestRequest.promise)
    const wrapper = open()
    route.params.slug = 'latest'
    await flushPromises()
    oldRequest.reject(new Error('old offline'))
    await flushPromises()
    expect(testCase.getFallback).not.toHaveBeenCalled()
    expect(wrapper.text()).toContain(testCase.loadingText)
    latestRequest.resolve(detail('latest'))
    await flushPromises()
    expect(wrapper.text()).toContain('latest title')
    wrapper.unmount()
  })

  it('旧 Markdown 渲染完成不能覆盖已显示的新正文', async () => {
    const oldMarkdown = deferred<string>()
    testCase.fetch.mockImplementation(async (slug) => detail(slug))
    vi.mocked(renderMarkdown).mockImplementation((markdown) =>
      markdown === 'older body' ? oldMarkdown.promise : Promise.resolve(`<p>${markdown}</p>`),
    )
    const wrapper = open()
    await flushPromises()
    route.params.slug = 'latest'
    await flushPromises()
    oldMarkdown.resolve('<p>older rendered late</p>')
    await flushPromises()
    expect(wrapper.text()).toContain('latest title')
    expect(wrapper.get(testCase.bodySelector).html()).toContain('latest body')
    expect(wrapper.text()).not.toContain('older rendered late')
    wrapper.unmount()
  })

  it('旧 fallback 失败不能为最新内容设置错误', async () => {
    const oldFallback = deferred<string>()
    testCase.fetch.mockRejectedValueOnce(new Error('offline')).mockResolvedValueOnce(detail('latest'))
    testCase.getFallback.mockReturnValue(fallback('older'))
    testCase.renderFallback.mockReturnValueOnce(oldFallback.promise)
    const wrapper = open()
    await flushPromises()
    route.params.slug = 'latest'
    await flushPromises()
    oldFallback.reject(new Error('local markdown failed'))
    await flushPromises()
    expect(wrapper.find('[role="alert"]').exists()).toBe(false)
    expect(wrapper.text()).toContain('latest title')
    expect(wrapper.get(testCase.bodySelector).html()).toContain('latest body')
    wrapper.unmount()
  })

  it('旧 fallback 成功不能覆盖新文章或项目', async () => {
    const oldFallback = deferred<string>()
    testCase.fetch.mockRejectedValueOnce(new Error('offline')).mockResolvedValueOnce(detail('latest'))
    testCase.getFallback.mockReturnValue(fallback('older'))
    testCase.renderFallback.mockReturnValueOnce(oldFallback.promise)
    const wrapper = open()
    await flushPromises()
    route.params.slug = 'latest'
    await flushPromises()
    oldFallback.resolve('<p>older local body</p>')
    await flushPromises()
    expect(wrapper.text()).toContain('latest title')
    expect(wrapper.get(testCase.bodySelector).html()).toContain('latest body')
    expect(wrapper.text()).not.toContain('older local body')
    wrapper.unmount()
  })

  it('最新 fallback 错误显示错误并结束加载', async () => {
    testCase.fetch.mockRejectedValue(new Error('offline'))
    testCase.getFallback.mockReturnValue(fallback('older'))
    testCase.renderFallback.mockRejectedValue(new Error('invalid markdown'))
    const wrapper = open()
    await flushPromises()
    expect(wrapper.get('[role="alert"]').text()).toContain('加载失败')
    expect(wrapper.text()).not.toContain(testCase.loadingText)
    wrapper.unmount()
  })

  it('卸载后失败不再读取或渲染 fallback', async () => {
    const request = deferred<PostDetail & GalleryDetail>()
    testCase.fetch.mockReturnValueOnce(request.promise)
    const wrapper = open()
    wrapper.unmount()
    request.reject(new Error('late offline'))
    await flushPromises()
    expect(testCase.getFallback).not.toHaveBeenCalled()
    expect(testCase.renderFallback).not.toHaveBeenCalled()
  })
})

function album(id: string): Album {
  return {
    id, title: `album ${id}`, description: '', cover: '', date: '2026-10-26',
    orientation: 'landscape', photos: [],
  }
}

const AlbumCardStub = defineComponent({
  props: ['album'], emits: ['open'],
  template: '<button class="album-card" @click="$emit(\'open\', album)">{{ album.title }}</button>',
})

describe('相册详情生命周期', () => {
  function open() {
    vi.mocked(fetchAlbums).mockResolvedValue([album('1'), album('2')])
    return mount(ImagesView, { global: { stubs: { RouterLink: true, AlbumCard: AlbumCardStub } } })
  }

  it('关闭相册后迟到的详情不会重新打开', async () => {
    const first = deferred<Album>()
    const second = deferred<Album>()
    vi.mocked(fetchAlbumDetail).mockReturnValueOnce(first.promise).mockReturnValueOnce(second.promise)
    const wrapper = open()
    await flushPromises()
    await wrapper.findAll('.album-card')[0]!.trigger('click')
    await wrapper.get('.album-detail__back').trigger('click')
    first.resolve({ ...album('1'), photos: [{ url: '/first.jpg' }] })
    await flushPromises()
    expect(wrapper.find('.album-detail').exists()).toBe(false)
    expect(wrapper.findAll('.album-card')).toHaveLength(2)
    await wrapper.findAll('.album-card')[1]!.trigger('click')
    second.resolve({ ...album('2'), photos: [{ url: '/second.jpg' }] })
    await flushPromises()
    expect(wrapper.get('h1').text()).toBe('album 2')
    expect(wrapper.get('.photo-item img').attributes('src')).toBe('/second.jpg')
    wrapper.unmount()
  })

  it('已关闭相册的失败不能清除另一相册的加载状态', async () => {
    const first = deferred<Album>()
    const second = deferred<Album>()
    vi.mocked(fetchAlbumDetail).mockReturnValueOnce(first.promise).mockReturnValueOnce(second.promise)
    const wrapper = open()
    await flushPromises()
    await wrapper.findAll('.album-card')[0]!.trigger('click')
    await wrapper.get('.album-detail__back').trigger('click')
    await wrapper.findAll('.album-card')[1]!.trigger('click')
    first.reject(new Error('old failure'))
    await flushPromises()
    expect(wrapper.get('[role="status"]').text()).toBe('照片加载中...')
    expect(wrapper.find('[role="alert"]').exists()).toBe(false)
    second.resolve(album('2'))
    await flushPromises()
    expect(wrapper.text()).toContain('暂无照片')
    wrapper.unmount()
  })
})
