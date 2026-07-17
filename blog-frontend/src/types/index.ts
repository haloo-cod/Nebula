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
  cover: string // 文章封面图 URL,由前端手动映射补齐,可能为空串
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

/** 展览页项目元数据与 Markdown 正文 */
export interface GalleryProject {
  slug: string // URL 标识,对应 src/assets/projects 下的 Markdown 文件名
  title: string // 项目名称
  description: string // 项目简介
  tags: string[] // 项目标签
  status: string // 项目状态,如 构建中 / 重构中
  year: string // 项目年份或阶段年份
  featured?: boolean // 是否作为重点项目展示
  content: string // Markdown 正文原文(渲染时才转 HTML)
}

/** 图书元数据(列表与阅读器共用,EPUB 元数据可按需补全) */
export interface Book {
  slug: string // URL 标识,由 EPUB 文件名或后端标识生成
  title: string // 书名,缺省时可由 EPUB 元数据补全
  author: string // 作者,缺省时可由 EPUB 元数据补全
  description: string // 简介或阅读备注,可能为空串
  cover: string // 封面图 URL,可能为空串;为空时使用占位封面
  file: string // EPUB 文件访问地址,测试阶段指向 public/books,后续可换后端 URL
}

/** 相册中的单张照片 */
export interface AlbumPhoto {
  url: string // 照片 URL,当前来自本地 assets,后续可换后端图床
  caption?: string // 照片说明文字,灯箱与悬停遮罩中展示,可缺省
}

/** 相册元数据(照片墙概览与相册详情共用) */
export interface Album {
  id: string // 相册唯一标识
  title: string // 相册标题
  description: string // 相册简介,可能为空串
  cover: string // 封面照片 URL(照片堆叠最上层)
  date: string // 相册日期标签,格式不限(如 2026.05)
  orientation: 'landscape' | 'portrait' // 照片墙堆叠方向,管理后台可按相册选择;决定概览照片栈的宽高比
  photos: AlbumPhoto[] // 全部照片;堆叠的中/底层取 photos[1]/photos[2],不足时条件渲染
}

/** 从 EPUB 内部自动解析出的图书元数据 */
export interface ExtractedBookMeta {
  title?: string // EPUB metadata.title
  author?: string // EPUB metadata.creator
  description?: string // EPUB metadata.description
  cover?: string // EPUB 内封面解析出的 blob URL
}

/** 友链条目(友链页鱼缸与列表共用) */
export interface Friend {
  name: string // 站点名
  bio: string // 简介
  avatar: string // 头像 URL
  url: string // 站点地址
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

// ---------------------------------------------------------------------------
// 说说(Moments)
// ---------------------------------------------------------------------------

/** 一条说说/碎碎念 */
export interface Moment {
  id: number
  date: string // ISO 日期时间,如 '2026-07-10T13:37:15'
  content: string // 纯文本正文
  mood?: string // 心情标签,如 '开心'、'疲惫'、'灵感'
  tags: string[]
  images: string[] // 图片 URL 列表
  likes: number // 点赞数
}

/** 说说评论(一层平铺,暂不支持嵌套回复) */
export interface MomentComment {
  id: number
  momentId: number // 所属说说 ID
  nickname: string // 评论者昵称
  avatar?: string // 评论者头像 URL
  content: string // 评论正文
  date: string // ISO 日期时间
  likes: number // 评论点赞数
}

/** getMoments 分页返回结构 */
export interface MomentPage {
  items: Moment[]
  total: number
}

// ---------------------------------------------------------------------------
// 藏宝阁（Treasure）
// ---------------------------------------------------------------------------

/** 藏宝阁分类（未来可由后端动态提供） */
export type TreasureCategory = '开源项目' | '工具' | '资源下载'

/** 藏宝阁条目 */
export interface Treasure {
  slug: string // 唯一标识
  title: string // 名称
  description: string // 简介
  category: TreasureCategory // 分类
  icon: string // 图标（emoji 或 SVG 路径）
  url: string // 外链地址（开源项目跳 GitHub 等）
  downloadUrl?: string // 可选下载链接（未来由后端提供）
  tags: string[] // 标签
}

// ---------------------------------------------------------------------------
// 自习室（Study Room）
// ---------------------------------------------------------------------------

/** 自习室待办（每个待办自带独立专注+休息倒计时） */
export interface StudyTodo {
  id: string // 唯一标识
  title: string // 任务名称
  durationMinutes: number // 专注时长（分钟）
  breakMinutes: number // 休息时长（分钟）
  remainingSeconds: number // 当前剩余秒数
  completedPomodoros: number // 累计完成番茄钟数
  todayCompleted: number // 今日完成番茄钟数（每日自动清零）
  isRunning: boolean // 是否正在倒计时
  isCompleted: boolean // 是否已手动完成
  createdAt: string // ISO 日期时间
}

/** 今日日程条目（时间段可选） */
export interface ScheduleItem {
  id: string // 唯一标识
  title: string // 日程内容
  startTime?: string // 开始时间，如 "09:00"
  endTime?: string // 结束时间，如 "10:00"
  isCompleted: boolean // 是否已完成
  createdAt: string // ISO 日期时间
}

/** 自习室历史记录（按天汇总） */
export interface StudyHistoryRecord {
  date: string // 日期 YYYY-MM-DD
  completedPomodoros: number // 完成番茄钟数
  totalFocusMinutes: number // 总专注分钟数
}

/** 自习室数据存储结构 */
export interface StudyRoomData {
  todos: StudyTodo[]
  schedule: ScheduleItem[]
  history: StudyHistoryRecord[]
}
