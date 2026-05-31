import { marked } from 'marked'

import test from '../assets/md/test.md?raw'
import testCopy from '../assets/md/test-copy.md?raw'
import testCopy2 from '../assets/md/test-copy-2.md?raw'

const rawFiles = {
  'test.md': test,
  'test-copy.md': testCopy,
  'test-copy-2.md': testCopy2,
}

function parseFrontmatter(raw) {
  const match = raw.match(/^---\r?\n([\s\S]*?)\r?\n---\r?\n?([\s\S]*)$/)
  if (!match) return { data: {}, content: raw }
  const data = {}
  const lines = match[1].split('\n')
  for (const line of lines) {
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
    } else if (!isNaN(Number(value)) && value !== '') {
      value = Number(value)
    }
    data[key] = value
  }
  return { data, content: match[2] }
}

function slugify(filename) {
  return filename.replace(/\.md$/, '').replace(/\s+/g, '-').toLowerCase()
}

const posts = Object.entries(rawFiles).map(([filename, raw]) => {
  const { data, content } = parseFrontmatter(raw)
  return {
    slug: slugify(filename),
    title: data.title || filename,
    description: data.description || '',
    date: data.published || '',
    tags: data.tags || [],
    category: data.category || '',
    draft: data.draft || false,
    pinned: data.pinned || false,
    content,
    _html: null,
    get html() {
      if (this._html === null) {
        this._html = marked.parse(this.content)
      }
      return this._html
    },
  }
})

posts.sort((a, b) => {
  if (a.pinned && !b.pinned) return -1
  if (!a.pinned && b.pinned) return 1
  return new Date(b.date) - new Date(a.date)
})

export function getPosts() {
  return posts
}

export function getPost(slug) {
  return posts.find((p) => p.slug === slug) || null
}
