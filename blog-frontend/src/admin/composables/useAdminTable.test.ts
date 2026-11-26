import { afterEach, beforeEach, describe, expect, it, vi } from 'vitest'
import { effectScope, type EffectScope } from 'vue'
import { useAdminTable } from './useAdminTable'

const messages = vi.hoisted(() => ({ error: vi.fn(), success: vi.fn(), confirm: vi.fn() }))
vi.mock('element-plus', () => ({
  ElMessage: { error: messages.error, success: messages.success },
  ElMessageBox: { confirm: messages.confirm },
}))

describe('管理表格删除反馈', () => {
  const scopes: EffectScope[] = []

  beforeEach(() => {
    vi.clearAllMocks()
    messages.confirm.mockResolvedValue('confirm')
  })
  afterEach(() => scopes.splice(0).forEach((scope) => scope.stop()))

  function setup() {
    const fetchData = vi.fn().mockResolvedValue({ items: [], total: 0 })
    const deleteItem = vi.fn().mockResolvedValue(undefined)
    const scope = effectScope()
    scopes.push(scope)
    const table = scope.run(() => useAdminTable<{ id: number }>({ fetchData, deleteItem }))!
    return { table, fetchData, deleteItem }
  }

  it.each(['cancel', 'close'])('用户 %s 时不删除、不提示成功或错误', async (action) => {
    const { table, deleteItem } = setup()
    messages.confirm.mockRejectedValueOnce(action)
    await table.handleDelete({ id: 1 })
    expect(deleteItem).not.toHaveBeenCalled()
    expect(messages.error).not.toHaveBeenCalled()
    expect(messages.success).not.toHaveBeenCalled()
  })

  it.each([
    '图片正在被相册引用，请先解除关联',
    '服务器无法删除文件',
    'cancel',
  ])('删除失败直接显示服务端详情：%s', async (detail) => {
    const { table, fetchData, deleteItem } = setup()
    const item = { id: 1 }
    table.data.value = [item]
    table.pagination.page = 2
    deleteItem.mockRejectedValueOnce(new Error(detail))
    await table.handleDelete(item)
    expect(messages.error).toHaveBeenCalledWith(detail)
    expect(messages.success).not.toHaveBeenCalled()
    expect(table.data.value).toEqual([item])
    expect(table.pagination.page).toBe(2)
    expect(fetchData).not.toHaveBeenCalled()
  })

  it('删除成功才提示成功并加载上一页', async () => {
    const { table, fetchData, deleteItem } = setup()
    table.data.value = [{ id: 1 }]
    table.pagination.page = 2
    await table.handleDelete({ id: 1 })
    expect(deleteItem).toHaveBeenCalledWith({ id: 1 })
    expect(messages.success).toHaveBeenCalledWith('删除成功')
    expect(messages.error).not.toHaveBeenCalled()
    expect(fetchData).toHaveBeenCalledWith({ page: 1, pageSize: 15, keyword: undefined })
  })
})
