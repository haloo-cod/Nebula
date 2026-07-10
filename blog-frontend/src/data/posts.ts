import type { Post, PostStat, Frontmatter } from '@/types'
import { postCoverAssignments } from '@/data/post-covers'

// 自动发现 src/assets/md 下所有 .md 文件,无需手动维护导入列表
// eager + ?raw:构建时把每个文件的原始字符串内容直接内联进来
const rawFiles = import.meta.glob<string>('../assets/md/*.md', {
  query: '?raw',
  import: 'default',
  eager: true,
})

/**
 * 解析 Markdown frontmatter
 * @param raw Markdown 原文(可能带 BOM)
 * @returns 解析出的元数据与去除 frontmatter 后的正文
 */
function parseFrontmatter(raw: string): { data: Frontmatter; content: string } {
  const match = raw.replace(/^\uFEFF/, '').match(/^---\r?\n([\s\S]*?)\r?\n---\r?\n?([\s\S]*)$/)
  if (!match) return { data: {}, content: raw }
  const data: Frontmatter = {}
  for (const line of match[1].split('\n')) {
    const sep = line.indexOf(':')
    if (sep === -1) continue
    const key = line.slice(0, sep).trim()
    let value: string | number | boolean | string[] = line.slice(sep + 1).trim()
    if (
      (value.startsWith('"') && value.endsWith('"')) ||
      (value.startsWith("'") && value.endsWith("'"))
    ) {
      value = value.slice(1, -1)
    } else if (value === 'true') {
      value = true
    } else if (value === 'false') {
      value = false
    } else if (value === '[]') {
      value = []
    } else if (value !== '' && !isNaN(Number(value))) {
      value = Number(value)
    }
    data[key] = value
  }
  return { data, content: match[2] }
}

/** 由文件路径生成 URL slug(取文件名,去扩展名,空格转连字符,转小写) */
function slugify(path: string): string {
  return path.split('/').pop()!.replace(/\.md$/, '').replace(/\s+/g, '-').toLowerCase()
}

/** 将相对图片路径转为 Vite 可解析的绝对路径（处理 ../img/xxx → /src/assets/img/xxx） */
function resolveImagePath(path: string): string {
  if (!path || path.startsWith('http://') || path.startsWith('https://')) return path
  return path.replace(/^(\.\.\/)?(img\/.*)$/, '/src/assets/$2')
}

const posts: Post[] = Object.entries(rawFiles)
  .map(([path, raw]): Post => {
    const { data, content } = parseFrontmatter(raw)
    return {
      slug: slugify(path),
      title: data.title || slugify(path),
      description: data.description || '',
      date: data.published || '',
      cover: resolveImagePath(postCoverAssignments[slugify(path)] || (data.image as string) || ''),
      tags: data.tags || [],
      category: data.category || '',
      draft: data.draft || false,
      pinned: data.pinned || false,
      content,
    }
  })
  .sort((a, b) => {
    if (a.pinned !== b.pinned) return a.pinned ? -1 : 1
    return new Date(b.date).getTime() - new Date(a.date).getTime()
  })

// 列表只需要元数据,正文渲染按需进行,marked 不会进入首页包
export function getPosts(): Post[] {
  return posts
}

// 按年份统计发表博客数量,返回按时间升序排列的 [{ label, count }]
// 用于右侧折线图:x 轴为时间(年),y 轴为发表数量
export function getPostStats(): PostStat[] {
  const counts = new Map<string, number>()
  for (const p of posts) {
    if (p.draft || !p.date) continue
    const year = String(p.date).slice(0, 4)
    if (!/^\d{4}$/.test(year)) continue
    counts.set(year, (counts.get(year) || 0) + 1)
  }
  return [...counts.entries()]
    .map(([label, count]): PostStat => ({ label, count }))
    .sort((a, b) => Number(a.label) - Number(b.label))
}

/** 按 slug 查找单篇文章,找不到返回 null */
export function getPost(slug: string): Post | null {
  return posts.find((p) => p.slug === slug) || null
}

// 懒加载 marked,仅在真正渲染文章正文时才下载并解析
let markedPromise: Promise<typeof import('marked').marked> | null = null
const htmlCache = new Map<string, string>()

/**
 * 渲染指定文章正文为 HTML(带缓存,marked 按需懒加载)
 * @param slug 文章标识
 * @returns 渲染后的 HTML 字符串;文章不存在时返回 null
 */
export async function renderPost(slug: string): Promise<string | null> {
  const post = getPost(slug)
  if (!post) return null
  if (htmlCache.has(slug)) return htmlCache.get(slug)!
  if (!markedPromise) {
    markedPromise = import('marked').then((m) => m.marked)
  }
  const marked = await markedPromise
  const html = (await marked.parse(post.content))
    // 把 ../img/xxx 这种相对路径转成 Vite 可解析的绝对路径
    .replace(/(<img\s+src=")(\.\.?\/)?(img\/[^"]+)"/g, '$1/src/assets/$3"')
  htmlCache.set(slug, html)
  return html
}
