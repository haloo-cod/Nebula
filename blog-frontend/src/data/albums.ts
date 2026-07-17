import type { Album, AlbumPhoto } from '@/types'

// 本地图片素材:当前照片墙先用 assets/img2 下的静态图验证效果,
// 后续接入后端相册接口时,只需把 getAlbums() 的返回值换成接口数据。
const rawImageFiles = import.meta.glob<string>('../assets/img2/*.{png,PNG,jpg,JPG,jpeg,jfif}', {
  query: '?url',
  import: 'default',
  eager: true,
})

// 文件名(不含扩展名,小写) → URL 的映射,方便手动分组时按名取图
const urlByName = Object.fromEntries(
  Object.entries(rawImageFiles).map(([path, url]) => [
    path
      .split('/')
      .pop()!
      .replace(/\.[^.]+$/, '')
      .toLowerCase(),
    url,
  ]),
)

/** 按文件名取图并附带说明文字,文件不存在时给出警告并回退空串 */
function photo(name: string, caption?: string): AlbumPhoto {
  const url = urlByName[name.toLowerCase()] || ''
  if (!url) console.warn(`[albums] 未找到图片素材: ${name}`)
  return { url, caption }
}

// 手动相册分组:演示阶段按文件名分配,封面取每组第一张
const albums: Album[] = [
  {
    id: 'light-fragments',
    title: '光影碎片',
    description: '随手收集的光与影,一些不成系列的瞬间',
    cover: photo('01', '第一束光').url,
    date: '2026.07',
    orientation: 'portrait',
    photos: [photo('01', '第一束光'), photo('02', '午后窗边'), photo('03', '街角一瞥')],
  },
  {
    id: 'journey-pickings',
    title: '旅途拾遗',
    description: '路上捡到的风景',
    cover: photo('04', '出发').url,
    date: '2026.05',
    orientation: 'portrait',
    photos: [photo('04', '出发'), photo('05', '远山')],
  },
  {
    id: 'daily-slices',
    title: '日常切片',
    description: '平凡日子的横截面',
    cover: photo('06', '清晨').url,
    date: '2026.03',
    orientation: 'portrait',
    photos: [photo('06', '清晨'), photo('07', '夜幕')],
  },
]

/** 获取全部相册列表 */
export function getAlbums(): Album[] {
  return albums
}
