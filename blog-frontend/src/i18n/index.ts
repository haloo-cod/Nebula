import { languages, defaultLang } from './languages'

/** 读取当前语言代码(持久化在 localStorage) */
export function getCurrentLang(): string {
  return localStorage.getItem('blog-lang') || defaultLang
}

/** 设置并持久化语言,同时通知 translate.js 切换 */
export function setLang(code: string): void {
  localStorage.setItem('blog-lang', code)
  if (typeof window.translate === 'undefined') return
  window.translate.changeLanguage(code)
}

/** 根据语言代码获取菜单显示名,未知代码时回退为代码本身 */
export function getLangLabel(code: string): string {
  const lang = languages.find((l) => l.code === code)
  return lang ? lang.label : code
}

export { languages, defaultLang }
