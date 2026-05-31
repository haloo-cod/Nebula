import { createRouter, createWebHistory } from 'vue-router'

const router = createRouter({
  history: createWebHistory(import.meta.env.BASE_URL),
  routes: [
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
  ],
})

export default router
