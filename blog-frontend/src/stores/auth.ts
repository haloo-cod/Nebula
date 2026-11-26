/**
 * 认证状态管理 Store
 * 管理 JWT token 的持久化、用户信息、登录/登出流程
 */

import { ref, computed, onScopeDispose } from 'vue'
import { defineStore } from 'pinia'
import { getToken, setToken, clearToken, subscribeToken } from '@/api/client'
import {
  getMe,
  login as loginApi,
  logoutSession,
  refreshSession,
  register as registerApi,
  type LoginRequest,
  type RegisterRequest,
  type RegisterResponse,
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
  let sessionVersion = 0
  const unsubscribe = subscribeToken((value, sessionChanged) => {
    token.value = value
    if (sessionChanged) {
      sessionVersion += 1
      user.value = null
    }
  })
  onScopeDispose(unsubscribe)

  // ---------- 计算属性 ----------
  /** 是否已登录（token 存在且用户信息已加载） */
  const isLoggedIn = computed(() => !!token.value && !!user.value)
  /** 是否为管理员 */
  const isAdmin = computed(() => user.value?.is_admin ?? false)

  // ---------- 操作 ----------

  /** 登录：调用 API 获取 token，然后拉取用户信息 */
  async function login(data: LoginRequest): Promise<void> {
    const res = await loginApi(data)
    setToken(res.access_token)
    // 登录成功后立即获取用户信息
    await fetchUser()
  }

  /** 注册并立即建立登录态 */
  async function register(data: RegisterRequest): Promise<RegisterResponse> {
    const res = await registerApi(data)
    if (res.requires_email_verification || !res.access_token) return res
    setToken(res.access_token)
    await fetchUser()
    return res
  }

  /** 拉取当前用户信息（用于页面刷新后恢复登录态） */
  async function fetchUser(): Promise<void> {
    const version = sessionVersion
    const currentUser = await getMe()
    if (version === sessionVersion && token.value) user.value = currentUser
  }

  /** 登出：清除 token 和用户信息 */
  function clearSession(): void {
    clearToken()
  }

  /** 登出并撤销后端刷新会话。 */
  async function logout(): Promise<void> {
    clearSession()
    await logoutSession()
  }

  /** 初始化：如果有 token 则尝试恢复用户信息 */
  async function init(forceRefresh = false): Promise<void> {
    try {
      // 匿名访客无需请求 refresh 接口，避免每次打开公开页面都产生预期内的 401。
      if (!token.value && !forceRefresh) {
        return
      }
      if (forceRefresh || !token.value) {
        await refreshSession()
      }
      if (token.value) await fetchUser()
    } catch {
      // 终止性刷新错误由客户端同步清理；网络和服务端异常保留可恢复的会话。
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
