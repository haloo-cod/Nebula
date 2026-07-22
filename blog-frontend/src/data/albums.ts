import type { Album } from '@/types'

/** 相册数据已由后端 API 提供，保留空 getter 兼容旧调用。 */
const albums: Album[] = []

export function getAlbums(): Album[] {
  return albums
}
