import { useState } from 'react'
import { TRAIN_TYPE_LABEL, toLocalInput } from '../utils'

function blankTrain(tracks, locos) {
  return {
    id: null,
    code: '',
    train_type: 'normal',
    arrival_time: '2026-09-18T08:00',
    departure_time: '2026-09-18T09:00',
    length_m: 500,
    weight_t: 2000,
    max_width_m: 3.2,
    max_height_m: 4.5,
    track_id: tracks[0]?.id ?? null,
    locomotive_id: locos[0]?.id ?? null,
    sequence_no: 1,
    destination: '',
    note: '',
  }
}

function Row({ train, tracks, locos, onChange, onSave, onDelete, saving }) {
  const set = (k, v) => onChange({ ...train, [k]: v })
  const isNew = !train.id
  return (
    <tr>
      <td><input style={{ width: 80 }} value={train.code} onChange={(e) => set('code', e.target.value)} /></td>
      <td>
        <select value={train.train_type} onChange={(e) => set('train_type', e.target.value)}>
          {Object.entries(TRAIN_TYPE_LABEL).map(([v, l]) => <option key={v} value={v}>{l}</option>)}
        </select>
      </td>
      <td><input type="datetime-local" value={toLocalInput(train.arrival_time)}
        onChange={(e) => set('arrival_time', e.target.value)} /></td>
      <td><input type="datetime-local" value={toLocalInput(train.departure_time)}
        onChange={(e) => set('departure_time', e.target.value)} /></td>
      <td><input type="number" style={{ width: 70 }} value={train.length_m}
        onChange={(e) => set('length_m', +e.target.value)} /></td>
      <td><input type="number" style={{ width: 70 }} value={train.weight_t}
        onChange={(e) => set('weight_t', +e.target.value)} /></td>
      <td><input type="number" step="0.01" style={{ width: 68 }} value={train.max_width_m}
        onChange={(e) => set('max_width_m', +e.target.value)} /></td>
      <td><input type="number" step="0.01" style={{ width: 68 }} value={train.max_height_m}
        onChange={(e) => set('max_height_m', +e.target.value)} /></td>
      <td>
        <select style={{ width: 70 }} value={train.track_id ?? ''}
          onChange={(e) => set('track_id', e.target.value ? +e.target.value : null)}>
          <option value="">未分配</option>
          {tracks.map((t) => <option key={t.id} value={t.id}>{t.name}</option>)}
        </select>
      </td>
      <td>
        <select style={{ width: 90 }} value={train.locomotive_id ?? ''}
          onChange={(e) => set('locomotive_id', e.target.value ? +e.target.value : null)}>
          <option value="">未指派</option>
          {locos.map((l) => <option key={l.id} value={l.id}>{l.name}</option>)}
        </select>
      </td>
      <td><input type="number" style={{ width: 55 }} value={train.sequence_no ?? ''}
        onChange={(e) => set('sequence_no', e.target.value === '' ? null : +e.target.value)} /></td>
      <td><input style={{ width: 80 }} value={train.destination}
        onChange={(e) => set('destination', e.target.value)} /></td>
      <td style={{ whiteSpace: 'nowrap' }}>
        <button className="sm" disabled={saving} onClick={() => onSave(train)}>
          {isNew ? '新增' : '保存'}
        </button>{' '}
        {!isNew && (
          <button className="sm danger" disabled={saving} onClick={() => onDelete(train)}>删除</button>
        )}
      </td>
    </tr>
  )
}

export default function TrainsPanel({ trains, tracks, locos, onMutate }) {
  const [drafts, setDrafts] = useState([])
  const [saving, setSaving] = useState(false)

  const save = async (train) => {
    setSaving(true)
    try {
      await onMutate('train', train)
      setDrafts((d) => d.filter((x) => x !== train))
    } finally {
      setSaving(false)
    }
  }

  const remove = async (train) => {
    if (!window.confirm(`确认删除货列 ${train.code}？`)) return
    setSaving(true)
    try {
      await onMutate('deleteTrain', train)
    } finally {
      setSaving(false)
    }
  }

  return (
    <div className="panel">
      <h2>货列到达计划 <span className="hint">配置到达/发车时间、车列尺寸、股道与机车指派、编组序号</span></h2>
      <div className="toolbar">
        <button className="ghost" onClick={() => setDrafts((d) => [...d, blankTrain(tracks, locos)])}>
          ＋ 新增货列
        </button>
      </div>
      <div style={{ overflowX: 'auto' }}>
        <table className="grid">
          <thead>
            <tr>
              <th>车次</th><th>类型</th><th>到达时间</th><th>发车时间</th>
              <th>车列长(m)</th><th>总重(t)</th><th>最大宽(m)</th><th>最大高(m)</th>
              <th>股道</th><th>机车</th><th>编组序号</th><th>到站</th><th>操作</th>
            </tr>
          </thead>
          <tbody>
            {trains.map((t) => (
              <Row key={t.id} train={t} tracks={tracks} locos={locos}
                onChange={(nt) => onMutate('stageTrain', nt)}
                onSave={save} onDelete={remove} saving={saving} />
            ))}
            {drafts.map((t, i) => (
              <Row key={`draft-${i}`} train={t} tracks={tracks} locos={locos}
                onChange={(nt) => setDrafts((d) => d.map((x, j) => j === i ? nt : x))}
                onSave={save} onDelete={() => setDrafts((d) => d.filter((_, j) => j !== i))}
                saving={saving} />
            ))}
          </tbody>
        </table>
      </div>
    </div>
  )
}
