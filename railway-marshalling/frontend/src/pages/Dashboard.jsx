import { useCallback, useEffect, useMemo, useState } from 'react'
import { api } from '../api'
import { buildTimeline, countByType } from '../utils'

const TYPE_META = {
  track_occupation: { label: '股道占用冲突', icon: '🛤️' },
  sequence: { label: '顺序冲突', icon: '🔀' },
  over_limit: { label: '超限风险', icon: '⚠️' },
  locomotive: { label: '机车冲突', icon: '🚂' },
}
const SEVERITY_LABEL = { high: '高', medium: '中', low: '低' }
const fmtTime = (v) => (v ? new Date(v).toLocaleString('zh-CN', { hour12: false }) : '未定')

export default function Dashboard() {
  const [analysis, setAnalysis] = useState(null)
  const [trains, setTrains] = useState([])
  const [tracks, setTracks] = useState([])
  const [running, setRunning] = useState(false)
  const [error, setError] = useState('')

  const load = useCallback(async () => {
    try {
      const [t, tk] = await Promise.all([api.list('trains'), api.list('tracks')])
      setTrains(t)
      setTracks(tk)
      setAnalysis(await api.latestAnalysis())
      setError('')
    } catch (e) {
      setError(e.message)
    }
  }, [])

  useEffect(() => { load() }, [load])

  const run = async () => {
    setRunning(true)
    try {
      setAnalysis(await api.runAnalysis())
      setError('')
    } catch (e) {
      setError(e.message)
    } finally {
      setRunning(false)
    }
  }

  const stats = useMemo(() => countByType(analysis?.results), [analysis])

  return (
    <section>
      <div className="page-header">
        <h2>冲突分析总览</h2>
        <button className="btn primary" onClick={run} disabled={running}>
          {running ? '分析中…' : '▶ 运行冲突分析'}
        </button>
      </div>
      {error && <div className="alert error">后端连接异常：{error}</div>}

      <div className="stat-grid">
        {Object.entries(TYPE_META).map(([type, meta]) => (
          <div key={type} className={`stat-card ${stats[type] ? 'has-conflict' : ''}`}>
            <span className="stat-icon">{meta.icon}</span>
            <div>
              <div className="stat-value">{stats[type] || 0}</div>
              <div className="stat-label">{meta.label}</div>
            </div>
          </div>
        ))}
      </div>

      {analysis && (
        <p className="muted">
          最近分析：{fmtTime(analysis.created_at)} ｜ 覆盖列车 {analysis.train_count} 列 ｜
          检出冲突 {analysis.conflict_count} 项
        </p>
      )}

      <TrackTimeline trains={trains} tracks={tracks} analysis={analysis} />

      <h3>冲突明细与调整建议</h3>
      {analysis?.results?.length ? (
        <div className="conflict-list">
          {analysis.results.map((c, i) => (
            <div key={i} className={`card conflict severity-${c.severity}`}>
              <div className="conflict-head">
                <span className={`badge severity-${c.severity}`}>
                  {SEVERITY_LABEL[c.severity]}风险
                </span>
                <span className="badge type">
                  {TYPE_META[c.type]?.icon} {TYPE_META[c.type]?.label || c.type}
                </span>
                <span className="muted">涉及列车 #{c.train_ids.join(' #')}</span>
              </div>
              <p className="conflict-message">{c.message}</p>
              <p className="conflict-suggestion">💡 {c.suggestion}</p>
            </div>
          ))}
        </div>
      ) : (
        <div className="card empty">
          {analysis ? '✅ 未检出冲突，当前编组计划可正常执行' : '尚未运行分析，点击右上角按钮开始'}
        </div>
      )}
    </section>
  )
}

/** 股道占用甘特图：按股道展示各列车占用时间窗。 */
function TrackTimeline({ trains, tracks, analysis }) {
  const data = useMemo(() => buildTimeline(trains, analysis), [trains, analysis])

  if (!data || !tracks.length) return null
  const { min, span, conflictTrains } = data
  const pct = (ts) => ((ts - min) / span) * 100

  return (
    <div className="card">
      <h3>股道占用时间窗</h3>
      <div className="timeline">
        {tracks.map((track) => (
          <div key={track.id} className="timeline-row">
            <div className="timeline-label">
              {track.name}
              <small>{track.length_m}m</small>
            </div>
            <div className="timeline-track">
              {trains.filter((t) => t.track_id === track.id).map((t) => {
                const start = new Date(t.arrival_time).getTime()
                const end = t.departure_time
                  ? new Date(t.departure_time).getTime()
                  : start + 6 * 3600e3
                const conflict = conflictTrains.has(t.id)
                return (
                  <div
                    key={t.id}
                    className={`timeline-bar ${conflict ? 'conflict' : ''}`}
                    style={{ left: `${pct(start)}%`, width: `${Math.max(pct(end) - pct(start), 1.5)}%` }}
                    title={`${t.train_number}：${fmtTime(t.arrival_time)} ~ ${fmtTime(t.departure_time)}`}
                  >
                    {t.train_number}
                  </div>
                )
              })}
            </div>
          </div>
        ))}
        <div className="timeline-axis">
          <span>{fmtTime(new Date(min).toISOString())}</span>
          <span>{fmtTime(new Date(min + span).toISOString())}</span>
        </div>
      </div>
    </div>
  )
}
