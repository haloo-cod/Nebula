import { createRouter, createWebHashHistory, type RouteRecordRaw } from 'vue-router'
import { getToken } from '@/api/client'

// 路由表(未做懒加载拆分按需可加)
const routes: RouteRecordRaw[] = [
  {
    path: '/',
    name: 'index',
    component: () => import('../views/index/index.vue'),
  },
  {
    path: '/archive',
    name: 'archive',
    component: () => import('../views/archive/archive.vue'),
  },
  {
    path: '/books',
    name: 'books',
    component: () => import('../views/books/books.vue'),
  },
  {
    path: '/books/read/:slug',
    name: 'book-reader',
    component: () => import('../views/books/reader.vue'),
  },
  {
    path: '/blog',
    name: 'blog',
    component: () => import('../views/blog/blog.vue'),
  },
  {
    path: '/images',
    name: 'images',
    component: () => import('../views/images/images.vue'),
  },
  {
    path: '/archive/tree',
    name: 'archive-tree',
    component: () => import('../views/archive/ArchiveTreePoster.vue'),
  },
  {
    // 从归档页进入文章:URL 带 /archive 前缀,使导航栏「归档」光标保持锁定
    path: '/archive/post/:slug',
    name: 'archive-post',
    component: () => import('../views/post/post.vue'),
  },
  {
    path: '/gallery',
    name: 'gallery',
    component: () => import('../views/gallery/gallery.vue'),
  },
  {
    path: '/gallery/project/:slug',
    name: 'gallery-project',
    component: () => import('../views/gallery/project.vue'),
  },
  {
    path: '/friends',
    name: 'friends',
    component: () => import('../views/friends/friends.vue'),
  },
  {
    path: '/treasure',
    name: 'treasure',
    component: () => import('../views/treasure/treasure.vue'),
  },
  {
    path: '/midnight-tavern',
    name: 'midnight-tavern',
    meta: { hideChrome: true },
    component: () => import('../views/midnight-tavern/midnight-tavern.vue'),
  },
  {
    path: '/about',
    name: 'about',
    component: () => import('../views/about/about.vue'),
  },
  {
    path: '/post/:slug',
    name: 'post',
    component: () => import('../views/post/post.vue'),
  },
  {
    path: '/moments',
    name: 'moments',
    component: () => import('../views/moments/moments.vue'),
  },
  {
    path: '/study-room',
    name: 'study-room',
    component: () => import('../views/study-room/study-room.vue'),
  },

  // =========================================================================
  // 管理后台路由
  // =========================================================================

  {
    // 登录页（独立全屏,不使用 AdminLayout）
    path: '/admin/login',
    name: 'admin-login',
    meta: { hideChrome: true },
    component: () => import('../admin/views/login/LoginView.vue'),
  },
  {
    // 管理后台主路由（带 AdminLayout 侧边栏+顶栏）
    path: '/admin',
    component: () => import('../admin/layout/AdminLayout.vue'),
    meta: { hideChrome: true, requiresAuth: true },
    redirect: '/admin/dashboard',
    children: [
      {
        path: 'dashboard',
        name: 'admin-dashboard',
        component: () => import('../admin/views/dashboard/DashboardView.vue'),
      },
      // Phase 2/3/4 的管理页面将在此处追加
    ],
  },
]

const router = createRouter({
  history: createWebHashHistory(import.meta.env.BASE_URL),
  routes,
})

// ---------------------------------------------------------------------------
// 导航守卫：管理后台需要登录
// ---------------------------------------------------------------------------
router.beforeEach((to) => {
  // 只拦截 requiresAuth 的路由
  const requiresAuth = to.matched.some((record) => record.meta.requiresAuth)
  if (!requiresAuth) return true

  const token = getToken()
  if (!token) {
    // 未登录,重定向到登录页
    return { path: '/admin/login', query: { redirect: to.fullPath } }
  }

  return true
})

export default router
