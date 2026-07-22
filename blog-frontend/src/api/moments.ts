/**
 * 说说 API
 * 对应后端 /api/v1/moments 路由
 */

import { api, resolveUrl } from './client'
import type { Moment, MomentComment } from '@/types'

/** 后端说说响应（含评论数组） */
export interface MomentResponse {
  id: number
  date: string
  content: string
  mood: string
  tags: string[]
  images: string[]
  likes: number
  comments: MomentComment[]
}

interface MomentListResponse {
  items: MomentResponse[]
  total: number
}

/** 获取说说列表（分页） */
export async function fetchMoments(
  page = 1,
  pageSize = 10,
): Promise<{ items: Moment[]; total: number }> {
  const res = await api.get<MomentListResponse>(
    `/api/v1/moments?page=${page}&page_size=${pageSize}`,
  )
  // 转为前端 Moment 类型（图片 URL 补全）
  const items: Moment[] = res.items.map((m) => ({
    id: m.id,
    date: m.date,
    content: m.content,
    mood: m.mood,
    tags: m.tags,
    images: m.images.map(resolveUrl),
    likes: m.likes,
    commentCount: m.comments?.length || 0,
  }))
  return { items, total: res.total }
}

/** 获取单条说说详情 */
export async function fetchMoment(id: number): Promise<MomentResponse> {
  return api.get<MomentResponse>(`/api/v1/moments/${id}`)
}

/** 点赞说说 */
export async function likeMoment(id: number): Promise<{ likes: number }> {
  return api.post<{ likes: number }>(`/api/v1/moments/${id}/like`)
}

/** 获取说说评论 */
export async function fetchMomentComments(id: number): Promise<MomentComment[]> {
  return api.get<MomentComment[]>(`/api/v1/moments/${id}/comments`)
}

/** 发表说说评论 */
export async function postMomentComment(
  id: number,
  nickname: string,
  content: string,
): Promise<MomentComment> {
  return api.post<MomentComment>(`/api/v1/moments/${id}/comments`, {
    nickname,
    content,
  })
}
