import { describe, expect, it } from 'vitest'
import { buildTimeline, countByType } from '../src/utils'

describe('countByType', () => {
  it('统计各类型冲突数量', () => {
    const results = [
      { type: 'track_occupation' },
      { type: 'over_limit' },
      { type: 'track_occupation' },
    ]
    expect(countByType(results)).toEqual({ track_occupation: 2, over_limit: 1 })
  })

  it('空输入返回空对象', () => {
    expect(countByType()).toEqual({})
  })
})

describe('buildTimeline', () => {
  const trains = [
    { id: 1, arrival_time: '2026-09-19T06:00:00', departure_time: '2026-09-19T09:00:00' },
    { id: 2, arrival_time: '2026-09-19T08:00:00', departure_time: null },
  ]

  it('计算时间范围', () => {
    const tl = buildTimeline(trains, null)
    expect(tl.min).toBe(new Date('2026-09-19T06:00:00').getTime())
    expect(tl.span).toBeGreaterThan(0)
  })

  it('标记涉占用/顺序冲突的列车', () => {
    const analysis = {
      results: [
        { type: 'track_occupation', train_ids: [1, 2] },
        { type: 'over_limit', train_ids: [3] },
      ],
    }
    const tl = buildTimeline(trains, analysis)
    expect(tl.conflictTrains.has(1)).toBe(true)
    expect(tl.conflictTrains.has(2)).toBe(true)
    expect(tl.conflictTrains.has(3)).toBe(false) // 超限不在甘特图标红
  })

  it('无列车时返回 null', () => {
    expect(buildTimeline([], null)).toBeNull()
  })
})
