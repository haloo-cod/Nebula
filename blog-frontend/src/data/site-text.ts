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
    subtitle: '分享好看的图片',
  },
  friends: {
    kicker: 'Friends',
    title: '友链',
    subtitle: '想做海洋馆的样子，收集互联网茫茫大海里有趣的朋友们。',
  },
  treasure: {
    kicker: 'Treasure',
    title: '藏宝阁',
    subtitle: '收集有趣的开源项目和实用工具，也会提供一些日轻的资源下载',
  },
  moments: {
    kicker: 'Moments',
    title: '说说',
    subtitle: '一些碎碎念，一些心情，一些生活的点滴。',
  },
  books: {
    kicker: 'Library',
    title: '图书',
    subtitle: '分享一些小说，大多数我自己看过然后再上来的（资源来自网络，如有侵权，深感抱歉，请立即联系我删除）',
  },
  gallery: {
    kicker: 'Projects',
    title: '项目',
    subtitle: '记录下自己做的一些项目',
  },
  blog: {
    kicker: 'Blog',
    title: '博文',
    subtitle: '记录下自己的一些想法和生活',
  },
}
