/**
 * 认证状态管理 Store
 * 管理 JWT token 的持久化、用户信息、登录/登出流程
 */

import { ref, computed } from 'vue'
import { defineStore } from 'pinia'
import { getToken, setToken, clearToken } from '@/api/client'
import { login as loginApi, getMe, type UserInfo, type LoginRequest } from '@/api/auth'

export const useAuthStore = defineStore('auth', () => {
  // ---------- 状态 ----------
  /** 当前用户信息,null 表示未登录/未拉取 */
  const user = ref<UserInfo | null>(null)
  /** token 是否存在（从 localStorage 读取） */
  const token = ref<string | null>(getToken())

  // ---------- 计算属性 ----------
  /** 是否已登录（token 存在且用户信息已加载） */
  const isLoggedIn = computed(() => !!token.value && !!user.value)
  /** 是否为管理员 */
  const isAdmin = computed(() => user.value?.is_admin ?? false)

  // ---------- 操作 ----------

  /** 登录：调用 API 获取 token，然后拉取用户信息 */
  async function login(data: LoginRequest): Promise<void> {
    const res = await loginApi(data)
    token.value = res.access_token
    setToken(res.access_token)
    // 登录成功后立即获取用户信息
    await fetchUser()
  }

  /** 拉取当前用户信息（用于页面刷新后恢复登录态） */
  async function fetchUser(): Promise<void> {
    try {
      user.value = await getMe()
    } catch {
      // token 无效或过期,清除登录态
      logout()
    }
  }

  /** 登出：清除 token 和用户信息 */
  function logout(): void {
    token.value = null
    user.value = null
    clearToken()
  }

  /** 初始化：如果有 token 则尝试恢复用户信息 */
  async function init(): Promise<void> {
    if (token.value) {
      await fetchUser()
    }
  }

  return {
    user,
    token,
    isLoggedIn,
    isAdmin,
    login,
    fetchUser,
    logout,
    init,
  }
})
