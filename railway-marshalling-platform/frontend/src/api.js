const BASE = '/api'

async function request(path, options = {}) {
  const resp = await fetch(`${BASE}${path}`, {
    headers: { 'Content-Type': 'application/json' },
    ...options,
  })
  if (!resp.ok) {
    let detail = `${resp.status} ${resp.statusText}`
    try {
      const body = await resp.json()
      detail = typeof body.detail === 'string' ? body.detail : JSON.stringify(body.detail)
    } catch {
      /* ignore */
    }
    throw new Error(detail)
  }
  if (resp.status === 204) return null
  return resp.json()
}

export const api = {
  health: () => request('/health'),
  analysis: () => request('/analysis'),

  listTrains: () => request('/trains'),
  createTrain: (data) => request('/trains', { method: 'POST', body: JSON.stringify(data) }),
  updateTrain: (id, data) => request(`/trains/${id}`, { method: 'PUT', body: JSON.stringify(data) }),
  deleteTrain: (id) => request(`/trains/${id}`, { method: 'DELETE' }),

  listTracks: () => request('/tracks'),
  createTrack: (data) => request('/tracks', { method: 'POST', body: JSON.stringify(data) }),
  updateTrack: (id, data) => request(`/tracks/${id}`, { method: 'PUT', body: JSON.stringify(data) }),
  deleteTrack: (id) => request(`/tracks/${id}`, { method: 'DELETE' }),

  listLocos: () => request('/locomotives'),
  createLoco: (data) => request('/locomotives', { method: 'POST', body: JSON.stringify(data) }),
  updateLoco: (id, data) => request(`/locomotives/${id}`, { method: 'PUT', body: JSON.stringify(data) }),
  deleteLoco: (id) => request(`/locomotives/${id}`, { method: 'DELETE' }),

  listRules: () => request('/rules'),
  updateRule: (key, value) => request(`/rules/${key}`, {
    method: 'PUT',
    body: JSON.stringify({ value }),
  }),
  resetRule: (key) => request(`/rules/${key}`, { method: 'DELETE' }),
}
