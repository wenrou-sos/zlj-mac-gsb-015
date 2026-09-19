import { SeverityBadge } from './Badge'

const ACTION_LABEL = {
  reassign_track: '改派股道',
  reassign_loco: '更换机车',
  reschedule: '调整时间',
  fix_sequence: '修正序号',
  manual_review: '人工复核',
}

export default function ConflictPanel({ analysis, onApply, applying }) {
  const conflicts = analysis?.conflicts || []

  return (
    <div>
      {conflicts.length === 0 && (
        <div className="empty-state">
          <div className="big">✅</div>
          当前编组计划未检测到冲突
        </div>
      )}
      {conflicts.map((c, idx) => (
        <div key={`${c.code}-${c.train_code}-${idx}`} className={`conflict ${c.severity}`}>
          <div className="head">
            <SeverityBadge severity={c.severity} />
            <strong>{c.title}</strong>
            <span className="code">{c.code}</span>
            {c.train_code && <span className="badge neutral">货列 {c.train_code}</span>}
            {c.track_name && <span className="badge neutral">股道 {c.track_name}</span>}
            {c.locomotive_name && <span className="badge neutral">机车 {c.locomotive_name}</span>}
            {c.related_train_code && (
              <span className="badge neutral">关联 {c.related_train_code}</span>
            )}
          </div>
          <div className="detail">{c.detail}</div>
          {c.suggestions?.length > 0 && (
            <div className="sugs">
              <span style={{ color: '#8aa0b5', fontSize: 12, alignSelf: 'center' }}>
                调整建议：
              </span>
              {c.suggestions.map((s, i) => (
                <span className="sug" key={i}>
                  <span className="action-tag">{ACTION_LABEL[s.action] || s.action}</span>
                  {s.description}
                  {s.action !== 'manual_review' && (
                    <button
                      className="sm"
                      disabled={applying}
                      onClick={() => onApply(c, s)}
                    >
                      {applying ? '处理中…' : '采纳'}
                    </button>
                  )}
                </span>
              ))}
            </div>
          )}
        </div>
      ))}
    </div>
  )
}
