/**
 * 管理后台侧边栏菜单配置
 * 定义菜单项的路由路径、图标、标题
 */

export interface AdminMenuItem {
  /** 路由路径 */
  path: string
  /** 菜单标题 */
  title: string
  /** Element Plus 图标组件名 */
  icon: string
}

/** 管理后台菜单列表 */
export const adminMenus: AdminMenuItem[] = [
  { path: '/admin/dashboard', title: '仪表盘', icon: 'Odometer' },
  { path: '/admin/analytics/visitors', title: '访问记录', icon: 'DataAnalysis' },
  { path: '/admin/posts', title: '文章管理', icon: 'Document' },
  { path: '/admin/moments', title: '说说管理', icon: 'ChatDotRound' },
  { path: '/admin/books', title: '图书管理', icon: 'Reading' },
  { path: '/admin/files', title: '文件管理', icon: 'FolderOpened' },
  { path: '/admin/gallery', title: '展览管理', icon: 'Picture' },
  { path: '/admin/albums', title: '相册管理', icon: 'Camera' },
  { path: '/admin/friends', title: '友链管理', icon: 'Connection' },
  { path: '/admin/treasures', title: '藏宝阁', icon: 'Present' },
  { path: '/admin/tavern', title: '深夜酒馆', icon: 'ColdDrink' },
  { path: '/admin/comments', title: '评论管理', icon: 'Comment' },
  { path: '/admin/carousel', title: '轮播管理', icon: 'Film' },
  { path: '/admin/backgrounds', title: '背景图', icon: 'Sunrise' },
  { path: '/admin/about', title: '关于页', icon: 'EditPen' },
  { path: '/admin/users', title: '用户管理', icon: 'UserFilled' },
  { path: '/admin/profile', title: '个人资料', icon: 'User' },
  { path: '/admin/site', title: '站点配置', icon: 'Setting' },
]
