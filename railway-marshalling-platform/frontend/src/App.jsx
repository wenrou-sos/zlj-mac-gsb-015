import { useCallback, useEffect, useMemo, useState } from 'react'
import { api } from './api'
import Timeline from './components/Timeline'
import ConflictPanel from './components/ConflictPanel'
import TrainsPanel from './components/TrainsPanel'
import TracksLocosPanel from './components/TracksLocosPanel'
import RulesPanel from './components/RulesPanel'
import Toast from './components/Toast'

const TABS = [
  { key: 'dashboard', label: '冲突总览' },
  { key: 'trains', label: '货列计划' },
  { key: 'resources', label: '股道 / 机车' },
  { key: 'rules', label: '编组规则' },
]

export default function App() {
  const [tab, setTab] = useState('dashboard')
  const [trains, setTrains] = useState([])
  const [tracks, setTracks] = useState([])
  const [locos, setLocos] = useState([])
  const [rules, setRules] = useState([])
  const [analysis, setAnalysis] = useState(null)
  const [health, setHealth] = useState('checking')
  const [error, setError] = useState('')
  const [toast, setToast] = useState('')
  const [applying, setApplying] = useState(false)
  const [loading, setLoading] = useState(true)

  const showToast = (msg) => {
    setToast(msg)
    setTimeout(() => setToast(''), 2600)
  }

  const loadAll = useCallback(async () => {
    const [t, tk, lc, rl, an] = await Promise.all([
      api.listTrains(), api.listTracks(), api.listLocos(),
      api.listRules(), api.analysis(),
    ])
    setTrains(t.items)
    setTracks(tk.items)
    setLocos(lc.items)
    setRules(rl.items)
    setAnalysis(an)
  }, [])

  const refreshAnalysis = useCallback(async () => {
    setAnalysis(await api.analysis())
  }, [])

  useEffect(() => {
    (async () => {
      try {
        await api.health()
        setHealth('ok')
        await loadAll()
      } catch (e) {
        setHealth('offline')
        setError(`加载数据失败：${e.message}`)
      } finally {
        setLoading(false)
      }
    })()
  }, [loadAll])

  // ---------------- 数据增删改 ----------------
  const mutate = async (kind, payload) => {
    setError('')
    try {
      switch (kind) {
        case 'stageTrain':
          setTrains((list) => list.map((x) => (x.id === payload.id ? payload : x)))
          return
        case 'train':
          if (payload.id) await api.updateTrain(payload.id, payload)
          else await api.createTrain(payload)
          showToast(payload.id ? '货列已保存' : '货列已新增')
          break
        case 'deleteTrain':
          await api.deleteTrain(payload.id)
          showToast(`货列 ${payload.code} 已删除`)
          break
        case 'stageTrack':
          setTracks((list) => list.map((x) => (x.id === payload.id ? payload : x)))
          return
        case 'track':
          if (payload.id) await api.updateTrack(payload.id, payload)
          else await api.createTrack(payload)
          showToast('股道已保存')
          break
        case 'deleteTrack':
          await api.deleteTrack(payload.id)
          showToast(`股道 ${payload.name} 已删除`)
          break
        case 'stageLoco':
          setLocos((list) => list.map((x) => (x.id === payload.id ? payload : x)))
          return
        case 'loco':
          if (payload.id) await api.updateLoco(payload.id, payload)
          else await api.createLoco(payload)
          showToast('机车已保存')
          break
        case 'deleteLoco':
          await api.deleteLoco(payload.id)
          showToast(`机车 ${payload.name} 已删除`)
          break
        default:
          return
      }
      await loadAll()
    } catch (e) {
      setError(e.message)
      await loadAll().catch(() => {})
    }
  }

  const updateRule = async (key, value) => {
    setError('')
    try {
      await api.updateRule(key, value)
      showToast('规则已更新')
      await loadAll()
    } catch (e) {
      setError(e.message)
    }
  }

  const resetRule = async (key) => {
    setError('')
    try {
      await api.resetRule(key)
      showToast('已恢复默认值')
      await loadAll()
    } catch (e) {
      setError(e.message)
    }
  }

  // ---------------- 采纳建议 ----------------
  const applySuggestion = async (conflict, sug) => {
    const trainCode = conflict.train_code || conflict.related_train_code
    if (!trainCode) {
      setError('该建议需要人工在货列计划中调整')
      return
    }
    const train = trains.find((t) => t.code === trainCode)
    if (!train) return
    const next = { ...train }

    if (sug.target_track_id) next.track_id = sug.target_track_id
    if (sug.target_locomotive_id) next.locomotive_id = sug.target_locomotive_id
    if (sug.new_sequence_no != null) next.sequence_no = sug.new_sequence_no
    if (sug.new_arrival_time) {
      const newStart = new Date(sug.new_arrival_time)
      const oldStart = new Date(train.arrival_time)
      const oldEnd = new Date(train.departure_time)
      const duration = oldEnd - oldStart
      next.arrival_time = newStart.toISOString()
      next.departure_time = new Date(newStart.getTime() + duration).toISOString()
    }

    setApplying(true)
    try {
      await api.updateTrain(train.id, next)
      showToast(`已采纳建议：${sug.description}`)
      await loadAll()
    } catch (e) {
      setError(e.message)
    } finally {
      setApplying(false)
    }
  }

  const summary = analysis?.summary
  const stats = useMemo(() => ([
    { label: '货列总数', value: analysis?.train_count ?? '-' },
    { label: '股道数量', value: analysis?.track_count ?? '-' },
    { label: '机车数量', value: analysis?.locomotive_count ?? '-' },
    { label: '高风险冲突', value: summary?.high ?? '-', cls: 'high' },
    { label: '中风险冲突', value: summary?.medium ?? '-', cls: 'medium' },
    { label: '低风险提示', value: summary?.low ?? '-', cls: 'low' },
  ]), [analysis, summary])

  return (
    <>
      <header className="app-header">
        <h1>🚦 铁路货运编组冲突分析平台</h1>
        <span className="sub">股道占用 · 顺序冲突 · 超限风险 · 机车资源</span>
        <div className="header-spacer" />
        <span className={`health-dot ${health === 'ok' ? '' : 'offline'}`}>
          <span className="dot" />
          {health === 'ok' ? '后端服务正常' : health === 'checking' ? '连接中…' : '后端不可用'}
        </span>
        <button className="ghost" onClick={() => refreshAnalysis()}>🔄 重新分析</button>
      </header>

      <nav className="tabs">
        {TABS.map((t) => (
          <div key={t.key}
            className={`tab ${tab === t.key ? 'active' : ''}`}
            onClick={() => setTab(t.key)}>
            {t.label}
          </div>
        ))}
      </nav>

      <main className="content">
        {error && <div className="error-banner">⚠️ {error}</div>}
        {loading && <div className="empty-state">数据加载中…</div>}

        {!loading && tab === 'dashboard' && analysis && (
          <>
            <div className="cards">
              {stats.map((s) => (
                <div key={s.label} className={`card ${s.cls || ''}`}>
                  <div className="label">{s.label}</div>
                  <div className="value">{s.value}</div>
                </div>
              ))}
            </div>

            <div className="panel">
              <h2>班计划时间轴
                <span className="hint">色块按该货列最高冲突等级着色，悬停查看详情</span>
              </h2>
              <Timeline analysis={analysis} trains={trains} tracks={tracks} locos={locos} />
            </div>

            <div className="panel">
              <h2>股道利用统计</h2>
              <table className="grid">
                <thead>
                  <tr><th>股道</th><th>接入列数</th><th>占用长度</th><th>利用率</th></tr>
                </thead>
                <tbody>
                  {analysis.track_stats.map((s) => {
                    const over = s.utilization > 1
                    return (
                      <tr key={s.track_id ?? 'none'}>
                        <td>{s.track_name}</td>
                        <td>{s.trains}</td>
                        <td>{s.used_length_m} / {s.capacity_m || '—'} m</td>
                        <td>
                          <span className="stat-bar-wrap">
                            <span className={`stat-bar ${over ? 'over' : ''}`}
                              style={{ width: `${Math.min(s.utilization * 100, 100)}%` }} />
                          </span>
                          {s.capacity_m ? `${(s.utilization * 100).toFixed(0)}%` : '—'}
                        </td>
                      </tr>
                    )
                  })}
                </tbody>
              </table>
            </div>

            <div className="panel">
              <h2>冲突检测结果与调整建议
                <span className="hint">共 {summary?.total ?? 0} 项，可直接点击「采纳」应用建议</span>
              </h2>
              <ConflictPanel analysis={analysis} onApply={applySuggestion} applying={applying} />
            </div>
          </>
        )}

        {!loading && tab === 'trains' && (
          <TrainsPanel trains={trains} tracks={tracks} locos={locos} onMutate={mutate} />
        )}
        {!loading && tab === 'resources' && (
          <TracksLocosPanel tracks={tracks} locos={locos} onMutate={mutate} />
        )}
        {!loading && tab === 'rules' && (
          <RulesPanel rules={rules} onUpdate={updateRule} onReset={resetRule} />
        )}
      </main>

      <Toast message={toast} />
    </>
  )
}
