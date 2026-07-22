/**
 * 认证相关 API
 * 对接后端 /api/v1/auth 模块（登录、获取当前用户信息）
 */

import { api } from './client'

/** 登录请求参数 */
export interface LoginRequest {
  username: string
  password: string
}

/** 普通用户注册请求 */
export interface RegisterRequest {
  username: string
  email: string
  password: string
}

/** 登录响应（JWT） */
export interface TokenResponse {
  access_token: string
  token_type: string
}

/** 当前用户信息 */
export interface UserInfo {
  id: number
  username: string
  is_admin: boolean
  email: string | null
  display_name: string
  avatar_url: string
  email_verified: boolean
}

/** 管理员登录 */
export function login(data: LoginRequest): Promise<TokenResponse> {
  return api.post<TokenResponse>('/api/v1/auth/login', data)
}

/** 用户名、邮箱和密码注册 */
export function register(data: RegisterRequest): Promise<TokenResponse> {
  return api.post<TokenResponse>('/api/v1/auth/register', data)
}

/** 使用 Refresh Cookie 恢复访问令牌 */
export function refreshSession(): Promise<TokenResponse> {
  return api.post<TokenResponse>('/api/v1/auth/refresh')
}

/** 撤销当前登录会话 */
export function logoutSession(): Promise<void> {
  return api.post<void>('/api/v1/auth/logout')
}

/** 获取当前登录用户信息（需要 token） */
export function getMe(): Promise<UserInfo> {
  return api.get<UserInfo>('/api/v1/auth/me', true)
}
