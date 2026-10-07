/** 来源表单的完整请求体。 */
export interface BackgroundSource {
  source_text: string
  source_url: string
}

/** 校验完整 HTTP(S) 外链；空地址表示仅显示文字。 */
export function isBackgroundSourceUrl(value: string): boolean {
  if (!value) return true
  if (!/^https?:\/\//i.test(value) || /\s/.test(value)) return false
  try {
    const url = new URL(value)
    return ['http:', 'https:'].includes(url.protocol) && Boolean(url.hostname)
  } catch {
    return false
  }
}

/** 与后台字段限制保持一致，返回可展示的校验错误。 */
export function backgroundSourceError(source: BackgroundSource): string {
  if ([...source.source_text.trim()].length > 120) return '来源文字最多 120 字符'
  if (source.source_url.trim().length > 2048) return '来源链接最多 2048 字符'
  if (!isBackgroundSourceUrl(source.source_url.trim()))
    return '来源链接必须是完整的 HTTP 或 HTTPS 地址'
  return ''
}
