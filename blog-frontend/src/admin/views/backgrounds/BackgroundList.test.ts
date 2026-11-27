import { afterEach, beforeEach, describe, expect, it, vi } from 'vitest'
import { createPinia, setActivePinia } from 'pinia'
import { flushPromises, mount } from '@vue/test-utils'
import { defineComponent, ref } from 'vue'
import type * as ElementPlus from 'element-plus'
import BackgroundList from './BackgroundList.vue'
import { useUIStore } from '@/stores/ui'
import type { ApiBgItem } from '@/api/backgrounds'

const elementMocks = vi.hoisted(() => ({
  success: vi.fn(),
  warning: vi.fn(),
  error: vi.fn(),
  confirm: vi.fn().mockResolvedValue('confirm'),
}))

vi.mock('element-plus', async (importOriginal) => ({
  ...(await importOriginal<typeof ElementPlus>()),
  ElMessage: {
    success: elementMocks.success,
    warning: elementMocks.warning,
    error: elementMocks.error,
  },
  ElMessageBox: {
    confirm: elementMocks.confirm,
  },
}))

const apiMocks = vi.hoisted(() => ({
  get: vi.fn(),
  post: vi.fn(),
  put: vi.fn(),
  patch: vi.fn(),
  delete: vi.fn(),
}))

vi.mock('@/api/client', () => ({
  api: apiMocks,
  resolveUrl: (url: string) => url,
}))

vi.mock('@/api/files', () => ({
  fetchFiles: vi.fn().mockResolvedValue([]),
}))

const storageBackendRef = ref<'local' | 'r2'>('local')
vi.mock('@/admin/composables/useStorageBackend', () => ({
  useStorageBackend: () => ({ storageBackend: storageBackendRef }),
}))

interface MockBgRow {
  id: number
  url: string
  theme: 'dark' | 'light'
  device: 'desktop' | 'mobile'
  sort_order: number
  created_at: string
  media_type: 'image' | 'video'
  poster_url?: string
  mime_type?: string
  file_size?: number
  source_text: string
  source_url: string
  storage_backend?: 'local' | 'r2'
}

const ElSelectStub = defineComponent({
  name: 'ElSelect',
  props: ['modelValue'],
  emits: ['update:modelValue', 'change'],
  template: `<select class="el-select-stub" :value="modelValue" @change="$emit('update:modelValue', $event.target.value); $emit('change', $event.target.value)"><slot /></select>`,
})

const ElOptionStub = defineComponent({
  name: 'ElOption',
  props: ['label', 'value'],
  template: `<option :value="value">{{ label }}</option>`,
})

const ElButtonStub = defineComponent({
  name: 'ElButton',
  props: ['disabled', 'loading', 'type'],
  emits: ['click'],
  template: `<button type="button" :disabled="disabled" @click="$emit('click', $event)"><slot /></button>`,
})

const ElCheckboxStub = defineComponent({
  name: 'ElCheckbox',
  props: ['modelValue'],
  emits: ['change'],
  template: `<input type="checkbox" class="bg-check-input" :checked="modelValue" @change="$emit('change', $event.target.checked)" />`,
})

const ElDialogStub = defineComponent({
  name: 'ElDialog',
  props: ['modelValue', 'title'],
  emits: ['update:modelValue', 'closed'],
  template: `<div v-if="modelValue" class="el-dialog-stub" :data-title="title"><slot /><slot name="footer" /></div>`,
})

const ElInputStub = defineComponent({
  name: 'ElInput',
  props: ['modelValue', 'placeholder'],
  emits: ['update:modelValue'],
  template: `<input :value="modelValue" :placeholder="placeholder" @input="$emit('update:modelValue', $event.target.value)" />`,
})

const ElRadioGroupStub = defineComponent({
  name: 'ElRadioGroup',
  props: ['modelValue'],
  emits: ['update:modelValue'],
  template: `<div class="el-radio-group-stub"><slot /></div>`,
})

const ElRadioStub = defineComponent({
  name: 'ElRadio',
  props: ['value'],
  template: `<label><slot /></label>`,
})

const stubs = {
  AdminPageHeader: { template: '<div><slot name="actions" /></div>' },
  BackgroundSourceFields: defineComponent({
    props: ['modelValue', 'error', 'disabled', 'batch'],
    emits: ['update:modelValue'],
    template: `<div class="source-fields-stub">
      <input class="source-text-input" :value="modelValue.source_text" @input="$emit('update:modelValue', { ...modelValue, source_text: $event.target.value })" />
      <input class="source-url-input" :value="modelValue.source_url" @input="$emit('update:modelValue', { ...modelValue, source_url: $event.target.value })" />
    </div>`,
  }),
  ImagePickerDialog: true,
  StorageBackendSelect: true,
  ElCard: { template: '<div><slot /></div>' },
  ElForm: { template: '<form><slot /></form>' },
  ElFormItem: { template: '<div><slot /></div>' },
  ElIcon: { template: '<i><slot /></i>' },
  ElSelect: ElSelectStub,
  ElOption: ElOptionStub,
  ElButton: ElButtonStub,
  ElCheckbox: ElCheckboxStub,
  ElDialog: ElDialogStub,
  ElInput: ElInputStub,
  ElRadioGroup: ElRadioGroupStub,
  ElRadio: ElRadioStub,
}

function makeServer(initialRows: MockBgRow[]) {
  let rows = initialRows.map((item) => ({ ...item }))
  let nextId = Math.max(0, ...rows.map((item) => item.id)) + 1

  apiMocks.get.mockImplementation(async (path: string) => {
    const parsed = new URL(path, 'http://localhost')
    const theme = parsed.searchParams.get('theme')
    const device = parsed.searchParams.get('device')
    const items = rows
      .filter((item) => (!theme || item.theme === theme) && (!device || item.device === device))
      .sort((a, b) => a.sort_order - b.sort_order || a.id - b.id)
      .map((item): ApiBgItem => ({ ...item }))
    return { items, total: items.length }
  })

  apiMocks.put.mockImplementation(
    async (path: string, body: { ids: number[]; theme: string; device: string }) => {
      if (path === '/api/v1/backgrounds/reorder') {
        body.ids.forEach((id, order) => {
          const target = rows.find(
            (item) => item.id === id && item.theme === body.theme && item.device === body.device,
          )
          if (target) target.sort_order = order
        })
      }
      return undefined
    },
  )

  apiMocks.patch.mockImplementation(
    async (path: string, body: { source_text: string; source_url: string }) => {
      const id = Number(path.match(/\/backgrounds\/(\d+)\/source$/)?.[1])
      const target = rows.find((item) => item.id === id)
      if (!target) throw new Error('背景图不存在')
      target.source_text = body.source_text
      target.source_url = body.source_url
      return { ...target }
    },
  )

  apiMocks.delete.mockImplementation(async (path: string) => {
    const id = Number(path.match(/\/backgrounds\/(\d+)$/)?.[1])
    rows = rows.filter((item) => item.id !== id)
    return undefined
  })

  apiMocks.post.mockImplementation(async (path: string, body: Record<string, unknown>) => {
    if (path.startsWith('/api/v1/backgrounds/video-upload')) {
      const storage =
        new URL(path, 'http://localhost').searchParams.get('storage_backend') ?? 'local'
      return {
        url: '/api/v1/backgrounds/media/uploaded-r2.mp4',
        media_type: 'video',
        mime_type: 'video/mp4',
        file_size: 2048,
        storage_backend: storage,
      }
    }
    const created: MockBgRow = {
      id: nextId++,
      url: String(body.media_url ?? '/uploads/images/new.webp'),
      theme: (body.theme as 'dark' | 'light') ?? 'dark',
      device: (body.device as 'desktop' | 'mobile') ?? 'desktop',
      sort_order: Number(body.sort_order ?? 0),
      created_at: '',
      media_type: (body.media_type as 'image' | 'video') ?? 'image',
      mime_type: String(body.mime_type ?? ''),
      file_size: Number(body.file_size ?? 0),
      source_text: String(body.source_text ?? ''),
      source_url: String(body.source_url ?? ''),
      storage_backend: (body.storage_backend as 'local' | 'r2') ?? 'local',
    }
    rows.push(created)
    return { ...created }
  })

  return {
    getRows: () => rows,
  }
}

describe('后台背景管理 → 前台 UI Store 全链路联动', () => {
  beforeEach(() => {
    localStorage.clear()
    setActivePinia(createPinia())
    vi.clearAllMocks()
    storageBackendRef.value = 'local'
    elementMocks.confirm.mockResolvedValue('confirm')
  })

  afterEach(() => {
    vi.restoreAllMocks()
  })

  it('拖拽首张卡片到末尾并保存顺序，正确提交新顺序且前台保持当前选中 ID', async () => {
    makeServer([
      {
        id: 11,
        url: '/uploads/images/a.webp',
        theme: 'dark',
        device: 'desktop',
        sort_order: 0,
        created_at: '',
        media_type: 'image',
        source_text: '画师A',
        source_url: '',
      },
      {
        id: 12,
        url: '/uploads/images/b.webp',
        theme: 'dark',
        device: 'desktop',
        sort_order: 1,
        created_at: '',
        media_type: 'image',
        source_text: '画师B',
        source_url: '',
      },
      {
        id: 13,
        url: '/uploads/images/c.webp',
        theme: 'dark',
        device: 'desktop',
        sort_order: 2,
        created_at: '',
        media_type: 'image',
        source_text: '画师C',
        source_url: '',
      },
    ])

    const ui = useUIStore()
    await ui.loadBackgrounds()
    ui.setDarkBg(1) // 选中 ID=12
    expect(ui.currentBackground.id).toBe(12)

    const wrapper = mount(BackgroundList, {
      global: {
        stubs,
        directives: { loading: () => undefined },
      },
    })
    await flushPromises()

    // 同时筛选主题与设备开启拖拽排序
    const selects = wrapper.findAll('.el-select-stub')
    await selects[0].setValue('dark')
    await selects[1].setValue('desktop')
    await flushPromises()

    // 把第 1 张（id=11）拖到最后一张（id=13）位置，期望新顺序为 [12, 13, 11]
    const cards = wrapper.findAll('.bg-item')
    expect(cards).toHaveLength(3)
    await cards[0].trigger('dragstart')
    await cards[2].trigger('drop')
    await flushPromises()

    const saveOrderBtn = wrapper.findAll('button').find((b) => b.text().includes('保存顺序'))!
    expect(saveOrderBtn.attributes('disabled')).toBeUndefined()
    await saveOrderBtn.trigger('click')
    await flushPromises()

    expect(apiMocks.put).toHaveBeenCalledWith(
      '/api/v1/backgrounds/reorder',
      { ids: [12, 13, 11], theme: 'dark', device: 'desktop' },
      true,
    )
    // 重排后前台仍保持选中 id=12，且 darkBgs 顺序已更新
    expect(ui.darkBgs.map((item) => item.id)).toEqual([12, 13, 11])
    expect(ui.currentBackground.id).toBe(12)
    expect(ui.darkBgIndex).toBe(0)
    wrapper.unmount()
  })

  it('切换筛选条件会清空选中状态，单项删除同步清理 selectedIds 并刷新前台回退背景', async () => {
    const server = makeServer([
      {
        id: 1,
        url: '/uploads/images/dark-1.webp',
        theme: 'dark',
        device: 'desktop',
        sort_order: 0,
        created_at: '',
        media_type: 'image',
        source_text: '',
        source_url: '',
      },
      {
        id: 2,
        url: '/uploads/images/dark-2.webp',
        theme: 'dark',
        device: 'desktop',
        sort_order: 1,
        created_at: '',
        media_type: 'image',
        source_text: '',
        source_url: '',
      },
      {
        id: 3,
        url: '/uploads/images/light-1.webp',
        theme: 'light',
        device: 'desktop',
        sort_order: 0,
        created_at: '',
        media_type: 'image',
        source_text: '',
        source_url: '',
      },
    ])

    const ui = useUIStore()
    await ui.loadBackgrounds()
    expect(ui.currentBackground.id).toBe(1)

    const wrapper = mount(BackgroundList, {
      global: {
        stubs,
        directives: { loading: () => undefined },
      },
    })
    await flushPromises()

    // 勾选 id=1 后切换主题筛选到 light，原选中状态必须清空，避免误删暗色背景
    const selects = wrapper.findAll('.el-select-stub')
    await selects[0].setValue('dark')
    await flushPromises()
    await wrapper.findAll('.bg-check-input')[0].setValue(true)
    expect(wrapper.text()).toContain('已选 1 张')

    await selects[0].setValue('light')
    await flushPromises()
    expect(wrapper.text()).toContain('已选 0 张')

    // 切回 dark，勾选 id=1 后直接点单项“移除”，selectedIds 应清零且前台回退到 id=2
    await selects[0].setValue('dark')
    await flushPromises()
    await wrapper.findAll('.bg-check-input')[0].setValue(true)
    const removeButtons = wrapper.findAll('button').filter((b) => b.text() === '移除')
    await removeButtons[0].trigger('click')
    await flushPromises()

    expect(server.getRows().map((item) => item.id)).toEqual([2, 3])
    expect(wrapper.text()).toContain('已选 0 张')
    expect(ui.currentBackground.id).toBe(2)
    wrapper.unmount()
  })

  it('编辑背景来源与 R2 本地视频上传都会完整回写并同步到前台 store', async () => {
    const createObjectUrlSpy = vi
      .spyOn(URL, 'createObjectURL')
      .mockReturnValue('blob:local-preview')
    const revokeObjectUrlSpy = vi.spyOn(URL, 'revokeObjectURL').mockImplementation(() => undefined)
    storageBackendRef.value = 'r2'

    makeServer([
      {
        id: 20,
        url: '/uploads/images/dark-a.webp',
        theme: 'dark',
        device: 'desktop',
        sort_order: 0,
        created_at: '',
        media_type: 'image',
        source_text: '旧画师',
        source_url: '',
      },
    ])

    const ui = useUIStore()
    await ui.loadBackgrounds()

    const wrapper = mount(BackgroundList, {
      global: {
        stubs,
        directives: { loading: () => undefined },
      },
    })
    await flushPromises()

    // 1. 编辑背景来源并验证同步到前台 currentBackground
    const sourceBtn = wrapper.findAll('button').find((b) => b.text() === '来源')!
    await sourceBtn.trigger('click')
    await wrapper.get('.source-text-input').setValue('新画师')
    await wrapper.get('.source-url-input').setValue('https://example.com/artist')
    const saveSourceBtn = wrapper.findAll('button').find((b) => b.text() === '保存')!
    await saveSourceBtn.trigger('click')
    await flushPromises()

    expect(ui.currentBackground.sourceText).toBe('新画师')
    expect(ui.currentBackground.sourceUrl).toBe('https://example.com/artist')

    // 2. 上传本地视频（R2 后端）并验证 storage_backend='r2' 透传以及 ObjectURL 释放
    const addBtn = wrapper.findAll('button').find((b) => b.text().includes('添加背景图'))!
    await addBtn.trigger('click')
    await flushPromises()

    // 切换媒体类型为 video（直接通过组件实例/radio 组）
    const radioGroups = wrapper.findAllComponents(ElRadioGroupStub)
    radioGroups[2].vm.$emit('update:modelValue', 'video')
    await flushPromises()

    const fileInput = wrapper.get('input[type="file"]')
    const fakeVideo = new File(['mp4data'], 'loop.mp4', { type: 'video/mp4' })
    Object.defineProperty(fileInput.element, 'files', { value: [fakeVideo], configurable: true })
    await fileInput.trigger('change')
    expect(createObjectUrlSpy).toHaveBeenCalledTimes(1)

    const confirmUploadBtn = wrapper.findAll('button').find((b) => b.text().includes('确认上传'))!
    await confirmUploadBtn.trigger('click')
    await flushPromises()

    expect(apiMocks.post).toHaveBeenCalledWith(
      '/api/v1/backgrounds',
      expect.objectContaining({
        media_type: 'video',
        media_url: '/api/v1/backgrounds/media/uploaded-r2.mp4',
        storage_backend: 'r2',
        theme: 'dark',
        device: 'desktop',
        sort_order: 1,
      }),
      true,
    )
    expect(revokeObjectUrlSpy).toHaveBeenCalledWith('blob:local-preview')
    expect(ui.darkBgs).toHaveLength(2)
    expect(ui.darkBgs[1].mediaType).toBe('video')

    wrapper.unmount()
  })
})
