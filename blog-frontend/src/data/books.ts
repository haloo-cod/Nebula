import type { Book, ExtractedBookMeta } from '@/types'

const rawBookFiles = import.meta.glob<string>('../assets/testepub/*.epub', {
  query: '?url',
  import: 'default',
  eager: true,
})

const extractedMetaCache = new Map<string, Promise<ExtractedBookMeta>>()

/** 由 EPUB 路径生成稳定 slug */
function slugify(path: string): string {
  return path
    .split('/')
    .pop()!
    .replace(/\.epub$/i, '')
    .trim()
}

/** 由 EPUB 路径生成默认书名 */
function titleFromPath(path: string): string {
  return decodeURIComponent(slugify(path))
}

const books: Book[] = Object.entries(rawBookFiles).map(([path, file]) => ({
  slug: slugify(path),
  title: titleFromPath(path),
  author: '',
  description: '',
  cover: '',
  file,
}))

/** 获取全部图书列表 */
export function getBooks(): Book[] {
  return books
}

/** 按 slug 查找单本图书,找不到返回 null */
export function getBook(slug: string): Book | null {
  return books.find((book) => book.slug === slug) || null
}

/**
 * 从 EPUB 文件中按需提取元数据。
 * @param book 图书配置
 * @returns EPUB 内部解析出的标题、作者、简介与封面
 */
export function extractBookMeta(book: Book): Promise<ExtractedBookMeta> {
  const cached = extractedMetaCache.get(book.slug)
  if (cached) return cached

  const task = (async (): Promise<ExtractedBookMeta> => {
    try {
      const { default: ePub } = await import('epubjs')
      const epubBook = ePub(book.file)
      const metadata = await epubBook.loaded.metadata
      const cover = (await epubBook.coverUrl()) || undefined
      epubBook.destroy()
      return {
        title: metadata.title || undefined,
        author: metadata.creator || undefined,
        description: metadata.description || undefined,
        cover,
      }
    } catch (error) {
      console.warn('[books] EPUB 元数据解析失败,使用文件名作为默认信息:', error)
      return {}
    }
  })()

  extractedMetaCache.set(book.slug, task)
  return task
}

/** 合并手动配置与 EPUB 自动解析结果,文件名标题优先保持可读 */
export async function getHydratedBook(slug: string): Promise<Book | null> {
  const book = getBook(slug)
  if (!book) return null
  const extracted = await extractBookMeta(book)
  return {
    ...book,
    title: book.title || extracted.title || book.slug,
    author: book.author || extracted.author || '',
    description: book.description || extracted.description || '',
    cover: book.cover || extracted.cover || '',
  }
}
