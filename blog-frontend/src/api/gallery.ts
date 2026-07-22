/**
 * 展览页 API
 * 对应后端 /api/v1/gallery 路由
 */

import { api } from './client'
import type { GalleryProject } from '@/types'

/** 后端返回的展览项目列表项 */
export interface GalleryListItem {
  id: number
  slug: string
  title: string
  description: string
  tags: string[]
  status: string
  year: string
  is_featured: boolean
  created_at: string
}

/** 后端返回的展览项目详情 */
export interface GalleryDetail {
  id: number
  slug: string
  title: string
  description: string
  tags: string[]
  status: string
  year: string
  is_featured: boolean
  content_md: string
  content_html: string
  created_at: string
  updated_at: string
}

/** 获取展览项目列表 */
export async function fetchGalleryProjects(): Promise<GalleryListItem[]> {
  return api.get<GalleryListItem[]>('/api/v1/gallery')
}

/** 获取展览项目详情 */
export async function fetchGalleryProject(slug: string): Promise<GalleryDetail> {
  return api.get<GalleryDetail>(`/api/v1/gallery/${encodeURIComponent(slug)}`)
}

/** 将 API 列表项转为前端 GalleryProject 类型（content 为空，详情页再加载） */
export function toFrontendGalleryProject(item: GalleryListItem): GalleryProject {
  return {
    slug: item.slug,
    title: item.title,
    description: item.description,
    tags: item.tags,
    status: item.status,
    year: item.year,
    featured: item.is_featured,
    content: '',
  }
}
