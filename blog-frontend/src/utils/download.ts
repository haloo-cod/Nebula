/** 带进度的鉴权下载工具。 */
export function downloadWithProgress(
  url: string,
  filename: string,
  options: {
    headers?: Record<string, string>
    onProgress?: (percent: number) => void
  } = {},
): Promise<void> {
  return new Promise((resolve, reject) => {
    const xhr = new XMLHttpRequest()
    xhr.open('GET', url)
    xhr.withCredentials = true
    Object.entries(options.headers ?? {}).forEach(([key, value]) =>
      xhr.setRequestHeader(key, value),
    )
    xhr.responseType = 'blob'

    xhr.addEventListener('progress', (event) => {
      if (event.lengthComputable) {
        options.onProgress?.(Math.round((event.loaded / event.total) * 100))
      }
    })
    xhr.addEventListener('load', () => {
      if (xhr.status < 200 || xhr.status >= 300) {
        reject(new Error(`下载失败 (${xhr.status})`))
        return
      }
      const objectUrl = URL.createObjectURL(xhr.response)
      const anchor = document.createElement('a')
      anchor.href = objectUrl
      anchor.download = filename
      document.body.appendChild(anchor)
      anchor.click()
      anchor.remove()
      URL.revokeObjectURL(objectUrl)
      options.onProgress?.(100)
      resolve()
    })
    xhr.addEventListener('error', () => reject(new Error('网络错误，下载失败')))
    xhr.addEventListener('abort', () => reject(new Error('下载已取消')))
    xhr.send()
  })
}
