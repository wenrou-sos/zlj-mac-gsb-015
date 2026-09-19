/** API 封装：默认走同源 /api（开发环境由 Vite 代理，生产由 Nginx 代理）。 */
const BASE = import.meta.env.VITE_API_URL || '/api'

async function request(path, options = {}) {
  const resp = await fetch(`${BASE}${path}`, {
    headers: { 'Content-Type': 'application/json' },
    ...options,
  })
  if (!resp.ok) {
    let detail = resp.statusText
    try {
      const body = await resp.json()
      detail = body.detail || detail
    } catch { /* 忽略非 JSON 响应 */ }
    throw new Error(detail)
  }
  return resp.status === 204 ? null : resp.json()
}

export const api = {
  list: (resource) => request(`/${resource}`),
  create: (resource, data) => request(`/${resource}`, { method: 'POST', body: JSON.stringify(data) }),
  update: (resource, id, data) => request(`/${resource}/${id}`, { method: 'PUT', body: JSON.stringify(data) }),
  remove: (resource, id) => request(`/${resource}/${id}`, { method: 'DELETE' }),
  runAnalysis: () => request('/analysis/run', { method: 'POST' }),
  latestAnalysis: () => request('/analysis/latest'),
  analysisHistory: () => request('/analysis/runs'),
}
