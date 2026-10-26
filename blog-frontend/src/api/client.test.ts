import { afterAll, afterEach, beforeEach, describe, expect, it, vi } from 'vitest'
import type { Mock } from 'vitest'
import { createPinia } from 'pinia'
import { Blob as NodeBlob } from 'node:buffer'
import * as client from './client'
import * as authApi from './auth'
import { uploadFile } from './files'
import { uploadImage } from './images'
import { useAuthStore } from '@/stores/auth'
import { downloadWithProgress } from '@/utils/download'

vi.hoisted(() => {
  vi.stubEnv('VITE_API_BASE_URL', '')
  vi.stubEnv('VITE_USE_API', 'true')
})

/** 记录浏览器 XHR 的请求体、认证配置和进度事件，不模拟刷新逻辑。 */
class TestXhr extends EventTarget {
  static requests: TestXhr[] = []
  upload = new EventTarget()
  headers = new Headers()
  method = ''
  url = ''
  withCredentials = false
  responseType: XMLHttpRequestResponseType = ''
  status = 0
  response: unknown = null
  responseText = ''
  body: Document | XMLHttpRequestBodyInit | null = null

  open(method: string, url: string): void {
    this.method = method
    this.url = url
  }

  setRequestHeader(key: string, value: string): void {
    this.headers.set(key, value)
  }

  send(body: Document | XMLHttpRequestBodyInit | null): void {
    this.body = body
    TestXhr.requests.push(this)
  }

  respond(status: number, body: string | Blob = ''): void {
    this.status = status
    this.response = body
    this.responseText = typeof body === 'string' ? body : ''
    this.dispatchEvent(new Event('load'))
  }

  progress(upload: boolean): void {
    const event = new ProgressEvent('progress', { lengthComputable: true, loaded: 1, total: 2 })
    const target = upload ? this.upload : this
    target.dispatchEvent(event)
  }
}

const user = {
  id: 1,
  username: 'reader',
  is_admin: true,
  email: 'reader@example.com',
  display_name: 'Reader',
  avatar_url: '',
  email_verified: true,
}

function json(body: unknown, status = 200): Response {
  return new Response(JSON.stringify(body), {
    status,
    headers: { 'Content-Type': 'application/json' },
  })
}

const store = useAuthStore(createPinia())
let fetchMock: Mock<typeof fetch>

beforeEach(() => {
  localStorage.clear()
  TestXhr.requests = []
  fetchMock = vi.fn<typeof fetch>()
  vi.stubGlobal('fetch', fetchMock)
  vi.stubGlobal('XMLHttpRequest', TestXhr)
  // Node 的真实 Blob 提供 text()，jsdom 的文件实现用于 FormData/File 即可。
  vi.stubGlobal('Blob', NodeBlob)
  vi.stubGlobal('URL', class extends URL {
    static createObjectURL = vi.fn(() => 'blob:test')
    static revokeObjectURL = vi.fn()
  })
  store.initialized = false
  client.setToken('expired')
  store.user = { ...user }
})

afterEach(() => {
  vi.unstubAllGlobals()
  vi.restoreAllMocks()
})

afterAll(() => {
  store.$dispose()
  vi.unstubAllEnvs()
})

describe('共享认证恢复', () => {
  it('fetch、文件上传和显式会话恢复共用一次刷新，并重放原始上传体和进度', async () => {
    const refresh = Promise.withResolvers<Response>()
    const started = Promise.withResolvers<void>()
    fetchMock.mockImplementation(async (url, init) => {
      if (String(url).endsWith('/auth/refresh')) {
        started.resolve()
        return refresh.promise
      }
      return new Headers(init?.headers).get('Authorization') === 'Bearer rotated'
        ? json({ ok: true })
        : json({ detail: 'expired' }, 401)
    })
    const progress = vi.fn()
    const request = client.api.get('/api/v1/private', true)
    const upload = uploadFile(new File(['file'], 'book.epub'), progress)
    const first = TestXhr.requests[0]
    first.progress(true)
    first.respond(401, JSON.stringify({ detail: 'expired' }))
    await started.promise
    const restore = authApi.refreshSession()
    expect(fetchMock.mock.calls.filter(([url]) => String(url).endsWith('/auth/refresh'))).toHaveLength(1)
    refresh.resolve(json({ access_token: 'rotated', token_type: 'bearer' }))
    await expect(request).resolves.toEqual({ ok: true })
    await expect(restore).resolves.toMatchObject({ access_token: 'rotated' })
    await vi.waitFor(() => expect(TestXhr.requests).toHaveLength(2))
    const retry = TestXhr.requests[1]
    expect(retry.body).toBe(first.body)
    expect(retry.withCredentials).toBe(true)
    expect(retry.headers.get('Authorization')).toBe('Bearer rotated')
    retry.progress(true)
    retry.respond(200, JSON.stringify({ id: 4, original_name: 'book.epub' }))
    await expect(upload).resolves.toMatchObject({ id: 4 })
    expect(progress).toHaveBeenCalledWith(50)
    expect(client.getToken()).toBe('rotated')
    expect(store.token).toBe('rotated')
    expect(store.user).toEqual(user)
    expect(store.isLoggedIn).toBe(true)
  })

  it('刷新被拒绝后同步清空 token 和用户，迟到的 401 不会再次刷新', async () => {
    const late = Promise.withResolvers<Response>()
    fetchMock.mockImplementation(async (url) => {
      if (String(url).endsWith('/auth/refresh')) return json({ detail: 'session expired' }, 401)
      if (String(url).endsWith('/late')) return late.promise
      return json({ detail: 'expired' }, 401)
    })
    const lateRequest = client.api.get('/api/v1/late', true)
    await expect(client.api.get('/api/v1/private', true)).rejects.toMatchObject({
      status: 401,
      message: 'session expired',
    })
    expect(client.getToken()).toBeNull()
    expect(store.token).toBeNull()
    expect(store.user).toBeNull()
    expect(store.isLoggedIn).toBe(false)
    late.resolve(json({ detail: 'late unauthorized' }, 401))
    await expect(lateRequest).rejects.toMatchObject({ status: 401 })
    expect(fetchMock.mock.calls.filter(([url]) => String(url).endsWith('/auth/refresh'))).toHaveLength(1)
  })

  it.each(['network', 'server'])('刷新发生 %s 异常时保留可恢复的登录状态', async (failure) => {
    fetchMock.mockImplementation(async (url) => {
      if (!String(url).endsWith('/auth/refresh')) return json({ detail: 'expired' }, 401)
      if (failure === 'network') throw new TypeError('offline')
      return json({ detail: 'temporarily unavailable' }, 503)
    })
    await expect(client.api.get('/api/v1/private', true)).rejects.toThrow(
      failure === 'network' ? 'offline' : 'temporarily unavailable',
    )
    expect(client.getToken()).toBe('expired')
    expect(store.token).toBe('expired')
    expect(store.user).toEqual(user)
    expect(store.isLoggedIn).toBe(true)
    expect(fetchMock).toHaveBeenCalledTimes(2)
  })

  it('迟到的旧 token 401 直接重用已轮换令牌，不再轮换 Cookie', async () => {
    const late = Promise.withResolvers<Response>()
    fetchMock.mockImplementation(async (url, init) => {
      if (String(url).endsWith('/auth/refresh')) {
        return json({ access_token: 'rotated', token_type: 'bearer' })
      }
      if (new Headers(init?.headers).get('Authorization') === 'Bearer rotated') {
        return json({ ok: true })
      }
      if (String(url).endsWith('/late')) return late.promise
      return json({ detail: 'expired' }, 401)
    })
    const lateRequest = client.api.get('/api/v1/late', true)
    await expect(client.api.get('/api/v1/private', true)).resolves.toEqual({ ok: true })
    late.resolve(json({ detail: 'expired' }, 401))
    await expect(lateRequest).resolves.toEqual({ ok: true })
    expect(fetchMock.mock.calls.filter(([url]) => String(url).endsWith('/auth/refresh'))).toHaveLength(1)
  })

  it('新登录之后才返回的旧 401 不会刷新或清空新会话', async () => {
    const pending = Promise.withResolvers<Response>()
    fetchMock.mockReturnValue(pending.promise)
    const request = client.api.get('/api/v1/private', true)
    client.setToken('new-login')
    store.user = { ...user, id: 2 }
    pending.resolve(json({ detail: 'old unauthorized' }, 401))
    await expect(request).rejects.toMatchObject({ status: 401, detail: 'old unauthorized' })
    expect(fetchMock).toHaveBeenCalledTimes(1)
    expect(store.token).toBe('new-login')
    expect(store.user?.id).toBe(2)
  })

  it.each([200, 401])('新登录之后旧刷新返回 %s 也不能覆盖或清理新会话', async (status) => {
    const pending = Promise.withResolvers<Response>()
    fetchMock.mockReturnValue(pending.promise)
    const refresh = authApi.refreshSession()
    client.setToken('new-login')
    store.user = { ...user, id: 2 }
    pending.resolve(json(
      status === 200 ? { access_token: 'old-session', token_type: 'bearer' } : { detail: 'expired' },
      status,
    ))
    await expect(refresh).rejects.toMatchObject({ status: 401 })
    expect(client.getToken()).toBe('new-login')
    expect(store.token).toBe('new-login')
    expect(store.user?.id).toBe(2)
  })

  it('刷新后的重试 403 原样抛出，并保留已恢复的令牌和用户', async () => {
    fetchMock
      .mockResolvedValueOnce(json({ detail: 'expired' }, 401))
      .mockResolvedValueOnce(json({ access_token: 'rotated', token_type: 'bearer' }))
      .mockResolvedValueOnce(json({ detail: 'permission denied' }, 403))
    await expect(client.api.get('/api/v1/private', true)).rejects.toMatchObject({
      status: 403,
      detail: 'permission denied',
    })
    expect(fetchMock).toHaveBeenCalledTimes(3)
    expect(store.token).toBe('rotated')
    expect(store.user).toEqual(user)
  })

  it('网络错误和非 401 响应都不会重试；重试自身的网络错误不会清理会话', async () => {
    fetchMock.mockRejectedValueOnce(new TypeError('offline'))
    await expect(client.api.get('/api/v1/private', true)).rejects.toThrow('offline')
    expect(fetchMock).toHaveBeenCalledTimes(1)
    fetchMock.mockResolvedValueOnce(json({ detail: 'busy' }, 503))
    await expect(client.api.get('/api/v1/private', true)).rejects.toMatchObject({ status: 503 })
    expect(fetchMock).toHaveBeenCalledTimes(2)
    fetchMock
      .mockResolvedValueOnce(json({ detail: 'expired' }, 401))
      .mockResolvedValueOnce(json({ access_token: 'rotated', token_type: 'bearer' }))
      .mockRejectedValueOnce(new TypeError('retry offline'))
    await expect(client.api.get('/api/v1/private', true)).rejects.toThrow('retry offline')
    expect(fetchMock).toHaveBeenCalledTimes(5)
    expect(store.token).toBe('rotated')
    expect(store.user).toEqual(user)
  })

  it('图片上传只重放一次同一个 FormData，第二次仍为 401 时直接报告', async () => {
    fetchMock
      .mockResolvedValueOnce(json({ detail: 'expired' }, 401))
      .mockResolvedValueOnce(json({ access_token: 'rotated', token_type: 'bearer' }))
      .mockResolvedValueOnce(json({ detail: 'still unauthorized' }, 401))
    await expect(uploadImage(new File(['image'], 'cover.png'))).rejects.toMatchObject({
      status: 401,
      detail: 'still unauthorized',
    })
    expect(fetchMock).toHaveBeenCalledTimes(3)
    expect(fetchMock.mock.calls[0][1]?.body).toBe(fetchMock.mock.calls[2][1]?.body)
    expect(new Headers(fetchMock.mock.calls[2][1]?.headers).get('Authorization')).toBe('Bearer rotated')
  })
})

describe('响应式用户信息', () => {
  it('初始化或用户查询遇到网络异常时保留现有状态，初始化仍然结束', async () => {
    fetchMock.mockRejectedValue(new TypeError('offline'))
    await expect(store.fetchUser()).rejects.toThrow('offline')
    await store.init()
    expect(store.initialized).toBe(true)
    expect(store.token).toBe('expired')
    expect(store.user).toEqual(user)
    await store.init(true)
    expect(store.token).toBe('expired')
    expect(store.user).toEqual(user)
  })

  it('旧用户查询结果不能覆盖新登录用户', async () => {
    const pending = Promise.withResolvers<Response>()
    fetchMock.mockReturnValue(pending.promise)
    const request = store.fetchUser()
    client.setToken('new-login')
    store.user = { ...user, id: 2 }
    pending.resolve(json(user))
    await request
    expect(store.user?.id).toBe(2)
    expect(store.token).toBe('new-login')
  })
})

describe('下载认证边界与错误', () => {
  it('受保护下载遇到 401 后用新 token 重试，并保留下载进度', async () => {
    fetchMock.mockResolvedValue(json({ access_token: 'rotated', token_type: 'bearer' }))
    const createUrl = vi.mocked(URL.createObjectURL)
    vi.spyOn(HTMLAnchorElement.prototype, 'click').mockImplementation(() => {})
    const progress = vi.fn()
    const request = downloadWithProgress('/api/v1/books/a/download', 'a.epub', {
      headers: { Authorization: 'Bearer expired' },
      onProgress: progress,
    })
    TestXhr.requests[0].respond(401, new Blob([JSON.stringify({ detail: 'expired' })]))
    await vi.waitFor(() => expect(TestXhr.requests).toHaveLength(2))
    const retry = TestXhr.requests[1]
    expect(retry.headers.get('Authorization')).toBe('Bearer rotated')
    retry.progress(false)
    const file = new Blob(['epub'])
    retry.respond(200, file)
    await request
    expect(progress).toHaveBeenCalledWith(50)
    expect(progress).toHaveBeenLastCalledWith(100)
    expect(createUrl).toHaveBeenCalledWith(file)
    expect(fetchMock).toHaveBeenCalledTimes(1)
  })

  it('第三方 URL 即使误传 Authorization 也不发送认证、Cookie 或刷新请求', async () => {
    const request = downloadWithProgress('https://downloads.example.org/file.zip', 'file.zip', {
      headers: { Authorization: 'Bearer secret', Cookie: 'session=secret', Accept: '*/*' },
    })
    const xhr = TestXhr.requests[0]
    expect(xhr.withCredentials).toBe(false)
    expect(xhr.headers.has('Authorization')).toBe(false)
    expect(xhr.headers.has('Cookie')).toBe(false)
    expect(xhr.headers.get('Accept')).toBe('*/*')
    xhr.respond(401, new Blob([JSON.stringify({ detail: 'external denied' })]))
    await expect(request).rejects.toMatchObject({ status: 401, detail: 'external denied' })
    expect(fetchMock).not.toHaveBeenCalled()
    expect(TestXhr.requests).toHaveLength(1)
    expect(store.token).toBe('expired')
  })

  it('未显式提供 headers 的公开下载不携带 token，也不会尝试刷新', async () => {
    const request = downloadWithProgress('/api/v1/files/public/download', 'file.zip')
    const xhr = TestXhr.requests[0]
    expect(xhr.headers.has('Authorization')).toBe(false)
    expect(xhr.withCredentials).toBe(false)
    xhr.respond(401, new Blob([JSON.stringify({ detail: 'login required' })]))
    await expect(request).rejects.toMatchObject({ status: 401, detail: 'login required' })
    expect(fetchMock).not.toHaveBeenCalled()
  })

  it('Blob 错误响应保留后端 JSON detail，非 401 不重试', async () => {
    const request = downloadWithProgress('/api/v1/books/a/download', 'a.epub', { headers: {} })
    TestXhr.requests[0].respond(403, new Blob([JSON.stringify({ detail: 'archive expired' })]))
    await expect(request).rejects.toMatchObject({ status: 403, message: 'archive expired' })
    expect(TestXhr.requests).toHaveLength(1)
    expect(fetchMock).not.toHaveBeenCalled()
  })
})
