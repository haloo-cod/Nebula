/**
 * 博文 API
 * 对应后端 /api/v1/posts 路由
 */

import { api, resolveUrl } from './client'
import type { Post, PostStat } from '@/types'

/** 后端返回的博文详情（含 Markdown 原文） */
export interface PostDetail {
  id: number
  slug: string
  title: string
  description: string
  date: string
  cover_url: string
  category: string
  tags: string[]
  is_draft: boolean
  is_pinned: boolean
  content_md: string
  content_html: string
  created_at: string
  updated_at: string
}

/** 后端返回的博文列表项 */
export interface PostListItem {
  id: number
  slug: string
  title: string
  description: string
  date: string
  cover_url: string
  category: string
  tags: string[]
  is_draft: boolean
  is_pinned: boolean
  created_at: string
}

interface PostListResponse {
  items: PostListItem[]
  total: number
}

/** 获取博文列表（分页 + 分类筛选） */
export async function fetchPosts(
  page = 1,
  pageSize = 12,
  category = '',
): Promise<{ items: PostListItem[]; total: number }> {
  let path = `/api/v1/posts?page=${page}&page_size=${pageSize}`
  if (category) path += `&category=${encodeURIComponent(category)}`
  return api.get<PostListResponse>(path)
}

/** 获取博文详情（含 Markdown 原文） */
export async function fetchPost(slug: string): Promise<PostDetail> {
  return api.get<PostDetail>(`/api/v1/posts/${encodeURIComponent(slug)}`)
}

/** 获取按年统计数据 */
export async function fetchPostStats(): Promise<PostStat[]> {
  return api.get<PostStat[]>('/api/v1/posts/stats')
}

/**
 * 将后端 PostListItem 转为前端 Post 类型（兼容现有组件）
 * 注意：content 字段为空，需要单独获取详情
 */
export function toFrontendPost(item: PostListItem): Post {
  return {
    slug: item.slug,
    title: item.title,
    description: item.description,
    date: item.date,
    cover: resolveUrl(item.cover_url),
    tags: item.tags,
    category: item.category,
    draft: item.is_draft,
    pinned: item.is_pinned,
    content: '',
  }
}
