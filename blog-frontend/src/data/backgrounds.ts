/** 背景图条目 */
export interface BackgroundItem {
  src: string
  mediaType?: 'image' | 'video'
  posterUrl?: string
  mimeType?: string
  fileSize?: number
}

export function isVideoBackground(item: {
  src?: string
  url?: string
  mediaType?: 'image' | 'video'
  media_type?: 'image' | 'video'
  mimeType?: string
  mime_type?: string
}): boolean {
  const src = item.src ?? item.url ?? ''
  const type = item.mediaType ?? item.media_type
  const mime = item.mimeType ?? item.mime_type
  return (
    type === 'video' ||
    mime?.startsWith('video/') === true ||
    /\/api\/v1\/files\/\d+\/media(?:\?|$)/i.test(src) ||
    /\.(mp4|webm|mov)(?:\?|$)/i.test(src)
  )
}

const darkDesktopFiles = import.meta.glob<string>(
  '../assets/backgrounds/desktop/dark/*.{png,PNG,jpg,JPG,jpeg,webp,WEBP}',
  { query: '?url', import: 'default', eager: true },
)
const lightDesktopFiles = import.meta.glob<string>(
  '../assets/backgrounds/desktop/light/*.{png,PNG,jpg,JPG,jpeg,webp,WEBP}',
  { query: '?url', import: 'default', eager: true },
)
const darkMobileFiles = import.meta.glob<string>(
  '../assets/backgrounds/mobile/dark/*.{png,PNG,jpg,JPG,jpeg,webp,WEBP}',
  { query: '?url', import: 'default', eager: true },
)
const lightMobileFiles = import.meta.glob<string>(
  '../assets/backgrounds/mobile/light/*.{png,PNG,jpg,JPG,jpeg,webp,WEBP}',
  { query: '?url', import: 'default', eager: true },
)

function toBackgroundItems(files: Record<string, string>): BackgroundItem[] {
  return Object.values(files).map((src) => ({ src }))
}

/** 静态 fallback: dark 主题桌面端背景图组 */
export const darkBackgrounds: BackgroundItem[] = toBackgroundItems(darkDesktopFiles)

/** 静态 fallback: light 主题桌面端背景图组 */
export const lightBackgrounds: BackgroundItem[] = toBackgroundItems(lightDesktopFiles)

/** 静态 fallback: dark 主题移动端背景图组 */
export const mobileDarkBackgrounds: BackgroundItem[] = toBackgroundItems(darkMobileFiles)

/** 静态 fallback: light 主题移动端背景图组 */
export const mobileLightBackgrounds: BackgroundItem[] = toBackgroundItems(lightMobileFiles)
