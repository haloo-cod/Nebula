/**
 * 通用文件 API
 * 用于藏宝阁资源上传、文件库管理和公开下载
 */

import { api, BASE_URL, getToken } from './client'
import type { StorageBackend } from './images'

/** 后端通用文件记录 */
export interface UploadedFile {
  id: number
  filename: string
  original_name: string
  url: string
  file_size: number
  mime_type: string
  created_at: string
  storage_backend?: StorageBackend
  /** R2 公开直链（未迁移或未配置自定义域名时为 undefined） */
  r2_url?: string | null
}

/** 文件分页列表响应 */
interface FileListResponse {
  items: UploadedFile[]
  total: number
}

/** 获取已上传文件列表（可按存储后端过滤） */
export async function fetchFiles(
  page = 1,
  pageSize = 200,
  storageBackend?: StorageBackend,
): Promise<UploadedFile[]> {
  const params = new URLSearchParams({
    page: String(page),
    page_size: String(pageSize),
  })
  if (storageBackend) params.set('storage_backend', storageBackend)
  const response = await api.get<FileListResponse>(`/api/v1/files?${params}`, true)
  return response.items
}

/** 删除已上传文件 */
export function deleteUploadedFile(fileId: number): Promise<void> {
  return api.delete<void>(`/api/v1/files/${fileId}`)
}

/** 上传任意类型文件，并报告浏览器侧上传进度 */
export function uploadFile(
  file: File,
  onProgress?: (percent: number) => void,
  storageBackend: StorageBackend = 'local',
): Promise<UploadedFile> {
  return new Promise((resolve, reject) => {
    const xhr = new XMLHttpRequest()
    const formData = new FormData()
    formData.append('file', file)

    xhr.open('POST', `${BASE_URL}/api/v1/files/upload?storage_backend=${storageBackend}`)
    const token = getToken()
    if (token) xhr.setRequestHeader('Authorization', `Bearer ${token}`)

    xhr.upload.addEventListener('progress', (event) => {
      if (event.lengthComputable && onProgress) {
        onProgress(Math.round((event.loaded / event.total) * 100))
      }
    })

    xhr.addEventListener('load', () => {
      if (xhr.status >= 200 && xhr.status < 300) {
        try {
          resolve(JSON.parse(xhr.responseText) as UploadedFile)
        } catch {
          reject(new Error('上传响应解析失败'))
        }
        return
      }

      try {
        const body = JSON.parse(xhr.responseText) as { detail?: string }
        reject(new Error(body.detail || `上传失败 (${xhr.status})`))
      } catch {
        reject(new Error(`上传失败 (${xhr.status})`))
      }
    })
    xhr.addEventListener('error', () => reject(new Error('网络错误，上传失败')))
    xhr.addEventListener('abort', () => reject(new Error('上传已取消')))
    xhr.send(formData)
  })
}

/** 按顺序批量上传文件，单个文件失败不会中断后续任务。 */
export async function uploadFiles(
  files: File[],
  onProgress?: (completed: number, total: number, current: string) => void,
  storageBackend: StorageBackend = 'local',
): Promise<{ file: File; result?: UploadedFile; error?: string }[]> {
  const results: { file: File; result?: UploadedFile; error?: string }[] = []
  for (const [index, file] of files.entries()) {
    onProgress?.(index, files.length, file.name)
    try {
      const result = await uploadFile(
        file,
        (percent) => {
          onProgress?.(index + percent / 100, files.length, file.name)
        },
        storageBackend,
      )
      results.push({ file, result })
    } catch (error: unknown) {
      results.push({ file, error: error instanceof Error ? error.message : '上传失败' })
    }
  }
  onProgress?.(files.length, files.length, '')
  return results
}
