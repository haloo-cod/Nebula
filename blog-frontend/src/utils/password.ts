/** 与后端一致的新密码限制；现有密码不会被截断或改写。 */
export function getPasswordError(password: string): string {
  if (Array.from(password).length < 8) return '密码至少需要 8 个字符'
  if (new TextEncoder().encode(password).byteLength > 72) return '密码最多为 72 个 UTF-8 字节'
  return ''
}
