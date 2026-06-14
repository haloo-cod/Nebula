import { createRouter, createWebHashHistory, type RouteRecordRaw } from 'vue-router'

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
    // 从归档页进入文章:URL 带 /archive 前缀,使导航栏「归档」光标保持锁定
    path: '/archive/post/:slug',
    name: 'archive-post',
    component: () => import('../views/post/post.vue'),
  },
  {
    path: '/gallery',
    component: () => import('../views/gallery/gallery.vue'),
    children: [
      {
        path: '',
        name: 'gallery',
        component: () => import('../views/gallery/GalleryHome.vue'),
      },
      {
        path: ':module',
        name: 'gallery-module',
        component: () => import('../views/gallery/GalleryModule.vue'),
      },
    ],
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
    path: '/about',
    name: 'about',
    component: () => import('../views/about/about.vue'),
  },
  {
    path: '/post/:slug',
    name: 'post',
    component: () => import('../views/post/post.vue'),
  },
]

const router = createRouter({
  history: createWebHashHistory(import.meta.env.BASE_URL),
  routes,
})

export default router
