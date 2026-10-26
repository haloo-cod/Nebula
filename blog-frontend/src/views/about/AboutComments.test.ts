import { afterEach, beforeEach, describe, expect, it, vi } from 'vitest'
import { reactive } from 'vue'
import { flushPromises, mount } from '@vue/test-utils'
import type { VueWrapper } from '@vue/test-utils'
import type { CommentItem } from '@/api/comments'
import AboutComments from './AboutComments.vue'

const mocks = vi.hoisted(() => ({
  fetch: vi.fn(),
  post: vi.fn(),
  remove: vi.fn(),
  error: vi.fn(),
  success: vi.fn(),
}))
const auth = reactive({ isLoggedIn: true, user: { id: 1 } })
vi.mock('@/stores/auth', () => ({ useAuthStore: () => auth }))
vi.mock('@/api/comments', () => ({
  fetchComments: mocks.fetch,
  postComment: mocks.post,
  deleteComment: mocks.remove,
}))
vi.mock('@/api/client', () => ({ resolveUrl: (url: string) => url }))
vi.mock('element-plus', () => ({ ElMessage: { error: mocks.error, success: mocks.success } }))

/** 真实两级响应形状，回复中的 parent_id 可指向另一条回复。 */
function comment(id: number, overrides: Partial<CommentItem> = {}): CommentItem {
  return {
    id,
    user_id: 1,
    author: `回复作者 ${id}`,
    date: '2026-01-01 12:00',
    content: `评论正文 ${id}`,
    avatar_color: '#888888',
    avatar_url: '',
    parent_id: null,
    reply_to_author: '',
    can_delete: true,
    children: [],
    ...overrides,
  }
}

function thread(rootId = 1): CommentItem {
  return comment(rootId, {
    author: '根作者',
    children: Array.from({ length: 5 }, (_, index) =>
      comment(rootId + index + 1, { parent_id: rootId, reply_to_author: '根作者' }),
    ),
  })
}

const wrappers: VueWrapper[] = []
function setup() {
  const wrapper = mount(AboutComments, {
    props: { pageKey: 'about' },
    global: { stubs: { RouterLink: true }, mocks: { $route: { fullPath: '/about' } } },
  })
  wrappers.push(wrapper)
  return wrapper
}

beforeEach(() => {
  vi.clearAllMocks()
  mocks.fetch.mockReset().mockResolvedValue([
    thread(),
    ...Array.from({ length: 4 }, (_, index) => comment(index + 10)),
  ])
  mocks.post.mockReset()
  mocks.remove.mockReset().mockResolvedValue(undefined)
  auth.isLoggedIn = true
  auth.user = { id: 1 }
})
afterEach(() => wrappers.splice(0).forEach((wrapper) => wrapper.unmount()))

describe('评论线程折叠和真实回复目标', () => {
  it('保留全部根评论，五条回复默认显示三条，可展开五条并收起到三条', async () => {
    const wrapper = setup()
    await flushPromises()

    expect(wrapper.findAll('.comments-list > .comment-item')).toHaveLength(5)
    expect(wrapper.findAll('.comment-item--child')).toHaveLength(3)
    expect(wrapper.get('.comments-title').text()).toBe('评论 (10)')
    const toggle = wrapper.get('.comment-thread-toggle')
    expect(toggle.text()).toBe('展开剩余 2 条回复')
    expect(toggle.attributes('aria-expanded')).toBe('false')
    const controlledId = toggle.attributes('aria-controls')
    expect(wrapper.find(`[id="${controlledId}"]`).exists()).toBe(true)

    await toggle.trigger('click')
    expect(wrapper.findAll('.comment-item--child')).toHaveLength(5)
    expect(toggle.attributes('aria-expanded')).toBe('true')
    expect(toggle.text()).toBe('收起回复')
    await toggle.trigger('click')
    expect(wrapper.findAll('.comment-item--child')).toHaveLength(3)
    expect(wrapper.findAll('.comments-list > .comment-item')).toHaveLength(5)
  })

  it('回复子项提交实际子项 ID，成功后平铺插入原线程并自动展开', async () => {
    const { promise, resolve: resolvePost } = Promise.withResolvers<CommentItem>()
    mocks.post.mockReturnValue(promise)
    const wrapper = setup()
    await flushPromises()
    const clickedReply = wrapper.findAll('.comment-item--child')[1]!
    await clickedReply.get('.comment-reply-btn').trigger('click')
    expect(wrapper.get('.comments-replying-to').text()).toContain('@回复作者 3')
    const input = wrapper.get('input[aria-label="评论内容"]')
    expect(input.attributes('placeholder')).toContain('@回复作者 3')
    await input.setValue('发送给子评论')
    await wrapper.get('.comments-submit').trigger('click')
    expect(mocks.post).toHaveBeenCalledWith('about', '发送给子评论', 3)
    expect(input.attributes('disabled')).toBeDefined()
    expect(wrapper.get('.comment-thread-toggle').attributes('disabled')).toBeDefined()

    resolvePost(comment(7, {
      content: '发送给子评论', parent_id: 3, reply_to_author: '回复作者 3', author: '当前账户',
    }))
    await flushPromises()
    expect(wrapper.findAll('.comments-list > .comment-item')).toHaveLength(5)
    const replies = wrapper.findAll('.comment-item--child')
    expect(replies).toHaveLength(6)
    expect(replies[5]!.text()).toContain('发送给子评论')
    expect(replies[5]!.text()).toContain('回复 @回复作者 3')
    expect(wrapper.get('.comment-thread-toggle').attributes('aria-expanded')).toBe('true')
    expect(wrapper.find('.comments-replying-to').exists()).toBe(false)
    expect((input.element as HTMLInputElement).value).toBe('')
    await wrapper.get('.comment-thread-toggle').trigger('click')
    expect(wrapper.findAll('.comment-item--child')).toHaveLength(3)
  })

  it('切换页面清空折叠、草稿和目标，旧页面的发帖结果不会插入新页面', async () => {
    const { promise, resolve: resolvePost } = Promise.withResolvers<CommentItem>()
    mocks.post.mockReturnValue(promise)
    const wrapper = setup()
    await flushPromises()
    await wrapper.get('.comment-thread-toggle').trigger('click')
    await wrapper.findAll('.comment-item--child')[4]!.get('.comment-reply-btn').trigger('click')
    await wrapper.get('input').setValue('旧页面草稿')
    await wrapper.get('.comments-submit').trigger('click')
    mocks.fetch.mockResolvedValue([thread(20)])
    await wrapper.setProps({ pageKey: 'post:new-context' })
    await flushPromises()

    expect(mocks.fetch).toHaveBeenLastCalledWith('post:new-context')
    expect(wrapper.findAll('.comment-item--child')).toHaveLength(3)
    expect(wrapper.get('.comment-thread-toggle').attributes('aria-expanded')).toBe('false')
    expect(wrapper.find('.comments-replying-to').exists()).toBe(false)
    expect((wrapper.get('input').element as HTMLInputElement).value).toBe('')
    resolvePost(comment(7, { content: '旧页面发送结果', parent_id: 6 }))
    await flushPromises()
    expect(wrapper.text()).not.toContain('旧页面发送结果')
    expect(wrapper.findAll('.comment-item--child')).toHaveLength(3)
  })

  it('加载失败可重试，发送失败保留内容与目标而不丢失回复', async () => {
    mocks.fetch.mockRejectedValueOnce(new Error('评论暂时不可用'))
    const wrapper = setup()
    await flushPromises()
    expect(wrapper.get('[role="alert"]').text()).toContain('评论暂时不可用')
    expect(wrapper.get('.comments-submit').attributes('disabled')).toBeDefined()
    await wrapper.get('.comments-retry').trigger('click')
    await flushPromises()
    expect(wrapper.findAll('.comment-item--child')).toHaveLength(3)
    await wrapper.findAll('.comment-item--child')[0]!.get('.comment-reply-btn').trigger('click')
    await wrapper.get('input').setValue('保留这条回复')
    mocks.post.mockRejectedValueOnce(new Error('发送失败，请重试'))
    await wrapper.get('.comments-submit').trigger('click')
    await flushPromises()
    expect(mocks.error).toHaveBeenCalledWith('发送失败，请重试')
    expect((wrapper.get('input').element as HTMLInputElement).value).toBe('保留这条回复')
    expect(wrapper.get('.comments-replying-to').text()).toContain('@回复作者 2')
    expect(wrapper.findAll('.comment-item--child')).toHaveLength(3)
    expect(wrapper.get('.comments-submit').attributes('disabled')).toBeUndefined()
  })
})
