import type { GalleryProject } from '@/types'

// 自动发现项目文档,与博客文章目录隔离,避免进入归档和首页统计。
const rawProjectFiles = import.meta.glob<string>('../assets/projects/*.md', {
  query: '?raw',
  import: 'default',
  eager: true,
})
//下面这个为静态数据
const projectMeta: Omit<GalleryProject, 'content'>[] = []

/** 由文件路径生成项目文档 slug */
function slugifyProjectPath(path: string): string {
  return path.split('/').pop()!.replace(/\.md$/, '').replace(/\s+/g, '-').toLowerCase()
}

const projectContentBySlug = new Map(
  Object.entries(rawProjectFiles).map(([path, raw]) => [slugifyProjectPath(path), raw]),
)

const galleryProjects: GalleryProject[] = projectMeta.map((meta) => ({
  ...meta,
  content: projectContentBySlug.get(meta.slug) || `# ${meta.title}\n\n项目文档整理中。`,
}))

/** 获取展览页项目列表 */
export function getGalleryProjects(): GalleryProject[] {
  return galleryProjects
}

/** 按 slug 查找展览页项目,找不到返回 null */
export function getGalleryProject(slug: string): GalleryProject | null {
  return galleryProjects.find((project) => project.slug === slug) || null
}

let markedPromise: Promise<typeof import('marked').marked> | null = null
const htmlCache = new Map<string, string>()

/** 渲染指定项目文档为 HTML,项目不存在时返回 null */
export async function renderGalleryProject(slug: string): Promise<string | null> {
  const project = getGalleryProject(slug)
  if (!project) return null
  if (htmlCache.has(slug)) return htmlCache.get(slug)!
  if (!markedPromise) {
    markedPromise = import('marked').then((m) => m.marked)
  }
  const marked = await markedPromise
  const html = await marked.parse(project.content)
  htmlCache.set(slug, html)
  return html
}
