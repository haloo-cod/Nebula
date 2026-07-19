/**
 * 相册 API
 * 对应后端 /api/v1/albums 路由
 */

import { api, resolveUrl } from './client'
import type { Album, AlbumPhoto } from '@/types'

/** 后端返回的照片条目 */
interface ApiPhoto {
  id: number
  url: string
  caption: string | null
  sort_order: number
  created_at: string
}

/** 后端返回的相册列表项 */
interface ApiAlbumItem {
  id: number
  title: string
  description: string
  orientation: string
  cover_url: string
  photo_count: number
  date: string
  created_at: string
  preview_photos: ApiPhoto[]
}

/** 后端返回的相册详情 */
interface ApiAlbumDetail extends ApiAlbumItem {
  photos: ApiPhoto[]
}

/** 相册列表响应 */
interface AlbumListResponse {
  items: ApiAlbumItem[]
  total: number
}

/** 获取相册列表 */
export async function fetchAlbums(): Promise<Album[]> {
  const resp = await api.get<AlbumListResponse>('/api/v1/albums')
  return resp.items.map((item) => toFrontendAlbum(item))
}

/** 获取相册详情（含完整照片列表） */
export async function fetchAlbumDetail(albumId: number): Promise<Album> {
  const detail = await api.get<ApiAlbumDetail>(`/api/v1/albums/${albumId}`)
  return toFrontendAlbumDetail(detail)
}

/** 将 API 列表项转为前端 Album 类型（photos 取 preview_photos 用于卡片堆叠） */
function toFrontendAlbum(item: ApiAlbumItem): Album {
  const photos: AlbumPhoto[] = item.preview_photos.map((p) => ({
    url: resolveUrl(p.url),
    caption: p.caption || undefined,
  }))

  return {
    id: String(item.id),
    title: item.title,
    description: item.description,
    cover: resolveUrl(item.cover_url),
    date: item.date,
    orientation: item.orientation as 'landscape' | 'portrait',
    photos,
  }
}

/** 将 API 详情转为前端 Album 类型（含完整照片） */
function toFrontendAlbumDetail(detail: ApiAlbumDetail): Album {
  const photos: AlbumPhoto[] = detail.photos.map((p) => ({
    url: resolveUrl(p.url),
    caption: p.caption || undefined,
  }))

  return {
    id: String(detail.id),
    title: detail.title,
    description: detail.description,
    cover: resolveUrl(detail.cover_url),
    date: detail.date,
    orientation: detail.orientation as 'landscape' | 'portrait',
    photos,
  }
}
