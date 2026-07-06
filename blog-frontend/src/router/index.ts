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
]

const router = createRouter({
  history: createWebHashHistory(import.meta.env.BASE_URL),
  routes,
})

export default router
