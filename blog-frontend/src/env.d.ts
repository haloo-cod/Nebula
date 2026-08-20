/// <reference types="vite/client" />

// ---------------------------------------------------------------------------
// 全局类型声明文件
// 作用:为 .vue 单文件组件、特殊资源导入、以及无官方类型的第三方库补充类型,
// 让 TS 在严格模式下也能正确识别这些导入。本文件不包含任何运行时代码。
// ---------------------------------------------------------------------------

// Vue 单文件组件:让 TS 把 `import X from './X.vue'` 识别为一个组件
declare module '*.vue' {
  import type { DefineComponent } from 'vue'
  const component: DefineComponent<{}, {}, any>
  export default component
}

// 以 ?raw 方式导入的 Markdown 文件:返回文件原始字符串内容
// 用于 data/posts.ts 通过 import.meta.glob 读取 src/assets/md/*.md
declare module '*.md?raw' {
  const content: string
  export default content
}

// 以 ?url 方式导入的 SVG 文件:返回资源的最终 URL
// 用于 SvgIcon.vue 通过 import.meta.glob 读取图标
declare module '*.svg?url' {
  const url: string
  export default url
}

// 大写扩展名图片模块声明(Vite 默认只覆盖小写扩展名)
declare module '*.PNG' {
  const src: string
  export default src
}

declare module '*.JPG' {
  const src: string
  export default src
}

// ---------------------------------------------------------------------------
// i18n-jsautotranslate 类型 shim
// 该库无官方类型声明,这里仅按本项目实际用到的 API 补一个最小声明。
// 不修改库源码,只描述其外形,供 i18n/index.ts、main.ts 调用时获得类型提示。
// ---------------------------------------------------------------------------
declare module 'i18n-jsautotranslate' {
  /** translate.js 实例的最小类型,仅覆盖本项目用到的成员 */
  interface Translate {
    /** 语言相关设置 */
    language: {
      /** 设置页面源语言,例如 'chinese_simplified' */
      setLocal(lang: string): void
    }
    /** 翻译服务提供方设置 */
    service: {
      /** 选择翻译服务,例如 'client.edge' */
      use(service: string): void
    }
    /** 内置的语言下拉选择器 */
    selectLanguageTag: {
      /** 是否显示内置语言选择器 */
      show: boolean
    }
    /** DOM 变更监听器 */
    listener: {
      /** 开始监听 DOM 变化以自动翻译新增内容 */
      start(): void
    }
    /** 立即执行一次翻译 */
    execute(): void
    /** 切换目标语言 */
    changeLanguage(lang: string): void
  }
  const translate: Translate
  export default translate
}

// Emoji 选择器仅注册自定义元素，项目侧只需声明其模块存在。
declare module 'emoji-picker-element'

// 将 translate 实例挂到 window 上(见 main.ts),这里声明对应的全局类型
interface Window {
  translate?: typeof import('i18n-jsautotranslate').default
}
