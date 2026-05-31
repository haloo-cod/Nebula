// 自动发现 src/assets/md 下所有 .md 文件，无需手动维护导入列表
const rawFiles = import.meta.glob('../assets/md/*.md', {
  query: '?raw',
  import: 'default',
  eager: true,
})

function parseFrontmatter(raw) {
  const match = raw.match(/^---\r?\n([\s\S]*?)\r?\n---\r?\n?([\s\S]*)$/)
  if (!match) return { data: {}, content: raw }
  const data = {}
  for (const line of match[1].split('\n')) {
    const sep = line.indexOf(':')
    if (sep === -1) continue
    const key = line.slice(0, sep).trim()
    let value = line.slice(sep + 1).trim()
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

function slugify(path) {
  return path
    .split('/')
    .pop()
    .replace(/\.md$/, '')
    .replace(/\s+/g, '-')
    .toLowerCase()
}

const posts = Object.entries(rawFiles)
  .map(([path, raw]) => {
    const { data, content } = parseFrontmatter(raw)
    return {
      slug: slugify(path),
      title: data.title || slugify(path),
      description: data.description || '',
      date: data.published || '',
      tags: data.tags || [],
      category: data.category || '',
      draft: data.draft || false,
      pinned: data.pinned || false,
      content,
    }
  })
  .sort((a, b) => {
    if (a.pinned !== b.pinned) return a.pinned ? -1 : 1
    return new Date(b.date) - new Date(a.date)
  })

// 列表只需要元数据，正文渲染按需进行，marked 不会进入首页包
export function getPosts() {
  return posts
}

export function getPost(slug) {
  return posts.find((p) => p.slug === slug) || null
}

// 懒加载 marked，仅在真正渲染文章正文时才下载并解析
let markedPromise = null
const htmlCache = new Map()

export async function renderPost(slug) {
  const post = getPost(slug)
  if (!post) return null
  if (htmlCache.has(slug)) return htmlCache.get(slug)
  if (!markedPromise) {
    markedPromise = import('marked').then((m) => m.marked)
  }
  const marked = await markedPromise
  const html = marked.parse(post.content)
  htmlCache.set(slug, html)
  return html
}
