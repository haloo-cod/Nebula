import { afterEach, beforeEach, describe, expect, it, vi } from 'vitest'
import { defineComponent } from 'vue'
import { flushPromises, mount } from '@vue/test-utils'
import StudyRoom from './study-room.vue'
import HistorySummary from '@/components/study/HistorySummary.vue'
import { getLogicalDate } from '@/utils/studyDate'
import type { StudyTodo, StudyHistoryRecord } from '@/types'

vi.mock('@/stores/ui', () => ({
  useUIStore: () => ({ liquidGlassEnabled: false, theme: 'dark' }),
}))

const TimerContent = defineComponent({
  name: 'StudyRoomContent',
  props: ['mode', 'activeTodo', 'formattedTime', 'isRunning', 'isFlashing'],
  emits: ['toggle', 'reset'],
  template: `<div class="timer" :data-running="isRunning" :data-flashing="isFlashing">
    <span class="timer-mode">{{ mode }}</span><output>{{ formattedTime }}</output>
    <button class="toggle-timer" @click="$emit('toggle')">开始/暂停</button>
    <button class="reset-timer" @click="$emit('reset')">重置</button>
  </div>`,
})
const TodoContent = defineComponent({
  props: ['todos', 'activeId'], emits: ['delete', 'select', 'toggle'],
  template: `<div><button v-for="todo in todos" :key="todo.id" class="delete-todo"
    :data-id="todo.id" @click="$emit('delete', todo.id)">{{ todo.title }}</button></div>`,
})
const SummaryContent = defineComponent({
  props: ['today', 'totalPomodoros', 'totalMinutes'],
  template: '<output class="today-count">{{ today?.completedPomodoros ?? 0 }}</output>',
})
const stubs = {
  LiquidGlass: true,
  PanelFallbackGlass: { template: '<section><slot /></section>' },
  StudyDrawer: { template: '<aside><slot /></aside>' },
  StudyRoomContent: TimerContent,
  TodoPanel: TodoContent,
  SchedulePanel: true,
  SvgIcon: true,
  HistorySummaryContent: SummaryContent,
}

function todo(id: string, remainingSeconds = 0): StudyTodo {
  return {
    id, title: `todo ${id}`, durationMinutes: 1, breakMinutes: 1, remainingSeconds,
    completedPomodoros: 0, todayCompleted: 0, isRunning: false, isCompleted: false,
    createdAt: '2026-10-26T04:00:00Z',
  }
}

function open(todos = [todo('first'), todo('second', 60)]) {
  localStorage.setItem('starlit-study-last-date', getLogicalDate())
  localStorage.setItem('starlit-study-todos', JSON.stringify(todos))
  return mount(StudyRoom, { global: { stubs } })
}

beforeEach(() => {
  vi.useFakeTimers()
  vi.setSystemTime(new Date(2026, 9, 26, 12))
  localStorage.clear()
})
afterEach(() => {
  vi.clearAllTimers()
  vi.restoreAllMocks()
  vi.useRealTimers()
})

describe('自习室计时器生命周期', () => {
  it('卸载清除专注结束后的自动休息回调，不再记录历史', async () => {
    const wrapper = open()
    await wrapper.get('.toggle-timer').trigger('click')
    await vi.advanceTimersByTimeAsync(1000)
    expect(wrapper.get('.timer-mode').text()).toBe('break')
    expect(wrapper.get('.today-count').text()).toBe('1')
    const activeTodo: StudyTodo = wrapper.findComponent(TimerContent).props('activeTodo')
    const history = wrapper.findComponent(HistorySummary).props('history')
    const historySnapshot = JSON.stringify(history)
    await flushPromises()
    const historyBeforeUnmount = localStorage.getItem('starlit-study-history')
    wrapper.unmount()
    await vi.advanceTimersByTimeAsync(120000)
    expect(activeTodo.isRunning).toBe(false)
    expect(activeTodo.remainingSeconds).toBe(60)
    expect(JSON.stringify(history)).toBe(historySnapshot)
    expect(localStorage.getItem('starlit-study-history')).toBe(historyBeforeUnmount)
  })

  it('卸载清除休息结束后的闪烁回调', async () => {
    const first = todo('first')
    first.breakMinutes = 0
    const timeout = vi.spyOn(window, 'setTimeout')
    const cancelTimeout = vi.spyOn(window, 'clearTimeout')
    const wrapper = open([first])
    await wrapper.get('.toggle-timer').trigger('click')
    await vi.advanceTimersByTimeAsync(3500)
    expect(wrapper.get('.timer-mode').text()).toBe('focus')
    expect(wrapper.get('.timer').attributes('data-flashing')).toBe('true')
    const flashCall = timeout.mock.calls.findLastIndex(([, delay]) => delay === 1500)
    const flashHandle = timeout.mock.results[flashCall]?.value
    expect(flashHandle).toBeDefined()
    const activeTodo: StudyTodo = wrapper.findComponent(TimerContent).props('activeTodo')
    const history = wrapper.findComponent(HistorySummary).props('history')
    const historySnapshot = JSON.stringify(history)
    wrapper.unmount()
    expect(cancelTimeout).toHaveBeenCalledWith(flashHandle)
    await vi.advanceTimersByTimeAsync(120000)
    expect(activeTodo.isRunning).toBe(false)
    expect(activeTodo.remainingSeconds).toBe(60)
    expect(JSON.stringify(history)).toBe(historySnapshot)
  })

  it('删除正在运行的任务会停止 interval，不替下一任务倒计时', async () => {
    const wrapper = open([todo('first', 60), todo('second', 60)])
    await wrapper.get('.toggle-timer').trigger('click')
    await wrapper.get('.delete-todo[data-id="first"]').trigger('click')
    expect(wrapper.get('.timer').attributes('data-running')).toBe('false')
    const stateAfterDelete = wrapper.get('.timer').html()
    await vi.advanceTimersByTimeAsync(65000)
    expect(wrapper.get('.timer output').text()).toBe('01:00')
    expect(wrapper.get('.today-count').text()).toBe('0')
    expect(wrapper.get('.timer').html()).toBe(stateAfterDelete)
    wrapper.unmount()
  })

  it('删除等待自动休息的任务会取消延迟，不启动下一任务', async () => {
    const wrapper = open()
    await wrapper.get('.toggle-timer').trigger('click')
    await vi.advanceTimersByTimeAsync(1000)
    expect(wrapper.get('.timer-mode').text()).toBe('break')
    await wrapper.get('.delete-todo[data-id="first"]').trigger('click')
    const stateAfterDelete = wrapper.get('.timer').html()
    await vi.advanceTimersByTimeAsync(65000)
    expect(wrapper.get('.timer-mode').text()).toBe('focus')
    expect(wrapper.get('.timer').attributes('data-running')).toBe('false')
    expect(wrapper.get('.timer output').text()).toBe('01:00')
    expect(wrapper.get('.today-count').text()).toBe('1')
    expect(wrapper.get('.timer').html()).toBe(stateAfterDelete)
    wrapper.unmount()
  })

  it('已有历史日期原样保留', async () => {
    const historical: StudyHistoryRecord[] = [
      { date: '2024-01-01', completedPomodoros: 2, totalFocusMinutes: 50 },
      { date: '2024-01-02', completedPomodoros: 3, totalFocusMinutes: 75 },
    ]
    localStorage.setItem('starlit-study-history', JSON.stringify(historical))
    const wrapper = open()
    await flushPromises()
    expect(JSON.parse(localStorage.getItem('starlit-study-history') || '[]')).toEqual(historical)
    wrapper.unmount()
  })
})

describe('历史摘要与存储逻辑日一致', () => {
  it.each([3, 4])('本地 %i 时显示对应逻辑日的记录', (hour) => {
    vi.setSystemTime(new Date(2026, 9, 26, hour, 0, 0))
    const wrapper = mount(HistorySummary, {
      props: {
        history: [
          { date: '2026-10-25', completedPomodoros: 2, totalFocusMinutes: 50 },
          { date: '2026-10-26', completedPomodoros: 3, totalFocusMinutes: 75 },
        ],
      },
      global: { stubs },
    })
    expect(wrapper.get('.today-count').text()).toBe(hour < 4 ? '2' : '3')
    wrapper.unmount()
  })
})
