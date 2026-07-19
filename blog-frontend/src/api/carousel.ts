/**
 * 首页轮播图 API
 * 对应后端 /api/v1/carousel 路由
 */

import { api, resolveUrl } from './client'

/** 轮播图条目 */
interface CarouselSlideItem {
  id: number
  url: string
  sort_order: number
}

/** 轮播图列表响应 */
interface CarouselListResponse {
  items: CarouselSlideItem[]
  total: number
}

/**
 * 获取首页轮播图列表
 * 返回已排序的图片 URL 数组
 */
export async function fetchCarouselSlides(): Promise<string[]> {
  const resp = await api.get<CarouselListResponse>('/api/v1/carousel')
  return resp.items.map((item) => resolveUrl(item.url))
}
