import { languages, defaultLang } from './languages'

export function getCurrentLang() {
  return localStorage.getItem('blog-lang') || defaultLang
}

export function setLang(code) {
  localStorage.setItem('blog-lang', code)
  if (typeof window.translate === 'undefined') return
  window.translate.changeLanguage(code)
}

export function getLangLabel(code) {
  const lang = languages.find((l) => l.code === code)
  return lang ? lang.label : code
}

export { languages, defaultLang }
