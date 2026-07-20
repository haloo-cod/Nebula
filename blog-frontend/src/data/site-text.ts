/**
 * 站点页面文案集中管理
 * 各页面的 kicker / title / subtitle 统一在此定义，避免散落在各 .vue 模板中。
 * 后续可对接后端 SiteConfig API，管理员后台修改后优先使用 API 值。
 */

/** 单个页面的文案结构 */
export interface PageText {
  kicker: string // 英文小标题（如 "Images"）
  title: string // 中文主标题（如 "图片"）
  subtitle: string // 副标题/描述（如 "定格时间，封存每一次心跳。"）
}

/** 全站页面文案配置 */
export const siteText: Record<string, PageText> = {
  images: {
    kicker: 'Images',
    title: '图片',
    subtitle: '定格时间，封存每一次心跳。',
  },
  friends: {
    kicker: 'Friends',
    title: '友链',
    subtitle: '一些有趣、温和且持续发光的站点。',
  },
  treasure: {
    kicker: 'Treasure',
    title: '藏宝阁',
    subtitle: '收集有趣的开源项目和实用资源，未来会提供文件下载。',
  },
  moments: {
    kicker: 'Moments',
    title: '说说',
    subtitle: '一些碎碎念，和偶然闪过的灵感。',
  },
  books: {
    kicker: 'Library',
    title: '图书',
    subtitle: '一块一块的玻璃书格。点击任意图书后进入全屏 EPUB 阅读器。',
  },
  gallery: {
    kicker: 'Projects',
    title: '项目',
    subtitle: '点击项目卡片进入独立 Markdown 文档，不进入博客归档和统计。',
  },
  blog: {
    kicker: 'Blog',
    title: '博文',
    subtitle: '一片一片的玻璃卡片。点击任意卡片进入文章页。',
  },
}
