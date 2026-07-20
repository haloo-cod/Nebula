/**
 * 图书 API
 * 对应后端 /api/v1/books 路由
 */

import { api, resolveUrl } from './client'
import type { Book } from '@/types'

/** 后端返回的图书列表项 */
export interface BookApiItem {
  id: number
  slug: string
  title: string
  author: string
  description: string
  cover_url: string
  file_path: string
  sort_order: number
  created_at: string
}

/** 后端返回的图书详情 */
export interface BookApiDetail {
  id: number
  slug: string
  title: string
  author: string
  description: string
  cover_url: string
  file_path: string
  sort_order: number
  created_at: string
  updated_at: string
}

/** 后端图书列表响应（含分页） */
interface BookListResponse {
  items: BookApiItem[]
  total: number
}

/**
 * 获取图书列表（后端分页 + 关键词搜索）
 * @param page 页码（从 1 开始）
 * @param pageSize 每页数量
 * @param keyword 搜索关键词（匹配标题/作者）
 */
export async function fetchBooks(
  page = 1,
  pageSize = 20,
  keyword = '',
): Promise<{ items: Book[]; total: number }> {
  let path = `/api/v1/books?page=${page}&page_size=${pageSize}`
  if (keyword.trim()) path += `&keyword=${encodeURIComponent(keyword.trim())}`
  const resp = await api.get<BookListResponse>(path)
  return {
    items: resp.items.map(toFrontendBook),
    total: resp.total,
  }
}

/** 获取单本图书 */
export async function fetchBook(slug: string): Promise<Book> {
  const item = await api.get<BookApiDetail>(`/api/v1/books/${encodeURIComponent(slug)}`)
  return toFrontendBook(item)
}

/** API 数据 → 前端 Book 类型 */
function toFrontendBook(item: BookApiItem): Book {
  return {
    slug: item.slug,
    title: item.title,
    author: item.author,
    description: item.description,
    cover: resolveUrl(item.cover_url),
    file: item.file_path,
  }
}
