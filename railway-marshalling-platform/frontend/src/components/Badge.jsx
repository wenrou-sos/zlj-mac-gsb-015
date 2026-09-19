export function Badge({ severity, children }) {
  return <span className={`badge ${severity || 'neutral'}`}>{children}</span>
}

export function SeverityBadge({ severity }) {
  const map = { high: '高风险', medium: '中风险', low: '低风险' }
  return <Badge severity={severity}>{map[severity] || severity}</Badge>
}
