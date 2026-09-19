import { useCallback, useEffect, useState } from 'react'
import { api } from '../api'

/**
 * 通用资源管理页：列表 + 新增/编辑表单 + 删除。
 * fields 配置驱动表单与表格渲染。
 */
export default function ResourcePage({ resource, title, fields, columns }) {
  const [items, setItems] = useState([])
  const [options, setOptions] = useState({})
  const [editing, setEditing] = useState(null) // null=关闭, {}=新增, {id:...}=编辑
  const [error, setError] = useState('')

  const load = useCallback(async () => {
    try {
      setItems(await api.list(resource))
      setError('')
    } catch (e) {
      setError(`加载失败：${e.message}（请确认后端已启动）`)
    }
  }, [resource])

  useEffect(() => { load() }, [load])

  // 加载 select 字段的选项来源
  useEffect(() => {
    fields.filter((f) => f.optionsSource).forEach((f) => {
      api.list(f.optionsSource).then((data) =>
        setOptions((prev) => ({ ...prev, [f.name]: data }))).catch(() => {})
    })
  }, [fields])

  const blank = () => Object.fromEntries(fields.map((f) => [f.name, f.default ?? '']))

  const submit = async (e) => {
    e.preventDefault()
    const payload = {}
    for (const f of fields) {
      let v = editing[f.name]
      if (v === '' || v === undefined) { payload[f.name] = null; continue }
      if (f.type === 'number') v = Number(v)
      if (f.type === 'checkbox') v = Boolean(v)
      if (f.type === 'datetime') v = new Date(v).toISOString()
      payload[f.name] = v
    }
    try {
      if (editing.id) await api.update(resource, editing.id, payload)
      else await api.create(resource, payload)
      setEditing(null)
      load()
    } catch (err) {
      alert(`保存失败：${err.message}`)
    }
  }

  const remove = async (id) => {
    if (!window.confirm('确认删除该记录？')) return
    await api.remove(resource, id)
    load()
  }

  return (
    <section>
      <div className="page-header">
        <h2>{title}</h2>
        <button className="btn primary" onClick={() => setEditing(blank())}>+ 新增</button>
      </div>
      {error && <div className="alert error">{error}</div>}

      {editing && (
        <form className="card form-grid" onSubmit={submit}>
          <h3>{editing.id ? `编辑 #${editing.id}` : '新增记录'}</h3>
          {fields.map((f) => (
            <label key={f.name} className="form-field">
              <span>{f.label}</span>
              {f.type === 'select' ? (
                <select value={editing[f.name] ?? ''} required={f.required}
                  onChange={(e) => setEditing({ ...editing, [f.name]: e.target.value })}>
                  <option value="">（未指定）</option>
                  {(f.options || options[f.name] || []).map((o) => (
                    <option key={o.value ?? o.id} value={o.value ?? o.id}>
                      {o.label ?? o[f.optionLabel || 'name']}
                    </option>
                  ))}
                </select>
              ) : f.type === 'checkbox' ? (
                <input type="checkbox" checked={Boolean(editing[f.name])}
                  onChange={(e) => setEditing({ ...editing, [f.name]: e.target.checked })} />
              ) : (
                <input
                  type={f.type === 'datetime' ? 'datetime-local' : f.type}
                  step={f.type === 'number' ? 'any' : undefined}
                  required={f.required}
                  value={f.type === 'datetime' && editing[f.name]
                    ? String(editing[f.name]).slice(0, 16) : editing[f.name] ?? ''}
                  onChange={(e) => setEditing({ ...editing, [f.name]: e.target.value })} />
              )}
            </label>
          ))}
          <div className="form-actions">
            <button type="submit" className="btn primary">保存</button>
            <button type="button" className="btn" onClick={() => setEditing(null)}>取消</button>
          </div>
        </form>
      )}

      <div className="card table-wrap">
        <table>
          <thead>
            <tr>
              {columns.map((c) => <th key={c.key}>{c.label}</th>)}
              <th>操作</th>
            </tr>
          </thead>
          <tbody>
            {items.map((item) => (
              <tr key={item.id}>
                {columns.map((c) => (
                  <td key={c.key}>{c.render ? c.render(item) : String(item[c.key] ?? '—')}</td>
                ))}
                <td className="row-actions">
                  <button className="btn small" onClick={() => setEditing({ ...item })}>编辑</button>
                  <button className="btn small danger" onClick={() => remove(item.id)}>删除</button>
                </td>
              </tr>
            ))}
            {items.length === 0 && !error && (
              <tr><td colSpan={columns.length + 1} className="empty">暂无数据</td></tr>
            )}
          </tbody>
        </table>
      </div>
    </section>
  )
}
