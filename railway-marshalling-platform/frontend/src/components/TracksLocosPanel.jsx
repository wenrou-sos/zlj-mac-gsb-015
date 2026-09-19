import { useState } from 'react'
import { LOCO_STATUS_LABEL, toLocalInput } from '../utils'

function TrackRow({ track, onChange, onSave, onDelete }) {
  const set = (k, v) => onChange({ ...track, [k]: v })
  const isNew = !track.id
  return (
    <tr>
      <td><input style={{ width: 70 }} value={track.name} onChange={(e) => set('name', e.target.value)} /></td>
      <td>
        <select value={track.track_kind} onChange={(e) => set('track_kind', e.target.value)}>
          <option value="classification">编组线</option>
          <option value="storage">停留线</option>
          <option value="departure">出发线</option>
          <option value="arrival">到达线</option>
        </select>
      </td>
      <td><input type="number" style={{ width: 80 }} value={track.length_m}
        onChange={(e) => set('length_m', +e.target.value)} /></td>
      <td><input type="number" style={{ width: 80 }} value={track.occupied_length_m}
        onChange={(e) => set('occupied_length_m', +e.target.value)} /></td>
      <td><input type="number" style={{ width: 80 }} value={track.max_load_t}
        onChange={(e) => set('max_load_t', +e.target.value)} /></td>
      <td><input type="checkbox" checked={track.allow_dangerous}
        onChange={(e) => set('allow_dangerous', e.target.checked)} /></td>
      <td><input type="checkbox" checked={track.allow_overload}
        onChange={(e) => set('allow_overload', e.target.checked)} /></td>
      <td style={{ whiteSpace: 'nowrap' }}>
        <button className="sm" onClick={() => onSave(track)}>{isNew ? '新增' : '保存'}</button>{' '}
        {!isNew && <button className="sm danger" onClick={() => onDelete(track)}>删除</button>}
      </td>
    </tr>
  )
}

function LocoRow({ loco, onChange, onSave, onDelete }) {
  const set = (k, v) => onChange({ ...loco, [k]: v })
  const isNew = !loco.id
  return (
    <tr>
      <td><input style={{ width: 90 }} value={loco.name} onChange={(e) => set('name', e.target.value)} /></td>
      <td><input style={{ width: 120 }} value={loco.model} onChange={(e) => set('model', e.target.value)} /></td>
      <td><input type="number" style={{ width: 80 }} value={loco.power_kw}
        onChange={(e) => set('power_kw', +e.target.value)} /></td>
      <td>
        <select value={loco.status} onChange={(e) => set('status', e.target.value)}>
          {Object.entries(LOCO_STATUS_LABEL).map(([v, l]) => <option key={v} value={v}>{l}</option>)}
        </select>
      </td>
      <td><input type="datetime-local" style={{ width: 160 }} value={toLocalInput(loco.available_from)}
        onChange={(e) => set('available_from', e.target.value || null)} /></td>
      <td><input type="datetime-local" style={{ width: 160 }} value={toLocalInput(loco.available_to)}
        onChange={(e) => set('available_to', e.target.value || null)} /></td>
      <td style={{ whiteSpace: 'nowrap' }}>
        <button className="sm" onClick={() => onSave(loco)}>{isNew ? '新增' : '保存'}</button>{' '}
        {!isNew && <button className="sm danger" onClick={() => onDelete(loco)}>删除</button>}
      </td>
    </tr>
  )
}

const blankTrack = {
  id: null, name: '', track_kind: 'classification', length_m: 800,
  occupied_length_m: 0, max_load_t: 4000, allow_dangerous: false, allow_overload: false, note: '',
}
const blankLoco = {
  id: null, name: '', model: '', power_kw: 1500, status: 'available',
  available_from: null, available_to: null, note: '',
}

export default function TracksLocosPanel({ tracks, locos, onMutate }) {
  const [newTracks, setNewTracks] = useState([])
  const [newLocos, setNewLocos] = useState([])

  const saveTrack = async (t) => {
    await onMutate('track', t)
    setNewTracks((d) => d.filter((x) => x !== t))
  }
  const deleteTrack = async (t) => {
    if (!window.confirm(`确认删除股道 ${t.name}？相关货列指派将被清空。`)) return
    await onMutate('deleteTrack', t)
  }
  const saveLoco = async (l) => {
    await onMutate('loco', l)
    setNewLocos((d) => d.filter((x) => x !== l))
  }
  const deleteLoco = async (l) => {
    if (!window.confirm(`确认删除机车 ${l.name}？`)) return
    await onMutate('deleteLoco', l)
  }

  return (
    <>
      <div className="panel">
        <h2>股道资源 <span className="hint">有效长度、现存车辆占用、允许载重、危险品/超限接车条件</span></h2>
        <div className="toolbar">
          <button className="ghost" onClick={() => setNewTracks((d) => [...d, { ...blankTrack }])}>
            ＋ 新增股道
          </button>
        </div>
        <div style={{ overflowX: 'auto' }}>
          <table className="grid">
            <thead>
              <tr>
                <th>股道</th><th>类型</th><th>有效长度(m)</th><th>现存占用(m)</th>
                <th>允许载重(t)</th><th>可停危险品</th><th>可接超限</th><th>操作</th>
              </tr>
            </thead>
            <tbody>
              {tracks.map((t) => (
                <TrackRow key={t.id} track={t}
                  onChange={(nt) => onMutate('stageTrack', nt)}
                  onSave={saveTrack} onDelete={deleteTrack} />
              ))}
              {newTracks.map((t, i) => (
                <TrackRow key={`nt-${i}`} track={t}
                  onChange={(nt) => setNewTracks((d) => d.map((x, j) => j === i ? nt : x))}
                  onSave={saveTrack}
                  onDelete={() => setNewTracks((d) => d.filter((_, j) => j !== i))} />
              ))}
            </tbody>
          </table>
        </div>
      </div>

      <div className="panel">
        <h2>机车资源 <span className="hint">机车型号功率、检修状态与当班可用时间窗</span></h2>
        <div className="toolbar">
          <button className="ghost" onClick={() => setNewLocos((d) => [...d, { ...blankLoco }])}>
            ＋ 新增机车
          </button>
        </div>
        <div style={{ overflowX: 'auto' }}>
          <table className="grid">
            <thead>
              <tr>
                <th>机车号</th><th>型号</th><th>功率(kW)</th><th>状态</th>
                <th>可用起</th><th>可用止</th><th>操作</th>
              </tr>
            </thead>
            <tbody>
              {locos.map((l) => (
                <LocoRow key={l.id} loco={l}
                  onChange={(nl) => onMutate('stageLoco', nl)}
                  onSave={saveLoco} onDelete={deleteLoco} />
              ))}
              {newLocos.map((l, i) => (
                <LocoRow key={`nl-${i}`} loco={l}
                  onChange={(nl) => setNewLocos((d) => d.map((x, j) => j === i ? nl : x))}
                  onSave={saveLoco}
                  onDelete={() => setNewLocos((d) => d.filter((_, j) => j !== i))} />
              ))}
            </tbody>
          </table>
        </div>
      </div>
    </>
  )
}
