import { uploadImageForVditor, type StorageBackend } from '@/api/images'
import { resolveUrl } from '@/api/client'

/** 编辑器每次上传时读取存储选择，并复用具备登录续期的图片接口。 */
export async function uploadEditorImages(
  files: File[],
  storageBackend: StorageBackend,
  insert: (markdown: string) => void,
): Promise<null> {
  for (const file of files) {
    if (!file.type.startsWith('image/')) throw new Error('请选择图片文件')
    if (file.size > 10 * 1024 * 1024) throw new Error('图片最大允许 10MB')
  }
  for (const file of files) {
    const image = await uploadImageForVditor(file, storageBackend)
    const alt = image.originalName.replace(/[\[\]\\]/g, '\\$&').replace(/[\r\n]/g, ' ')
    const url = resolveUrl(image.url).replace(/[()]/g, encodeURIComponent)
    insert(`![${alt}](${url})\n`)
  }
  return null
}
