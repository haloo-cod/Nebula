// ---------------------------------------------------------------------------
// 全站共享的领域数据类型
// 集中定义文章、个人资料、日历等核心数据结构,供数据层与组件层复用。
// ---------------------------------------------------------------------------

/** 博客文章元数据(列表与详情共用,正文按需渲染) */
export interface Post {
  slug: string // URL 标识,由 Markdown 文件名生成
  title: string // 文章标题,缺省时回退为 slug
  description: string // 摘要描述,可能为空串
  date: string // 发表日期(frontmatter 的 published 字段),可能为空串
  tags: string[] // 标签列表
  category: string // 分类,可能为空串
  draft: boolean // 是否草稿(草稿不参与统计与默认展示)
  pinned: boolean // 是否置顶
  content: string // Markdown 正文原文(渲染时才转 HTML)
}

/** Markdown frontmatter 解析后的键值对(动态结构,值类型不定) */
export interface Frontmatter {
  title?: string
  description?: string
  published?: string
  tags?: string[]
  category?: string
  draft?: boolean
  pinned?: boolean
  // frontmatter 可能包含任意自定义字段,故保留索引签名
  [key: string]: string | number | boolean | string[] | undefined
}

/** 按年份聚合的文章数量统计,用于右侧折线图 */
export interface PostStat {
  label: string // x 轴标签(年份,如 '2024')
  count: number // 该年发表数量
}

/** 个人资料 */
export interface Profile {
  name: string // 昵称
  bio: string // 个性签名 / 简介
}

/** 社交链接 */
export interface SocialLink {
  label: string // 平台名称,如 'GitHub'
  icon: string // 图标(当前为 emoji)
  url: string // 跳转地址
}

/** 支持的界面语言 */
export interface Language {
  label: string // 菜单显示名,如 '中文'
  code: string // translate.js 语种代码,如 'chinese_simplified'
  native: string // 该语言的本地名称
}

/** 某天的节假日信息(由整年节假日数据提取得到) */
export interface HolidayDay {
  name: string // 节假日名称
  isOff: boolean // 是否为放假日
  isWork: boolean // 是否为调休补班日
}

/** timor.tech 节假日 API 返回的单条记录(仅声明本项目用到的字段) */
export interface HolidayApiInfo {
  name: string // 节假日名称
  holiday: boolean // true=放假, false=调休补班
}

/** timor.tech 节假日 API 的整体响应外形 */
export interface HolidayApiResponse {
  // key 为 'MM-DD' 格式的日期字符串
  holiday?: Record<string, HolidayApiInfo>
}
