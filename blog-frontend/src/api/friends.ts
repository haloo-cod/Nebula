/**
 * 友链 API
 * 对应后端 /api/v1/friends 路由
 */

import { api } from './client'
import type { Friend } from '@/types'

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
