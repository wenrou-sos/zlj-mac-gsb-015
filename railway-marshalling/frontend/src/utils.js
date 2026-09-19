/** 纯函数工具，便于单元测试。 */

/** 按冲突类型统计数量。 */
export function countByType(results = []) {
  const stats = {}
  for (const c of results) stats[c.type] = (stats[c.type] || 0) + 1
  return stats
}

/** 计算甘特图时间范围与涉冲突列车集合。 */
export function buildTimeline(trains, analysis) {
  const timed = trains.filter((t) => t.arrival_time)
  if (!timed.length) return null
  const times = timed.flatMap((t) => [
    new Date(t.arrival_time).getTime(),
    t.departure_time ? new Date(t.departure_time).getTime() : new Date(t.arrival_time).getTime() + 6 * 3600e3,
  ])
  const min = Math.min(...times)
  const max = Math.max(...times)
  const conflictTrains = new Set(
    (analysis?.results || [])
      .filter((c) => c.type === 'track_occupation' || c.type === 'sequence')
      .flatMap((c) => c.train_ids),
  )
  return { min, span: Math.max(max - min, 1), conflictTrains }
}
