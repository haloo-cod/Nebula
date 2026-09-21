/**
 * 存储后端选择 composable
 * 全局（跨页面）记住管理员选择的默认存储后端，并检测 R2 是否可用
 */

import { ref } from 'vue'
import { api } from '@/api/client'
import type { StorageBackend } from '@/api/images'

const STORAGE_KEY = 'blog_admin_storage_backend'

/** 当前选择的存储后端（模块级单例，跨组件共享） */
const storageBackend = ref<StorageBackend>(
  (localStorage.getItem(STORAGE_KEY) as StorageBackend) === 'r2' ? 'r2' : 'local',
)

/** R2 是否启用（来自后端 storage-config 接口） */
const r2Enabled = ref<boolean | null>(null)

/** 配置是否已加载完成 */
const configLoaded = ref(false)

/** 拉取后端存储配置，确定 R2 可用性；R2 不可用时自动回落到 local */
async function loadStorageConfig(): Promise<void> {
  if (configLoaded.value) return
  try {
    const config = await api.get<{ r2_enabled: boolean }>('/api/v1/r2-migration/storage-config', true)
    r2Enabled.value = config.r2_enabled
    if (!config.r2_enabled && storageBackend.value === 'r2') {
      storageBackend.value = 'local'
    }
  } catch {
    // 配置接口失败时保守地视为不可用
    r2Enabled.value = false
  } finally {
    configLoaded.value = true
  }
}

/** 切换存储后端并持久化 */
function setStorageBackend(value: StorageBackend): void {
  storageBackend.value = value
  localStorage.setItem(STORAGE_KEY, value)
}

/** 存储后端选择逻辑 */
export function useStorageBackend() {
  return {
    storageBackend,
    r2Enabled,
    configLoaded,
    loadStorageConfig,
    setStorageBackend,
  }
}
