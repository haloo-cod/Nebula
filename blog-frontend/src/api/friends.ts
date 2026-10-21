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
interface ApiFriendItem {
  id: number
  name: string
  bio: string
  avatar: string
  url: string
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
