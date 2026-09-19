import { fmtTime } from '../utils'

/**
 * 甘特式时间轴：
 * 按股道、机车分组泳道；每列车一个色块，颜色取其最高冲突等级。
 */
export default function Timeline({ analysis, trains, tracks, locos }) {
  if (!trains.length) return null

  const start = new Date(analysis.timeline_start || trains[0].arrival_time).getTime()
  const end = new Date(analysis.timeline_end || trains[0].departure_time).getTime()
  const span = Math.max(end - start, 60_000)
  const PAD = 15 * 60_000
  const vStart = start - PAD
  const vEnd = end + PAD
  const vSpan = vEnd - vStart

  const pct = (t) => ((new Date(t).getTime() - vStart) / vSpan) * 100

  // 每列车的最高冲突等级
  const rank = { high: 3, medium: 2, low: 1 }
  const worstByTrain = {}
  for (const c of analysis.conflicts || []) {
    const cur = worstByTrain[c.train_code]
    if (!c.train_code) continue
    if (!cur || rank[c.severity] > rank[cur]) worstByTrain[c.train_code] = c.severity
  }

  // 小时刻度
  const ticks = []
  const tickStart = new Date(vStart)
  tickStart.setMinutes(0, 0, 0)
  for (let t = tickStart.getTime(); t < vEnd; t += 60 * 60_000) {
    if (t >= vStart) ticks.push(t)
  }

  const groups = [
    {
      title: '股道占用',
      lanes: tracks.map((tk) => ({
        key: `t-${tk.id}`,
        title: tk.name,
        sub: `${tk.length_m}m`,
        bars: trains.filter((tr) => tr.track_id === tk.id),
      })).concat([{
        key: 't-none',
        title: '未分配',
        sub: '',
        bars: trains.filter((tr) => !tr.track_id),
      }]).filter((l) => l.bars.length > 0),
    },
    {
      title: '机车担当',
      lanes: locos.map((l) => ({
        key: `l-${l.id}`,
        title: l.name,
        sub: l.model,
        bars: trains.filter((tr) => tr.locomotive_id === l.id),
      })).concat([{
        key: 'l-none',
        title: '未指派',
        sub: '',
        bars: trains.filter((tr) => !tr.locomotive_id),
      }]).filter((l) => l.bars.length > 0),
    },
  ]

  return (
    <div className="timeline-wrap">
      <div className="timeline">
        {groups.map((g) => (
          <div key={g.title}>
            <div className="tl-section-title">{g.title}</div>
            {g.lanes.map((lane) => (
              <div className="tl-lane" key={lane.key}>
                <div className="tl-lane-title">
                  <b>{lane.title}</b>
                  <span>{lane.sub}</span>
                </div>
                <div className="tl-track">
                  {ticks.map((t) => (
                    <div key={t}>
                      <div className="tl-grid-line" style={{ left: `${pct(t)}%` }} />
                      <div className="tl-grid-label" style={{ left: `${pct(t)}%` }}>
                        {fmtTime(new Date(t).toISOString())}
                      </div>
                    </div>
                  ))}
                  {lane.bars.map((tr) => {
                    const left = pct(tr.arrival_time)
                    const width = Math.max(
                      (new Date(tr.departure_time) - new Date(tr.arrival_time)) / vSpan * 100,
                      1.5,
                    )
                    const sev = worstByTrain[tr.code]
                    const cls = tr.track_id === null || tr.locomotive_id === null
                      ? (tr.track_id === null && lane.key.startsWith('t-') ? 'unassigned'
                        : tr.locomotive_id === null && lane.key.startsWith('l-') ? 'unassigned'
                          : sev ? `has-${sev}` : '')
                      : sev ? `has-${sev}` : ''
                    return (
                      <div
                        key={`${lane.key}-${tr.id}`}
                        className={`tl-bar ${cls}`}
                        style={{ left: `${left}%`, width: `${width}%` }}
                        title={`${tr.code}｜${fmtTime(tr.arrival_time)}–${fmtTime(tr.departure_time)}`
                          + `${sev ? `｜最高${sev === 'high' ? '高' : sev === 'medium' ? '中' : '低'}风险` : ''}`}
                      >
                        {tr.code}
                      </div>
                    )
                  })}
                </div>
              </div>
            ))}
          </div>
        ))}
      </div>
    </div>
  )
}
