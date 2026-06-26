import { ref } from 'vue'
import { defineStore } from 'pinia'

/** 全局 UI 状态 — 控制导航栏等全局组件的显隐时机 */
export const useUIStore = defineStore('ui', () => {
  const showNavbar = ref(true)

  return { showNavbar }
})
