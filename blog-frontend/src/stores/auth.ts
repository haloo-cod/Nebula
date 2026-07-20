/**
 * 认证状态管理 Store
 * 管理 JWT token 的持久化、用户信息、登录/登出流程
 */

import { ref, computed } from 'vue'
import { defineStore } from 'pinia'
import { getToken, setToken, clearToken } from '@/api/client'
import {
  getMe,
  login as loginApi,
  logoutSession,
  refreshSession,
  register as registerApi,
  type LoginRequest,
  type RegisterRequest,
  type UserInfo,
} from '@/api/auth'

export const useAuthStore = defineStore('auth', () => {
  // ---------- 状态 ----------
  /** 当前用户信息,null 表示未登录/未拉取 */
  const user = ref<UserInfo | null>(null)
  /** 是否已经完成首次登录态恢复。 */
  const initialized = ref(false)
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

  /** 注册并立即建立登录态 */
  async function register(data: RegisterRequest): Promise<void> {
    const res = await registerApi(data)
    token.value = res.access_token
    setToken(res.access_token)
    await fetchUser()
  }

  /** 拉取当前用户信息（用于页面刷新后恢复登录态） */
  async function fetchUser(): Promise<void> {
    try {
      user.value = await getMe()
    } catch {
      // token 无效或过期,清除登录态
      clearSession()
    }
  }

  /** 登出：清除 token 和用户信息 */
  function clearSession(): void {
    token.value = null
    user.value = null
    clearToken()
  }

  /** 登出并撤销后端刷新会话。 */
  async function logout(): Promise<void> {
    try {
      await logoutSession()
    } finally {
      clearSession()
    }
  }

  /** 初始化：如果有 token 则尝试恢复用户信息 */
  async function init(forceRefresh = false): Promise<void> {
    try {
      // 匿名访客无需请求 refresh 接口，避免每次打开公开页面都产生预期内的 401。
      if (!token.value && !forceRefresh) {
        return
      }
      if (forceRefresh || !token.value) {
        const res = await refreshSession()
        token.value = res.access_token
        setToken(res.access_token)
      }
      if (token.value) await fetchUser()
    } catch {
      clearSession()
    } finally {
      initialized.value = true
    }
  }

  return {
    user,
    initialized,
    token,
    isLoggedIn,
    isAdmin,
    login,
    register,
    fetchUser,
    logout,
    init,
  }
})
