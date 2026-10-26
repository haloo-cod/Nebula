import { apiXhr } from '@/api/client'

/** 带进度的鉴权下载工具。 */
export async function downloadWithProgress(
  url: string,
  filename: string,
  options: {
    headers?: Record<string, string>
    onProgress?: (percent: number) => void
  } = {},
): Promise<void> {
  const xhr = await apiXhr(url, {
    headers: options.headers,
    auth: options.headers !== undefined,
    responseType: 'blob',
    onDownloadProgress: options.onProgress,
  })
  const objectUrl = URL.createObjectURL(xhr.response)
  const anchor = document.createElement('a')
  anchor.href = objectUrl
  anchor.download = filename
  document.body.appendChild(anchor)
  anchor.click()
  anchor.remove()
  URL.revokeObjectURL(objectUrl)
  options.onProgress?.(100)
}
