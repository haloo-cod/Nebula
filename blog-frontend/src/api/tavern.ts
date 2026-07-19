/**
 * 深夜酒馆 API
 * 对应后端 /api/v1/tavern 路由
 */

import { api } from './client'

/** 酒馆留言条目 */
export interface TavernPost {
  id: number
  author: string
  topic: string
  body: string
  created_at: string
}

/** 留言列表响应 */
interface TavernListResponse {
  items: TavernPost[]
  total: number
}

/** 获取可见留言列表 */
export async function fetchTavernPosts(): Promise<TavernPost[]> {
  const resp = await api.get<TavernListResponse>('/api/v1/tavern')
  return resp.items
}

/** 发布留言（匿名） */
export async function submitTavernPost(
  author: string,
  topic: string,
  body: string,
): Promise<TavernPost> {
  return api.post<TavernPost>('/api/v1/tavern', { author, topic, body })
}
