import { afterEach, beforeEach, describe, expect, it, vi } from 'vitest'
import { defineComponent, h, ref } from 'vue'
import { flushPromises, mount, type VueWrapper } from '@vue/test-utils'
import type * as ElementPlus from 'element-plus'
import ImagePickerDialog, { type PickerImage } from './ImagePickerDialog.vue'

const mocks = vi.hoisted(() => ({ get: vi.fn(), upload: vi.fn(), error: vi.fn(), success: vi.fn(), warning: vi.fn() }))
vi.mock('@/api/client', () => ({ api: { get: mocks.get }, resolveUrl: (url: string) => url }))
vi.mock('@/api/images', () => ({ uploadImage: mocks.upload }))
vi.mock('@/admin/composables/useStorageBackend', () => ({
  useStorageBackend: () => ({ storageBackend: ref('local') }),
}))
vi.mock('element-plus', async (importOriginal) => ({
  ...(await importOriginal<typeof ElementPlus>()),
  ElMessage: { error: mocks.error, success: mocks.success, warning: mocks.warning },
}))

/** 模拟真实后端分页响应。 */
interface ImagePage {
  items: PickerImage[]
  total: number
}

const Dialog = defineComponent({
  props: { modelValue: Boolean },
  setup: (props, { slots }) => () => props.modelValue
    ? h('section', [slots.default?.(), slots.footer?.()]) : null,
})
const Input = defineComponent({
  props: { modelValue: String },
  emits: ['update:modelValue', 'clear'],
  setup: (props, { emit }) => () => h('input', {
    value: props.modelValue,
    onInput: (event: Event) => emit('update:modelValue', (event.target as HTMLInputElement).value),
  }),
})
const Button = defineComponent({
  props: { disabled: Boolean },
  setup: (props, { slots }) => () => h('button', { disabled: props.disabled }, slots.default?.()),
})
const Pagination = defineComponent({
  props: { currentPage: Number, pageSize: Number, total: Number, disabled: Boolean },
  emits: ['current-change', 'size-change'],
  setup: (props) => () => h('div', { 'data-total': props.total, 'data-page': props.currentPage }),
})
const Result = defineComponent({
  props: { title: String },
  setup: (props, { slots }) => () => h('div', [props.title, slots.extra?.()]),
})
const Empty = defineComponent({
  props: { description: String },
  setup: (props) => () => h('div', props.description),
})

function image(id: number): PickerImage {
  return {
    id, original_name: `图片-${id}.jpg`, url: `/images/${id}.jpg`, file_size: 100,
    width: 320, height: 240, mime_type: 'image/jpeg', created_at: '2026-01-01T00:00:00Z',
  }
}

describe('图片选择器跨页和请求状态', () => {
  const wrappers: VueWrapper[] = []
  beforeEach(() => {
    vi.clearAllMocks()
    mocks.get.mockImplementation(async (path: string): Promise<ImagePage> => {
      const page = Number(new URL(path, 'http://test').searchParams.get('page'))
      return { items: page === 6 ? [image(125)] : [image(1)], total: 125 }
    })
  })
  afterEach(() => wrappers.splice(0).forEach((wrapper) => wrapper.unmount()))

  function setup(multiple = true) {
    const wrapper = mount(ImagePickerDialog, {
      props: { modelValue: true, multiple },
      global: {
        stubs: {
          ElDialog: Dialog, ElInput: Input, ElButton: Button, ElPagination: Pagination,
          ElResult: Result, ElEmpty: Empty, StorageBackendSelect: true,
        },
        directives: { loading: () => {} },
      },
    })
    wrappers.push(wrapper)
    return wrapper
  }

  async function clickButton(wrapper: VueWrapper, text: string) {
    const button = wrapper.findAll('button').find((item) => item.text().includes(text))
    expect(button).toBeDefined()
    await button!.trigger('click')
  }

  it('125 张图片可翻到第 6 页，确认包含各页已选图片', async () => {
    const wrapper = setup()
    await flushPromises()
    expect(wrapper.findComponent(Pagination).props('total')).toBe(125)
    await wrapper.find('.image-option').trigger('click')
    wrapper.findComponent(Pagination).vm.$emit('current-change', 6)
    await flushPromises()
    expect(mocks.get).toHaveBeenLastCalledWith('/api/v1/images?page=6&page_size=24', true)
    expect(wrapper.find('.image-name').text()).toBe('图片-125.jpg')
    await wrapper.find('.image-option').trigger('click')
    await clickButton(wrapper, '确认选择')
    expect(wrapper.emitted('select-many')?.[0]?.[0]).toEqual([image(1), image(125)])
  })

  it('搜索发送服务端关键词并从第一页开始，翻页保留搜索条件', async () => {
    const wrapper = setup(false)
    await flushPromises()
    wrapper.findComponent(Pagination).vm.$emit('current-change', 6)
    await flushPromises()
    await wrapper.find('input').setValue('  旧图 & 封面  ')
    await clickButton(wrapper, '搜索')
    await flushPromises()
    let params = new URL(mocks.get.mock.calls.at(-1)![0], 'http://test').searchParams
    expect(params.get('page')).toBe('1')
    expect(params.get('keyword')).toBe('旧图 & 封面')
    // 后端可匹配内部文件名；前端不再二次过滤只匹配原文件名。
    expect(wrapper.find('.image-option').exists()).toBe(true)
    wrapper.findComponent(Pagination).vm.$emit('current-change', 2)
    await flushPromises()
    params = new URL(mocks.get.mock.calls.at(-1)![0], 'http://test').searchParams
    expect(params.get('page')).toBe('2')
    expect(params.get('keyword')).toBe('旧图 & 封面')
  })

  it('较早请求晚失败也不覆盖新结果或发出错误提示', async () => {
    const oldRequest = Promise.withResolvers<ImagePage>()
    const newRequest = Promise.withResolvers<ImagePage>()
    mocks.get.mockReturnValueOnce(oldRequest.promise).mockReturnValueOnce(newRequest.promise)
    const wrapper = setup()
    await wrapper.find('input').setValue('最新')
    await clickButton(wrapper, '搜索')
    newRequest.resolve({ items: [image(120)], total: 1 })
    await flushPromises()
    oldRequest.reject(new Error('旧请求失败'))
    await flushPromises()
    expect(wrapper.find('.image-name').text()).toBe('图片-120.jpg')
    expect(wrapper.findComponent(Pagination).props('total')).toBe(1)
    expect(mocks.error).not.toHaveBeenCalled()
  })

  it('真实加载失败显示详情，可手动重载并显示空列表', async () => {
    mocks.get.mockRejectedValueOnce(new Error('图片列表暂不可用'))
    const wrapper = setup()
    await flushPromises()
    expect(wrapper.text()).toContain('图片列表暂不可用')
    expect(mocks.error).toHaveBeenCalledWith('图片列表暂不可用')
    mocks.get.mockResolvedValueOnce({ items: [], total: 0 })
    await clickButton(wrapper, '重新加载')
    await flushPromises()
    expect(wrapper.text()).toContain('暂无可选图片')
    expect(wrapper.findComponent(Result).exists()).toBe(false)
  })

  it('关闭后重新打开清空选择、关键词和页码，并忽略关闭前的响应', async () => {
    const wrapper = setup()
    await flushPromises()
    await wrapper.find('.image-option').trigger('click')
    const stale = Promise.withResolvers<ImagePage>()
    mocks.get.mockReturnValueOnce(stale.promise)
    wrapper.findComponent(Pagination).vm.$emit('current-change', 6)
    await flushPromises()
    await wrapper.setProps({ modelValue: false })
    await wrapper.setProps({ modelValue: true })
    await flushPromises()
    stale.resolve({ items: [image(125)], total: 125 })
    await flushPromises()
    expect(wrapper.findComponent(Pagination).props('currentPage')).toBe(1)
    expect(wrapper.find('input').element.value).toBe('')
    expect(wrapper.find('.image-option').classes()).not.toContain('selected')
    expect(wrapper.find('.image-name').text()).toBe('图片-1.jpg')
    expect(wrapper.text()).toContain('确认选择（0）')
  })
})
