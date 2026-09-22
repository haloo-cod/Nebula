/**
 * R2 迁移管理 API
 * 对接后端 /api/v1/r2-migration/* 接口
 */
import { api } from './client'

/** 各表的迁移统计 */
export interface MigrationTableStats {
  total: number
  migrated: number
  pending: number
}

/** 迁移状态总览（GET /migration-status 响应） */
export interface MigrationStatus {
  r2_enabled: boolean
  images: MigrationTableStats
  files: MigrationTableStats
  backgrounds: MigrationTableStats
  books: MigrationTableStats
}

/** 存储配置（GET /storage-config 响应） */
export interface StorageConfig {
  r2_enabled: boolean
  r2_configured: boolean
  default_storage: string
}

/** 迁移请求体：只需传入对应类型的 id 列表 */
export interface MigrateRequest {
  image_ids?: number[]
  file_ids?: number[]
  background_ids?: number[]
  book_ids?: number[]
}

/** 迁移结果响应 */
export interface MigrateResponse {
  success_count: number
  failed_count: number
  failed_ids: number[]
  errors: string[]
}

/** 获取迁移状态统计。 */
export function getMigrationStatus(): Promise<MigrationStatus> {
  return api.get<MigrationStatus>('/api/v1/r2-migration/migration-status', true)
}

/** 获取存储配置。 */
export function getStorageConfig(): Promise<StorageConfig> {
  return api.get<StorageConfig>('/api/v1/r2-migration/storage-config', true)
}

/** 批量迁移图片到 R2。 */
export function migrateImages(imageIds: number[]): Promise<MigrateResponse> {
  return api.post<MigrateResponse>(
    '/api/v1/r2-migration/migrate-images',
    { image_ids: imageIds } satisfies MigrateRequest,
    true,
  )
}

/** 批量迁移通用文件到 R2。 */
export function migrateFiles(fileIds: number[]): Promise<MigrateResponse> {
  return api.post<MigrateResponse>(
    '/api/v1/r2-migration/migrate-files',
    { file_ids: fileIds } satisfies MigrateRequest,
    true,
  )
}

/** 批量迁移背景视频到 R2。 */
export function migrateBackgrounds(backgroundIds: number[]): Promise<MigrateResponse> {
  return api.post<MigrateResponse>(
    '/api/v1/r2-migration/migrate-backgrounds',
    { background_ids: backgroundIds } satisfies MigrateRequest,
    true,
  )
}

/** 批量迁移图书 EPUB 到 R2。 */
export function migrateBooks(bookIds: number[]): Promise<MigrateResponse> {
  return api.post<MigrateResponse>(
    '/api/v1/r2-migration/migrate-books',
    { book_ids: bookIds } satisfies MigrateRequest,
    true,
  )
}

/** 预签名直传请求体 */
export interface PresignRequest {
  filename: string
  content_type: string
  directory: 'images' | 'files'
}

/** 预签名直传响应 */
export interface PresignResponse {
  upload_url: string
  r2_key: string
  url: string
  cache_control: string
  storage_backend: 'r2'
}

/** 申请预签名 PUT URL（管理员）。 */
export function presignUpload(req: PresignRequest): Promise<PresignResponse> {
  return api.post<PresignResponse>('/api/v1/r2-migration/presign-upload', req, true)
}

/** 直传完成后的登记请求体 */
export interface RegisterUploadRequest {
  directory: 'images' | 'files'
  r2_key: string
  original_name: string
  mime_type: string
  file_size: number
  width?: number
  height?: number
}

/** 登记后的记录（匹配后端响应） */
export interface RegisteredUpload {
  id: number
  filename: string
  original_name: string
  url: string
  file_size: number
  mime_type: string
}

/** 直传完成后登记数据库记录（管理员）。 */
export function registerUpload(req: RegisterUploadRequest): Promise<RegisteredUpload> {
  return api.post<RegisteredUpload>('/api/v1/r2-migration/register-upload', req, true)
}

/** 为全部已迁移对象补写 Cache-Control 元数据（管理员，幂等）。 */
export function backfillCache(): Promise<MigrateResponse> {
  return api.post<MigrateResponse>('/api/v1/r2-migration/backfill-cache', {}, true)
}

/**
 * 浏览器直传文件到 R2：申请预签名 URL → PUT 直传 → 登记记录。
 *
 * 与服务器中转上传不同，此路径不经后端转发，适合大文件。
 * 返回 null 表示 R2 未启用或目录不支持直传（调用方应回退到服务器中转上传）。
 *
 * @param file 要上传的文件
 * @param directory 对象键目录：'images' | 'files'
 * @param onProgress 上传进度回调（0-100）
 */
export async function uploadDirectToR2(
  file: File,
  directory: 'images' | 'files',
  onProgress?: (percent: number) => void,
): Promise<RegisteredUpload | null> {
  const presigned = await presignUpload({
    filename: file.name,
    content_type: file.type || 'application/octet-stream',
    directory,
  })

  // PUT 直传 R2（预签名 URL 已含认证，不能再带 Authorization 头）。
  // Cache-Control 已参与签名，必须回传同值头，否则 R2 拒绝（403 SignatureDoesNotMatch）
  const ok = await new Promise<boolean>((resolve, reject) => {
    const xhr = new XMLHttpRequest()
    xhr.open('PUT', presigned.upload_url)
    xhr.setRequestHeader('Content-Type', file.type || 'application/octet-stream')
    if (presigned.cache_control) {
      xhr.setRequestHeader('Cache-Control', presigned.cache_control)
    }
    xhr.upload.addEventListener('progress', (event) => {
      if (event.lengthComputable && onProgress) {
        onProgress(Math.round((event.loaded / event.total) * 100))
      }
    })
    xhr.addEventListener('load', () => resolve(xhr.status >= 200 && xhr.status < 300))
    xhr.addEventListener('error', () => reject(new Error('直传 R2 失败（网络错误或 CORS 拦截）')))
    xhr.addEventListener('abort', () => reject(new Error('直传已取消')))
    xhr.send(file)
  })
  if (!ok) throw new Error('直传 R2 失败，请检查桶 CORS 配置是否允许 PUT')

  return registerUpload({
    directory,
    r2_key: presigned.r2_key,
    original_name: file.name,
    mime_type: file.type || 'application/octet-stream',
    file_size: file.size,
  })
}
