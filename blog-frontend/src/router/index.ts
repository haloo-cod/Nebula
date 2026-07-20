import {
  createRouter,
  createWebHashHistory,
  type RouteLocationNormalized,
  type RouteRecordRaw,
} from 'vue-router'
import { getToken } from '@/api/client'
import { useAuthStore } from '@/stores/auth'
import { recordAnalyticsEvent } from '@/api/analytics'

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
    meta: { hideRain: true },
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
    meta: { hideChrome: true, requiresAuth: true },
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
  {
    path: '/login',
    name: 'user-login',
    meta: { hideChrome: true },
    component: () => import('../views/auth/UserLogin.vue'),
  },
  {
    path: '/register',
    name: 'user-register',
    meta: { hideChrome: true },
    component: () => import('../views/auth/UserRegister.vue'),
  },
  {
    path: '/auth/callback',
    name: 'auth-callback',
    meta: { hideChrome: true },
    component: () => import('../views/auth/AuthCallback.vue'),
  },
  {
    path: '/verify-email',
    name: 'verify-email',
    meta: { hideChrome: true },
    component: () => import('../views/auth/VerifyEmail.vue'),
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
    meta: { hideChrome: true, requiresAuth: true, requiresAdmin: true },
    redirect: '/admin/dashboard',
    children: [
      {
        path: 'dashboard',
        name: 'admin-dashboard',
        component: () => import('../admin/views/dashboard/DashboardView.vue'),
      },
      {
        path: 'analytics/visitors',
        name: 'admin-analytics-visitors',
        component: () => import('../admin/views/analytics/VisitorList.vue'),
      },
      // ===== Phase 2: 核心 CRUD 页面 =====
      {
        path: 'posts',
        name: 'admin-posts',
        component: () => import('../admin/views/posts/PostList.vue'),
      },
      {
        path: 'posts/new',
        name: 'admin-post-create',
        component: () => import('../admin/views/posts/PostEditor.vue'),
      },
      {
        path: 'posts/:id',
        name: 'admin-post-edit',
        component: () => import('../admin/views/posts/PostEditor.vue'),
      },
      {
        path: 'moments',
        name: 'admin-moments',
        component: () => import('../admin/views/moments/MomentList.vue'),
      },
      {
        path: 'books',
        name: 'admin-books',
        component: () => import('../admin/views/books/BookList.vue'),
      },
      {
        path: 'files',
        name: 'admin-files',
        component: () => import('../admin/views/files/FileList.vue'),
      },
      {
        path: 'comments',
        name: 'admin-comments',
        component: () => import('../admin/views/comments/CommentList.vue'),
      },
      // ===== Phase 3: 内容管理页面 =====
      {
        path: 'gallery',
        name: 'admin-gallery',
        component: () => import('../admin/views/gallery/GalleryList.vue'),
      },
      {
        path: 'albums',
        name: 'admin-albums',
        component: () => import('../admin/views/albums/AlbumList.vue'),
      },
      {
        path: 'friends',
        name: 'admin-friends',
        component: () => import('../admin/views/friends/FriendList.vue'),
      },
      {
        path: 'treasures',
        name: 'admin-treasures',
        component: () => import('../admin/views/treasures/TreasureList.vue'),
      },
      {
        path: 'tavern',
        name: 'admin-tavern',
        component: () => import('../admin/views/tavern/TavernList.vue'),
      },
      // ===== Phase 4: 配置与媒体管理 =====
      {
        path: 'carousel',
        name: 'admin-carousel',
        component: () => import('../admin/views/carousel/CarouselList.vue'),
      },
      {
        path: 'backgrounds',
        name: 'admin-backgrounds',
        component: () => import('../admin/views/backgrounds/BackgroundList.vue'),
      },
      {
        path: 'about',
        name: 'admin-about',
        component: () => import('../admin/views/about/AboutEditor.vue'),
      },
      {
        path: 'users',
        name: 'admin-users',
        component: () => import('../admin/views/users/UserList.vue'),
      },
      {
        path: 'profile',
        name: 'admin-profile',
        component: () => import('../admin/views/profile/ProfileEdit.vue'),
      },
      {
        path: 'site',
        name: 'admin-site',
        component: () => import('../admin/views/site/SiteConfig.vue'),
      },
    ],
  },
]

const router = createRouter({
  history: createWebHashHistory(import.meta.env.BASE_URL),
  routes,
})

/** 记录前台成功导航，后台和认证页面不纳入公开访问统计。 */
router.afterEach((to) => {
  if (
    to.path.startsWith('/admin') ||
    ['/login', '/register', '/auth/callback', '/verify-email'].includes(to.path)
  ) {
    return
  }
  const key = 'starlit_visitor_id'
  let visitorId = localStorage.getItem(key)
  if (!visitorId) {
    visitorId = crypto.randomUUID()
    localStorage.setItem(key, visitorId)
  }
  void recordAnalyticsEvent({
    event_type: 'page_view',
    path: to.fullPath,
    title: typeof to.meta.title === 'string' ? to.meta.title : to.name?.toString() || to.path,
    referrer: document.referrer,
    visitor_id: visitorId,
  }).catch(() => undefined)
})

// ---------------------------------------------------------------------------
// 导航守卫：管理后台需要登录
// ---------------------------------------------------------------------------
router.beforeEach((to) => {
  // 只拦截 requiresAuth 的路由
  const requiresAuth = to.matched.some((record) => record.meta.requiresAuth)
  if (!requiresAuth) return true

  const auth = useAuthStore()
  if (!auth.initialized) {
    return auth.init().then(() => checkAuthentication(to, auth))
  }

  return checkAuthentication(to, auth)
})

/** 检查受保护路由的登录状态和管理员权限。 */
function checkAuthentication(to: RouteLocationNormalized, auth: ReturnType<typeof useAuthStore>) {
  const token = getToken()
  if (!token || !auth.user) {
    const loginPath = to.path.startsWith('/admin') ? '/admin/login' : '/login'
    return { path: loginPath, query: { redirect: to.fullPath } }
  }

  if (to.matched.some((record) => record.meta.requiresAdmin) && !auth.isAdmin) {
    return { path: '/', query: { error: 'admin_required' } }
  }

  // 普通用户即使已登录，也必须由后端管理员权限保护最终接口访问。

  return true
}

export default router
