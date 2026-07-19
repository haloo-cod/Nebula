/**
 * 管理后台通用表格 composable
 * 封装分页、搜索、加载状态、删除确认等通用逻辑
 */

import { ref, reactive, watch } from 'vue'
import { ElMessageBox, ElMessage } from 'element-plus'

/** 分页参数 */
export interface Pagination {
  page: number
  pageSize: number
  total: number
}

/** useAdminTable 配置项 */
export interface AdminTableOptions<T> {
  /** 获取列表数据的函数，接收分页和搜索参数 */
  fetchData: (params: { page: number; pageSize: number; keyword?: string }) => Promise<{ items: T[]; total: number }>
  /** 删除单条数据的函数（可选） */
  deleteItem?: (item: T) => Promise<void>
  /** 默认每页条数 */
  defaultPageSize?: number
}

/** 通用表格管理 composable */
export function useAdminTable<T>(options: AdminTableOptions<T>) {
  const { fetchData, deleteItem, defaultPageSize = 15 } = options

  // 状态
  const loading = ref(false)
  const data = ref<T[]>([])
  const keyword = ref('')
  const pagination = reactive<Pagination>({
    page: 1,
    pageSize: defaultPageSize,
    total: 0,
  })

  /** 加载数据 */
  async function loadData() {
    loading.value = true
    try {
      const res = await fetchData({
        page: pagination.page,
        pageSize: pagination.pageSize,
        keyword: keyword.value || undefined,
      })
      data.value = res.items
      pagination.total = res.total
    } catch (err: unknown) {
      const msg = err instanceof Error ? err.message : '加载失败'
      ElMessage.error(msg)
    } finally {
      loading.value = false
    }
  }

  /** 搜索（重置到第一页） */
  function handleSearch() {
    pagination.page = 1
    loadData()
  }

  /** 切换页码 */
  function handlePageChange(page: number) {
    pagination.page = page
    loadData()
  }

  /** 切换每页条数 */
  function handleSizeChange(size: number) {
    pagination.pageSize = size
    pagination.page = 1
    loadData()
  }

  /** 删除确认 + 执行 */
  async function handleDelete(item: T, label = '此项') {
    if (!deleteItem) return

    try {
      await ElMessageBox.confirm(`确定要删除${label}吗？此操作不可恢复。`, '确认删除', {
        confirmButtonText: '删除',
        cancelButtonText: '取消',
        type: 'warning',
      })
      await deleteItem(item)
      ElMessage.success('删除成功')
      // 如果当前页删完了,回到上一页
      if (data.value.length === 1 && pagination.page > 1) {
        pagination.page--
      }
      await loadData()
    } catch {
      // 用户取消或删除失败,不处理
    }
  }

  /** 刷新当前页 */
  function refresh() {
    loadData()
  }

  // 监听 keyword 为空时自动刷新（清空搜索框时）
  watch(keyword, (val) => {
    if (!val) {
      pagination.page = 1
      loadData()
    }
  })

  return {
    loading,
    data,
    keyword,
    pagination,
    loadData,
    handleSearch,
    handlePageChange,
    handleSizeChange,
    handleDelete,
    refresh,
  }
}
