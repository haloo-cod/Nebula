/**
 * 图床 API
 * 统一封装图片上传（支持选择存储后端）与列表查询
 */

import { BASE_URL, getToken } from './client'

/** 存储后端类型 */
export type StorageBackend = 'local' | 'r2'

/** 图床图片记录（匹配后端 ImageResponse） */
export interface UploadedImage {
  id: number
  filename: string
  original_name: string
  url: string
  file_size: number
  width: number
  height: number
  mime_type: string
  created_at: string
  storage_backend?: StorageBackend
}

/** 图片分页列表响应 */
interface ImageListResponse {
  items: UploadedImage[]
  total: number
}

/**
 * 上传图片到图床
 * @param file 图片文件
 * @param storageBackend 存储后端：'local' 本地磁盘 | 'r2' Cloudflare R2
 */
export async function uploadImage(
  file: File,
  storageBackend: StorageBackend = 'local',
): Promise<UploadedImage> {
  const formData = new FormData()
  formData.append('file', file)

  const response = await fetch(
    `${BASE_URL}/api/v1/images/upload?storage_backend=${storageBackend}`,
    {
      method: 'POST',
      headers: { Authorization: `Bearer ${getToken() ?? ''}` },
      body: formData,
      credentials: 'include',
    },
  )

  if (!response.ok) {
    const body = (await response.json().catch(() => ({}))) as { detail?: string }
    throw new Error(body.detail || `图片上传失败 (${response.status})`)
  }
  return (await response.json()) as UploadedImage
}

/**
 * 上传图片并返回 Vditor 要求的响应格式（供编辑器 upload.format 使用）
 */
export async function uploadImageForVditor(
  file: File,
  storageBackend: StorageBackend = 'local',
): Promise<{ url: string; originalName: string }> {
  const image = await uploadImage(file, storageBackend)
  return { url: image.url, originalName: image.original_name }
}

/** 分页获取图床图片列表 */
export async function fetchImages(
  page = 1,
  pageSize = 100,
  storageBackend?: StorageBackend,
): Promise<{ items: UploadedImage[]; total: number }> {
  const params = new URLSearchParams({
    page: String(page),
    page_size: String(pageSize),
  })
  if (storageBackend) params.set('storage_backend', storageBackend)
  const { api } = await import('./client')
  return api.get<ImageListResponse>(`/api/v1/images?${params}`, true)
}
