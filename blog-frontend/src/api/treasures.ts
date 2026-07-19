/**
 * 藏宝阁 API
 * 对应后端 /api/v1/treasures 路由
 */

import { api } from './client'
import type { Treasure, TreasureCategory } from '@/types'

/** 后端返回的藏宝条目 */
interface ApiTreasureItem {
  id: number
  slug: string
  title: string
  description: string
  category: string
  icon: string
  url: string
  download_file: string
  tags: string[]
  sort_order: number
  created_at: string
}

/** 藏宝列表响应 */
interface TreasureListResponse {
  items: ApiTreasureItem[]
  total: number
}

/** 获取藏宝列表（可按分类筛选） */
export async function fetchTreasures(category?: string): Promise<Treasure[]> {
  const query = category ? `?category=${encodeURIComponent(category)}` : ''
  const resp = await api.get<TreasureListResponse>(`/api/v1/treasures${query}`)
  return resp.items.map((item) => ({
    slug: item.slug,
    title: item.title,
    description: item.description,
    category: item.category as TreasureCategory,
    icon: item.icon,
    url: item.url,
    downloadUrl: item.download_file || undefined,
    tags: item.tags,
  }))
}

/** 获取所有分类列表 */
export async function fetchTreasureCategories(): Promise<TreasureCategory[]> {
  return api.get<TreasureCategory[]>('/api/v1/treasures/categories')
}
