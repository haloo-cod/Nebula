/**
 * 友链 API
 * 对应后端 /api/v1/friends 路由
 */

import { api, BASE_URL } from './client'
import type { Friend } from '@/types'
import { resolveRssUrl } from '@/utils/rss'

/** 交换友链展示信息。 */
export interface FriendExchangeInfo {
  name: string
  url: string
  avatar: string
  bio: string
  requirements: string[]
  contact: string
  rss_url: string
}

/** 首页与友链页共享订阅地址，留空时生成可复制的完整本站地址。 */
export function resolveFriendRssUrl(rssUrl = ''): string {
  return resolveRssUrl(rssUrl, BASE_URL, window.location.origin)
}

/** 后端返回的友链条目 */
export interface ApiFriendItem {
  id: number
  name: string
  bio: string
  avatar: string
  url: string
  rss_url: string
  sort_order: number
  created_at: string
}

/** 友链列表响应 */
interface FriendListResponse {
  items: ApiFriendItem[]
  total: number
}

/** 获取友链列表 */
export async function fetchFriends(): Promise<Friend[]> {
  const resp = await api.get<FriendListResponse>('/api/v1/friends')
  return resp.items.map((item) => ({
    name: item.name,
    bio: item.bio,
    avatar: item.avatar,
    url: item.url,
  }))
}

/** 获取交换友链展示信息。 */
export function fetchFriendExchangeInfo(): Promise<FriendExchangeInfo> {
  return api.get<FriendExchangeInfo>('/api/v1/friends/exchange-info')
}

/** 申请审核状态。 */
export type FriendApplicationStatus = 'pending' | 'approved' | 'rejected'

/** 申请提交字段；审核信息只由服务器赋值。 */
export interface FriendApplicationCreate {
  name: string
  url: string
  avatar: string
  email: string
  rss_url?: string
}

/** 所有访客可见的已通过申请。 */
export interface FriendApplicationPublic {
  id: number
  name: string
  url: string
  avatar: string
  rss_url: string
  created_at: string
  reviewed_at: string
  friend_id: number
}

/** 仅申请本人及管理员可见的申请。 */
export interface FriendApplicationPrivate {
  id: number
  name: string
  url: string
  avatar: string
  rss_url: string
  created_at: string
  reviewed_at: string | null
  friend_id: number | null
  email: string
  user_id: number | null
  status: FriendApplicationStatus
  review_note: string
}

/** 公开申请分页结果。 */
export interface FriendApplicationListResponse {
  items: FriendApplicationPublic[]
  total: number
}

/** 私有申请分页结果。 */
export interface FriendApplicationPrivateListResponse {
  items: FriendApplicationPrivate[]
  total: number
}

/** 管理员审核决策；拒绝必须提供原因。 */
export interface FriendApplicationReview {
  decision: 'approved' | 'rejected'
  reason?: string
}

/** 提交申请，不会直接公开。 */
export function submitFriendApplication(
  data: FriendApplicationCreate,
): Promise<FriendApplicationPrivate> {
  return api.post('/api/v1/friends/applications', data, true)
}

/** 获取已通过且仍关联正式友链的公开申请。 */
export function fetchFriendApplications(
  page = 1,
  pageSize = 10,
): Promise<FriendApplicationListResponse> {
  return api.get(`/api/v1/friends/applications?page=${page}&page_size=${pageSize}`)
}

/** 获取当前登录用户的申请历史。 */
export function fetchMyFriendApplications(
  page = 1,
  pageSize = 10,
): Promise<FriendApplicationPrivateListResponse> {
  return api.get(`/api/v1/friends/applications/mine?page=${page}&page_size=${pageSize}`, true)
}

/** 按审核状态获取管理员申请列表。 */
export function fetchAdminFriendApplications(
  status: FriendApplicationStatus | '',
  page = 1,
  pageSize = 20,
): Promise<FriendApplicationPrivateListResponse> {
  const params = new URLSearchParams({ page: String(page), page_size: String(pageSize) })
  if (status) params.set('status', status)
  return api.get(`/api/v1/friends/applications/admin?${params}`, true)
}

/** 审核申请，批准后自动创建正式友链。 */
export function reviewFriendApplication(
  id: number,
  data: FriendApplicationReview,
): Promise<FriendApplicationPrivate> {
  return api.patch(`/api/v1/friends/applications/${id}/review`, data, true)
}

/** 删除申请，已通过申请同时移除正式友链与讨论。 */
export function deleteFriendApplication(id: number): Promise<void> {
  return api.delete(`/api/v1/friends/applications/${id}`, true)
}

/** 只重新生成正式友链 JSON 副本。 */
export function syncFriendsJson(): Promise<void> {
  return api.post('/api/v1/friends/sync-json', undefined, true)
}
