import { createRouter, createWebHistory } from 'vue-router'
import index from '../views/index/index.vue'
import post from '../views/posts/post.vue'
import gallery from '../views/gallery/gallery.vue'
import other from '../views/other/other.vue'
import about from '../views/about/about.vue'

const router = createRouter({
  history: createWebHistory(import.meta.env.BASE_URL),
  routes: [
    {
      path: '/',
      name: 'index',
      component: index,
    },
    {
      path: '/post',
      name: 'post',
      component: post,
    },
    {
      path: '/gallery',
      name: 'gallery',
      component: gallery,
    },
    {
      path: '/other',
      name: 'other',
      component: other,
    },
    {
      path: '/about',
      name: 'about',
      component: about,
    },
  ],
})

export default router
