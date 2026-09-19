import { useState } from 'react'

const CATEGORY_LABEL = {
  track: '股道规则',
  gauge: '限界规则',
  locomotive: '机车规则',
  switch: '检查开关',
  general: '通用',
  custom: '自定义',
}

export default function RulesPanel({ rules, onUpdate, onReset }) {
  const [editing, setEditing] = useState({})

  const groups = {}
  for (const r of rules) {
    ;(groups[r.category] ||= []).push(r)
  }

  const draft = (key) => (key in editing ? editing[key] : null)

  return (
    <div className="panel">
      <h2>编组规则 <span className="hint">修改后点击保存，下一次分析立即生效；重置可恢复系统默认值</span></h2>
      {Object.entries(groups).map(([cat, rows]) => (
        <div key={cat} style={{ marginBottom: 18 }}>
          <h3 style={{ fontSize: 13, color: '#9fb5c9', margin: '8px 0' }}>
            {CATEGORY_LABEL[cat] || cat}
          </h3>
          <table className="grid">
            <tbody>
              {rows.map((r) => {
                const val = draft(r.key)
                const current = val === null ? r.value : val
                return (
                  <tr key={r.key} className="rule-row">
                    <td style={{ width: 240 }}>
                      <b>{r.label || r.key}</b>
                      <div className="rule-desc">{r.description}</div>
                      <div className="rule-desc">key: {r.key}</div>
                    </td>
                    <td style={{ width: 220 }}>
                      {r.value_type === 'boolean' ? (
                        <input type="checkbox" checked={!!current}
                          onChange={(e) => setEditing((s) => ({ ...s, [r.key]: e.target.checked }))} />
                      ) : (
                        <input
                          type={r.value_type === 'number' ? 'number' : 'text'}
                          step="any"
                          value={current ?? ''}
                          onChange={(e) => setEditing((s) => ({
                            ...s,
                            [r.key]: r.value_type === 'number' ? +e.target.value : e.target.value,
                          }))}
                        />
                      )}
                    </td>
                    <td>
                      {r.customized && <span className="badge medium">已自定义</span>}{' '}
                      {val !== null && <span className="badge low">未保存</span>}
                    </td>
                    <td style={{ width: 160 }}>
                      {val !== null && (
                        <button className="sm" onClick={async () => {
                          await onUpdate(r.key, val)
                          setEditing((s) => { const n = { ...s }; delete n[r.key]; return n })
                        }}>保存</button>
                      )}{' '}
                      {r.customized && val === null && (
                        <button className="sm ghost" onClick={() => onReset(r.key)}>重置默认</button>
                      )}
                    </td>
                  </tr>
                )
              })}
            </tbody>
          </table>
        </div>
      ))}
    </div>
  )
}
