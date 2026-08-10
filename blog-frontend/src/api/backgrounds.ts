import { api, resolveUrl } from './client'

export interface ApiBgItem {
  id: number
  url: string
  theme: string
  device: string
  sort_order: number
  created_at: string
  media_type?: 'image' | 'video'
  poster_url?: string
  mime_type?: string
  file_size?: number
  mediaType?: 'image' | 'video'
  posterUrl?: string
  mimeType?: string
  fileSize?: number
}

interface BgListResponse {
  items: ApiBgItem[]
  total: number
}

export async function fetchBackgrounds(theme: string, device: string): Promise<ApiBgItem[]> {
  const resp = await api.get<BgListResponse>(`/api/v1/backgrounds?theme=${theme}&device=${device}`)
  console.info('[Backgrounds] loaded', theme, device, resp.items)
  return resp.items.map((item) => ({
    ...item,
    url: resolveUrl(item.url),
    mediaType: item.media_type === 'video' ? 'video' : 'image',
    posterUrl: item.poster_url ? resolveUrl(item.poster_url) : undefined,
    mimeType: item.mime_type,
    fileSize: item.file_size,
  }))
}
