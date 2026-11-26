import { afterEach, beforeEach, describe, expect, it, vi } from 'vitest'
import { flushPromises, mount } from '@vue/test-utils'
import PostCarousel from './PostCarousel.vue'
import MomentCarousel from './MomentCarousel.vue'
import Carousel from './Carousel.vue'
import { fetchPosts } from '@/api/posts'
import { fetchMoments } from '@/api/moments'
import { fetchCarouselSlides } from '@/api/carousel'
import { getPosts } from '@/data/posts'
import type { Post, Moment } from '@/types'
import type { PostListItem } from '@/api/posts'
import type * as PostApi from '@/api/posts'

vi.mock('vue-router', () => ({ useRouter: () => ({ push: vi.fn() }) }))
vi.mock('@/api/posts', async (importOriginal) => ({
  ...(await importOriginal<typeof PostApi>()), fetchPosts: vi.fn(),
}))
vi.mock('@/api/moments', () => ({ fetchMoments: vi.fn() }))
vi.mock('@/api/carousel', () => ({ fetchCarouselSlides: vi.fn() }))
vi.mock('@/data/posts', () => ({ getPosts: vi.fn() }))

const localPosts: Post[] = ['first', 'second'].map((slug) => ({
  slug, title: slug, description: '', date: '2026-10-26', cover: '', category: '', tags: [],
  draft: false, pinned: false, content: '',
}))
const postItems: PostListItem[] = localPosts.map((post, index) => ({
  id: index + 1, slug: post.slug, title: post.title, description: '', date: post.date,
  cover_url: '', category: '', tags: [], is_draft: false, is_pinned: false, created_at: '',
}))
const momentItems: Moment[] = [1, 2].map((id) => ({
  id, date: '2026-10-26T12:00:00Z', content: `moment ${id}`, tags: [], images: [], likes: 0,
}))

beforeEach(() => {
  vi.resetAllMocks()
  vi.useFakeTimers()
  vi.mocked(getPosts).mockReturnValue(localPosts)
})
afterEach(() => {
  vi.clearAllTimers()
  vi.restoreAllMocks()
  vi.useRealTimers()
})

const components = { posts: PostCarousel, moments: MomentCarousel, images: Carousel }

describe('首页轮播资源清理', () => {
  it.each(['posts', 'moments', 'images'] as const)('%s 卸载后迟到的成功不重建 interval', async (kind) => {
    const posts = Promise.withResolvers<{ items: PostListItem[]; total: number }>()
    const moments = Promise.withResolvers<{ items: Moment[]; total: number }>()
    const images = Promise.withResolvers<string[]>()
    vi.mocked(fetchPosts).mockReturnValue(posts.promise)
    vi.mocked(fetchMoments).mockReturnValue(moments.promise)
    vi.mocked(fetchCarouselSlides).mockReturnValue(images.promise)
    const interval = vi.spyOn(window, 'setInterval')
    const wrapper = mount(components[kind])
    wrapper.unmount()
    const callsAfterUnmount = interval.mock.calls.length
    posts.resolve({ items: postItems, total: 2 })
    moments.resolve({ items: momentItems, total: 2 })
    images.resolve(['/first.jpg', '/second.jpg'])
    await flushPromises()
    expect(interval).toHaveBeenCalledTimes(callsAfterUnmount)
  })

  it.each(['posts', 'moments'] as const)('%s 卸载后迟到的失败也不启动 fallback interval', async (kind) => {
    const request = Promise.withResolvers<{ items: PostListItem[] & Moment[]; total: number }>()
    vi.mocked(fetchPosts).mockReturnValue(request.promise)
    vi.mocked(fetchMoments).mockReturnValue(request.promise)
    const interval = vi.spyOn(window, 'setInterval')
    const wrapper = mount(components[kind])
    wrapper.unmount()
    const callsAfterUnmount = interval.mock.calls.length
    request.reject(new Error('late offline'))
    await flushPromises()
    expect(interval).toHaveBeenCalledTimes(callsAfterUnmount)
  })

  it('卸载清理已运行的 interval、过渡 fallback 和轨道事件', async () => {
    vi.mocked(fetchCarouselSlides).mockResolvedValue(['/first.jpg', '/second.jpg'])
    const interval = vi.spyOn(window, 'setInterval')
    const timeout = vi.spyOn(window, 'setTimeout')
    const cancelInterval = vi.spyOn(window, 'clearInterval')
    const cancelTimeout = vi.spyOn(window, 'clearTimeout')
    const wrapper = mount(Carousel)
    await flushPromises()
    const track = wrapper.get('.carousel-track').element
    const removeListener = vi.spyOn(track, 'removeEventListener')
    await wrapper.findAll('.carousel-dot')[1]!.trigger('click')
    const autoplayCall = interval.mock.calls.findLastIndex(([, delay]) => delay === 4000)
    const transitionCall = timeout.mock.calls.findLastIndex(([, delay]) => delay === 600)
    const autoplayHandle = interval.mock.results[autoplayCall]?.value
    const transitionHandle = timeout.mock.results[transitionCall]?.value
    expect(autoplayHandle).toBeDefined()
    expect(transitionHandle).toBeDefined()
    wrapper.unmount()
    expect(cancelInterval).toHaveBeenCalledWith(autoplayHandle)
    expect(cancelTimeout).toHaveBeenCalledWith(transitionHandle)
    const callsAfterUnmount = interval.mock.calls.length
    expect(removeListener).toHaveBeenCalledWith('transitionend', expect.any(Function))
    expect(removeListener).toHaveBeenCalledWith('transitioncancel', expect.any(Function))
    await vi.advanceTimersByTimeAsync(10000)
    expect(interval).toHaveBeenCalledTimes(callsAfterUnmount)
  })
})
