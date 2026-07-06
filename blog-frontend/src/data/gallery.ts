import type { GalleryProject } from '@/types'

// 自动发现项目文档,与博客文章目录隔离,避免进入归档和首页统计。
const rawProjectFiles = import.meta.glob<string>('../assets/projects/*.md', {
  query: '?raw',
  import: 'default',
  eager: true,
})

const projectMeta: Omit<GalleryProject, 'content'>[] = [
  {
    slug: 'my-blog',
    title: 'My Blog',
    description: '围绕内容、液态玻璃视觉和个人表达构建的 Vue 博客前端。',
    tags: ['Vue', 'Vite', 'TypeScript', 'Markdown', 'Liquid Glass'],
    status: '重构中',
    year: '2026',
  },
  {
    slug: 'deep-sea-gallery',
    title: '深海玻璃标本柜',
    description: '一个用于展示项目与技能的深海感作品展厅。',
    tags: ['Vue Router', 'LiquidGlass', 'Design System', 'Responsive'],
    status: '构建中',
    year: '2026',
  },
  {
    slug: 'project-docs',
    title: '项目文档系统',
    description: '独立于博客文章的项目 Markdown 详情链路,为后端接入预留边界。',
    tags: ['Markdown', 'marked', 'Data Layer', 'API Ready'],
    status: '规划中',
    year: '2026',
  },
  {
    slug: 'backend-roadmap',
    title: '后端接入路线',
    description: '为项目、资源下载和动态内容准备 FastAPI 接口边界。',
    tags: ['FastAPI', 'API', 'Resource', 'Deployment'],
    status: '待接入',
    year: '2026',
  },
]

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
