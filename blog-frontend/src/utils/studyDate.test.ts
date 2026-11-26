// @vitest-environment node
import { execFileSync } from 'node:child_process'
import { readFileSync } from 'node:fs'
import { ModuleKind, ScriptTarget, transpileModule } from 'typescript'
import { describe, expect, it } from 'vitest'
import { getLogicalDate } from './studyDate'

// 每个时区独立运行实际工具代码，避免 Vitest 工作线程改变 TZ 后 Date 缓存未更新。
const executable = transpileModule(readFileSync(new URL('./studyDate.ts', import.meta.url), 'utf8'), {
  compilerOptions: { module: ModuleKind.ESNext, target: ScriptTarget.ESNext },
}).outputText

const boundaries = [
  {
    timezone: 'Asia/Shanghai',
    instants: [
      '2026-10-25T19:59:59.999Z',
      '2026-10-25T20:00:00.000Z',
      '2026-10-25T20:00:00.001Z',
      '2026-12-31T20:00:00.000Z',
      '2024-02-29T19:00:00.000Z',
    ],
    dates: ['2026-10-25', '2026-10-26', '2026-10-26', '2027-01-01', '2024-02-29'],
  },
  {
    timezone: 'America/New_York',
    instants: [
      '2026-01-01T08:59:59.999Z',
      '2026-01-01T09:00:00.000Z',
      '2026-10-26T03:00:00.000Z',
      '2026-03-08T07:59:59.999Z',
      '2026-03-08T08:00:00.000Z',
      '2026-11-01T08:59:59.999Z',
      '2026-11-01T09:00:00.000Z',
    ],
    dates: ['2025-12-31', '2026-01-01', '2026-10-25', '2026-03-07', '2026-03-08', '2026-10-31', '2026-11-01'],
  },
]

describe('自习室本地 04:00 逻辑日期', () => {
  it.each(boundaries)('$timezone 的日界线、跨年和夏令时', ({ timezone, instants, dates }) => {
    const program = `${executable}\nconsole.log(JSON.stringify(${JSON.stringify(instants)}.map(value => getLogicalDate(new Date(value)))))`
    const result = execFileSync(process.execPath, ['--input-type=module', '--eval', program], {
      env: { ...process.env, TZ: timezone }, encoding: 'utf8',
    })
    expect(JSON.parse(result)).toEqual(dates)
  })

  it('不会修改调用者传入的时间', () => {
    const now = new Date(2026, 9, 26, 3, 59, 59)
    const timestamp = now.getTime()
    expect(getLogicalDate(now)).toBe('2026-10-25')
    expect(now.getTime()).toBe(timestamp)
  })
})
