/** 后台文件目录浏览 API。 */
import { api } from './client'

/** 允许浏览的业务根目录。 */
export type StorageRoot = 'uploads' | 'content'

/** 子目录路径，相对于当前业务根目录。 */
export interface StorageDirectory {
  name: string
  path: string
}

/** 本地文件及其关联的数据库 / R2 元数据。 */
export interface StorageEntry {
  name: string
  path: string
  title: string
  file_size: number | null
  modified_at: string | null
  local_exists: boolean
  storage_backend: 'local' | 'r2'
  record_kind: string | null
  record_id: number | null
  r2_key: string | null
  r2_url: string | null
  url: string | null
  manage_url: string | null
}

/** 目录浏览响应：目录完整返回，文件按页返回。 */
export interface StorageBrowseResponse {
  root: StorageRoot
  path: string
  directories: StorageDirectory[]
  items: StorageEntry[]
  total: number
  page: number
  page_size: number
  r2_enabled: boolean
}

/** 获取指定目录的本地文件和已登记 R2 对象。 */
export function browseStorage(
  root: StorageRoot,
  path = '',
  page = 1,
  pageSize = 50,
): Promise<StorageBrowseResponse> {
  const params = new URLSearchParams({
    root,
    path,
    page: String(page),
    page_size: String(pageSize),
  })
  return api.get<StorageBrowseResponse>(`/api/v1/storage/browse?${params}`, true)
}
