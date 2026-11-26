/**
 * 管理后台侧边栏菜单配置
 * 按「概览 / 内容 / 互动 / 系统」4 大分组组织全部 19 个管理模块。
 */

/** 单个菜单项定义 */
export interface AdminMenuItem {
  /** 路由路径 */
  path: string
  /** 菜单标题 */
  title: string
  /** Element Plus 图标组件名 */
  icon: string
  /** 供命令面板检索的附加关键词 */
  keywords?: string
}

/** 菜单分组定义 */
export interface AdminMenuGroup {
  /** 分组唯一标识 */
  key: string
  /** 分组中文标题 */
  title: string
  /** 分组下属菜单项 */
  items: AdminMenuItem[]
}

/** 分组菜单配置 */
export const adminMenuGroups: AdminMenuGroup[] = [
  {
    key: 'overview',
    title: '概览',
    items: [
      { path: '/admin/dashboard', title: '仪表盘', icon: 'Odometer', keywords: 'dashboard stats overview 统计' },
      { path: '/admin/analytics/visitors', title: '访问记录', icon: 'DataAnalysis', keywords: 'visitors analytics ip 日志' },
    ],
  },
  {
    key: 'content',
    title: '内容',
    items: [
      { path: '/admin/posts', title: '文章管理', icon: 'Document', keywords: 'posts blog markdown 博文' },
      { path: '/admin/moments', title: '说说管理', icon: 'ChatDotRound', keywords: 'moments 动态 碎碎念' },
      { path: '/admin/books', title: '图书管理', icon: 'Reading', keywords: 'books epub 书库' },
      { path: '/admin/files', title: '文件管理', icon: 'FolderOpened', keywords: 'files images media 图床 媒体' },
      { path: '/admin/gallery', title: '展览管理', icon: 'Picture', keywords: 'gallery projects 项目' },
      { path: '/admin/albums', title: '相册管理', icon: 'Camera', keywords: 'albums photos 照片' },
      { path: '/admin/treasures', title: '藏宝阁', icon: 'Present', keywords: 'treasures tools 资源 工具' },
    ],
  },
  {
    key: 'community',
    title: '互动',
    items: [
      { path: '/admin/comments', title: '评论管理', icon: 'Comment', keywords: 'comments 留言' },
      { path: '/admin/friends', title: '友链管理', icon: 'Connection', keywords: 'friends links 申请' },
      { path: '/admin/tavern', title: '深夜酒馆', icon: 'ColdDrink', keywords: 'tavern 酒馆' },
    ],
  },
  {
    key: 'system',
    title: '系统',
    items: [
      { path: '/admin/carousel', title: '轮播管理', icon: 'Film', keywords: 'carousel 首页轮播' },
      { path: '/admin/backgrounds', title: '背景图', icon: 'Sunrise', keywords: 'backgrounds 壁纸 视频背景' },
      { path: '/admin/about', title: '关于页', icon: 'EditPen', keywords: 'about 自我介绍' },
      { path: '/admin/users', title: '用户管理', icon: 'UserFilled', keywords: 'users accounts 账户 权限' },
      { path: '/admin/profile', title: '个人资料', icon: 'User', keywords: 'profile avatar 社交链接' },
      { path: '/admin/site', title: '站点配置', icon: 'Setting', keywords: 'site config 设置' },
      { path: '/admin/storage/r2-migration', title: 'R2 迁移', icon: 'UploadFilled', keywords: 'r2 storage cloudflare 存储' },
    ],
  },
]

/** 扁平菜单列表（兼容既有调用方） */
export const adminMenus: AdminMenuItem[] = adminMenuGroups.flatMap((group) => group.items)

/** 根据当前路由路径查找所属分组与菜单项 */
export function findAdminMenuContext(path: string): {
  groupTitle: string
  item: AdminMenuItem | null
} {
  for (const group of adminMenuGroups) {
    const matched = group.items.find((item) => path === item.path || path.startsWith(`${item.path}/`))
    if (matched) return { groupTitle: group.title, item: matched }
  }
  return { groupTitle: '工作台', item: null }
}
