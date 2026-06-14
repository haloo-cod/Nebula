import type { Language } from '@/types'

// 支持的语言列表,translate.js 语种代码参考 http://translate.zvo.cn/4071.html
export const languages: Language[] = [
  { label: '中文', code: 'chinese_simplified', native: '简体中文' },
  { label: 'English', code: 'english', native: 'English' },
  { label: '日本語', code: 'japanese', native: '日本語' },
  { label: '한국어', code: 'korean', native: '한국어' },
  { label: 'Français', code: 'french', native: 'Français' },
  { label: 'Deutsch', code: 'german', native: 'Deutsch' },
  { label: 'Русский', code: 'russian', native: 'Русский' },
  { label: 'Español', code: 'spanish', native: 'Español' },
  { label: '繁體中文', code: 'chinese_traditional', native: '繁體中文' },
]

// 默认语言
export const defaultLang = 'chinese_simplified'
