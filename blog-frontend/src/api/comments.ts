/**
 * 通用评论 API
 * 对应后端 /api/v1/comments 路由
 */

import { api } from './client'

/** 评论条目（含嵌套回复） */
export interface CommentItem {
  id: number
  author: string
  date: string
  content: string
  avatar_color: string
  children: CommentItem[]
}

interface CommentListResponse {
  items: CommentItem[]
  total: number
}

/** 获取指定页面的评论列表 */
export async function fetchComments(pageKey: string): Promise<CommentItem[]> {
  const res = await api.get<CommentListResponse>(
    `/api/v1/comments?page_key=${encodeURIComponent(pageKey)}`,
  )
  return res.items
}

/** 获取指定页面的评论总数 */
export async function fetchCommentCount(pageKey: string): Promise<number> {
  const res = await api.get<{ page_key: string; count: number }>(
    `/api/v1/comments/count?page_key=${encodeURIComponent(pageKey)}`,
  )
  return res.count
}

/** 批量获取多个页面的评论总数 */
export async function fetchBatchCommentCount(
  pageKeys: string[],
): Promise<Record<string, number>> {
  return api.post<Record<string, number>>('/api/v1/comments/batch-count', {
    page_keys: pageKeys,
  })
}

/** 发表评论 */
export async function postComment(
  pageKey: string,
  author: string,
  content: string,
  parentId?: number | null,
): Promise<CommentItem> {
  return api.post<CommentItem>('/api/v1/comments', {
    page_key: pageKey,
    author,
    content,
    parent_id: parentId || null,
  })
}

/** 删除评论（需认证） */
export async function deleteComment(pageKey: string, commentId: number): Promise<void> {
  await api.delete(`/api/v1/comments/${commentId}?page_key=${encodeURIComponent(pageKey)}`)
}
