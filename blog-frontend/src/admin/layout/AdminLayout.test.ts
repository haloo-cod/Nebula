import { describe, it, expect, vi, beforeEach } from 'vitest'
import { mount, flushPromises } from '@vue/test-utils'
import { createMemoryHistory, createRouter } from 'vue-router'
import { createPinia } from 'pinia'
import AdminLayout from './AdminLayout.vue'
import DashboardView from '@/admin/views/dashboard/DashboardView.vue'

vi.mock('@/api/client', () => ({
  api: {
    get: vi.fn((path: string) => {
      if (path.includes('overview')) {
        return Promise.resolve({
          today_pv: 10,
          today_uv: 5,
          yesterday_pv: 8,
          yesterday_uv: 4,
          total_pv: 100,
          total_uv: 50,
          page_views: 90,
          book_downloads: 5,
          zip_downloads: 5,
        })
      }
      if (path.includes('trend')) {
        return Promise.resolve([
          { date: '2026-11-25', pv: 8, uv: 4 },
          { date: '2026-11-26', pv: 10, uv: 5 },
        ])
      }
      if (path.includes('pages')) return Promise.resolve([])
      if (path.includes('visitors')) return Promise.resolve({ items: [], total: 0 })
      return Promise.resolve({})
    }),
  },
  getToken: () => 'fake-token',
  setToken: vi.fn(),
  clearToken: vi.fn(),
  subscribeToken: () => () => {},
  resolveUrl: (u: string) => u,
}))

describe('AdminLayout + DashboardView', () => {
  beforeEach(() => {
    Object.defineProperty(window, 'matchMedia', {
      writable: true,
      value: vi.fn().mockImplementation(() => ({
        matches: false,
        addListener: vi.fn(),
        removeListener: vi.fn(),
        addEventListener: vi.fn(),
        removeEventListener: vi.fn(),
      })),
    })
  })

  it('mounts cleanly and renders sidebar, topbar, and dashboard', async () => {
    const router = createRouter({
      history: createMemoryHistory(),
      routes: [
        {
          path: '/admin',
          component: AdminLayout,
          children: [{ path: 'dashboard', component: DashboardView }],
        },
      ],
    })
    await router.push('/admin/dashboard')
    await router.isReady()

    const errors: unknown[] = []
    const wrapper = mount(AdminLayout, {
      global: {
        plugins: [createPinia(), router],
        config: {
          errorHandler(err) {
            errors.push(err)
          },
        },
      },
    })
    await flushPromises()

    expect(errors).toEqual([])
    expect(wrapper.find('#admin-app').exists()).toBe(true)
    expect(wrapper.text()).toContain('Starlit')
    expect(wrapper.text()).toContain('内容工作台')
    expect(document.documentElement.classList.contains('admin-theme')).toBe(true)
  })
})
