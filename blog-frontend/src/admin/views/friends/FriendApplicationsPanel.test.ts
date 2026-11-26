import { afterEach, beforeEach, describe, expect, it, vi } from 'vitest'
import { defineComponent, h } from 'vue'
import { flushPromises, mount } from '@vue/test-utils'
import type { VueWrapper } from '@vue/test-utils'
import ElementPlus from 'element-plus'
import type * as ElementPlusExports from 'element-plus'
import type { CommentItem } from '@/api/comments'
import type { FriendApplicationPrivate } from '@/api/friends'
import FriendApplicationsPanel from './FriendApplicationsPanel.vue'

const mocks = vi.hoisted(() => ({
  applications: vi.fn(),
  fetch: vi.fn(),
  post: vi.fn(),
  remove: vi.fn(),
  error: vi.fn(),
  success: vi.fn(),
  confirm: vi.fn(),
}))
vi.mock('@/api/friends', () => ({
  fetchAdminFriendApplications: mocks.applications,
  deleteFriendApplication: vi.fn(),
  reviewFriendApplication: vi.fn(),
  syncFriendsJson: vi.fn(),
}))
vi.mock('@/api/comments', () => ({
  fetchComments: mocks.fetch,
  postComment: mocks.post,
  deleteComment: mocks.remove,
}))
vi.mock('element-plus', async (importOriginal) => ({
  ...(await importOriginal<typeof ElementPlusExports>()),
  ElMessage: { error: mocks.error, success: mocks.success, warning: vi.fn() },
  ElMessageBox: { confirm: mocks.confirm },
}))

/** 只替换抽屉的传送和动画边界，表格、按钮和输入仍由真实 Element Plus 渲染。 */
const Drawer = defineComponent({
  props: { modelValue: Boolean, title: String },
  emits: ['update:modelValue', 'closed'],
  setup(props, { slots, emit }) {
    return () => props.modelValue ? h('section', { class: 'test-discussion-drawer' }, [
      h('h2', props.title),
      slots.default?.(),
      h('button', {
        onClick: () => {
          emit('update:modelValue', false)
          emit('closed')
        },
      }, '关闭讨论'),
    ]) : null
  },
})

function application(id: number): FriendApplicationPrivate {
  return {
    id, name: `站点 ${id}`, url: `https://site-${id}.example.com/`, avatar: '', rss_url: '',
    email: 'private@example.com', user_id: 1, status: 'approved', review_note: '', friend_id: id,
    created_at: '2026-01-01T12:00:00Z', reviewed_at: '2026-01-01T12:00:00Z',
  }
}

function comment(id: number, overrides: Partial<CommentItem> = {}): CommentItem {
  return {
    id, user_id: 1, author: `作者 ${id}`, date: '2026-01-01 12:00', content: `回复正文 ${id}`,
    avatar_color: '#888888', avatar_url: '', can_delete: true, parent_id: null,
    reply_to_author: '', children: [], ...overrides,
  }
}

function thread(id = 1): CommentItem {
  return comment(id, {
    children: Array.from({ length: 5 }, (_, index) =>
      comment(id + index + 1, { parent_id: id, reply_to_author: `作者 ${id}` }),
    ),
  })
}

function button(wrapper: VueWrapper, text: string) {
  const found = wrapper.findAll('button').find((item) => item.text() === text)
  if (!found) throw new Error(`缺少按钮：${text}`)
  return found
}

const wrappers: VueWrapper[] = []
function setup() {
  const wrapper = mount(FriendApplicationsPanel, {
    global: { plugins: [ElementPlus], stubs: { ElDrawer: Drawer, ElDialog: true } },
  })
  wrappers.push(wrapper)
  return wrapper
}

const originalScrollIntoView = Object.getOwnPropertyDescriptor(Element.prototype, 'scrollIntoView')
beforeEach(() => {
  vi.clearAllMocks()
  mocks.applications.mockReset().mockResolvedValue({ items: [application(1), application(2)], total: 2 })
  mocks.fetch.mockReset().mockResolvedValue([thread(), comment(10)])
  mocks.post.mockReset()
  mocks.confirm.mockResolvedValue('confirm')
  vi.stubGlobal('ResizeObserver', class {
    observe = vi.fn()
    unobserve = vi.fn()
    disconnect = vi.fn()
  })
  Element.prototype.scrollIntoView = vi.fn()
})
afterEach(() => {
  wrappers.splice(0).forEach((wrapper) => wrapper.unmount())
  vi.unstubAllGlobals()
  if (originalScrollIntoView) {
    Object.defineProperty(Element.prototype, 'scrollIntoView', originalScrollIntoView)
  } else {
    Reflect.deleteProperty(Element.prototype, 'scrollIntoView')
  }
})

describe('管理端友链讨论线程', () => {
  it('所有根评论可见，每根五条回复默认三条，展开五条后可以收起', async () => {
    const wrapper = setup()
    await flushPromises()
    await button(wrapper, '查看讨论').trigger('click')
    await flushPromises()

    expect(mocks.fetch).toHaveBeenCalledWith('friend-application:1')
    expect(wrapper.findAll('.discussion-table .el-table__row')).toHaveLength(5)
    expect(wrapper.findAll('.discussion-reply-row')).toHaveLength(3)
    expect(wrapper.get('.discussion-list-title').text()).toBe('讨论 (7)')
    const expand = button(wrapper, '展开剩余 2 条回复')
    expect(expand.attributes('aria-expanded')).toBe('false')
    expect(wrapper.find(`[id="${expand.attributes('aria-controls')}"]`).exists()).toBe(true)
    await expand.trigger('click')
    await flushPromises()
    expect(wrapper.findAll('.discussion-reply-row')).toHaveLength(5)
    expect(button(wrapper, '收起回复').attributes('aria-expanded')).toBe('true')
    await button(wrapper, '收起回复').trigger('click')
    await flushPromises()
    expect(wrapper.findAll('.discussion-reply-row')).toHaveLength(3)
    expect(wrapper.findAll('.discussion-table .el-table__row')).toHaveLength(5)
  })

  it('子评论的回复保留实际目标，并在发送成功刷新后展开该线程', async () => {
    const { promise, resolve } = Promise.withResolvers<CommentItem>()
    mocks.post.mockReturnValue(promise)
    const wrapper = setup()
    await flushPromises()
    await button(wrapper, '查看讨论').trigger('click')
    await flushPromises()
    const row = wrapper.findAll('.discussion-table .el-table__row')
      .find((item) => item.text().includes('回复正文 3'))
    const reply = row?.findAll('button').find((item) => item.text() === '回复')
    if (!reply) throw new Error('缺少子评论回复按钮')
    await reply.trigger('click')
    expect(wrapper.get('.reply-target').text()).toContain('@作者 3')
    await wrapper.get('textarea').setValue('回复给第三位作者')
    await button(wrapper, '发送').trigger('click')
    expect(mocks.post).toHaveBeenCalledWith('friend-application:1', '回复给第三位作者', 3)
    expect(wrapper.get('textarea').attributes('disabled')).toBeDefined()

    const newComment = comment(7, { parent_id: 3, reply_to_author: '作者 3', content: '回复给第三位作者' })
    const refreshed = thread()
    refreshed.children.push(newComment)
    mocks.fetch.mockResolvedValue([refreshed, comment(10)])
    resolve(newComment)
    await flushPromises()
    expect(wrapper.findAll('.discussion-reply-row')).toHaveLength(6)
    expect(wrapper.get('.discussion-table').text()).toContain('回复给第三位作者')
    expect(wrapper.get('.discussion-table').text()).toContain('回复 @作者 3')
    expect(wrapper.find('.reply-target').exists()).toBe(false)
    expect(button(wrapper, '收起回复').attributes('aria-expanded')).toBe('true')
  })

  it('关闭再打开抽屉重置展开状态，关闭后旧发送结果不覆盖下一条申请', async () => {
    const { promise, resolve } = Promise.withResolvers<CommentItem>()
    mocks.post.mockReturnValue(promise)
    const wrapper = setup()
    await flushPromises()
    await button(wrapper, '查看讨论').trigger('click')
    await flushPromises()
    await button(wrapper, '展开剩余 2 条回复').trigger('click')
    await flushPromises()
    const row = wrapper.findAll('.discussion-table .el-table__row')
      .find((item) => item.text().includes('回复正文 6'))
    const reply = row?.findAll('button').find((item) => item.text() === '回复')
    if (!reply) throw new Error('缺少第五条回复')
    await reply.trigger('click')
    await wrapper.get('textarea').setValue('旧申请回复')
    await button(wrapper, '发送').trigger('click')
    await button(wrapper, '关闭讨论').trigger('click')
    mocks.fetch.mockResolvedValue([thread(20)])
    const openButtons = wrapper.findAll('button').filter((item) => item.text() === '查看讨论')
    await openButtons[1]!.trigger('click')
    await flushPromises()
    expect(mocks.fetch).toHaveBeenLastCalledWith('friend-application:2')
    expect(wrapper.findAll('.discussion-reply-row')).toHaveLength(3)
    expect(wrapper.find('.reply-target').exists()).toBe(false)
    resolve(comment(7, { content: '旧申请发送结果', parent_id: 6 }))
    await flushPromises()
    expect(wrapper.get('.discussion-table').text()).not.toContain('旧申请发送结果')
    expect(wrapper.findAll('.discussion-reply-row')).toHaveLength(3)
  })
})
