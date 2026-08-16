const API_BASE = String(import.meta.env.VITE_NEXUX_API_URL || '').replace(/\/$/, '')

async function request(path, init) {
  const response = await fetch(`${API_BASE}${path}`, {
    ...init,
    headers: {
      Accept: 'application/json',
      ...(init?.body ? { 'Content-Type': 'application/json' } : {}),
      ...(init?.headers || {}),
    },
  })

  if (!response.ok) {
    let detail = response.statusText || `HTTP ${response.status}`
    try {
      const body = await response.json()
      detail = body?.detail || detail
    } catch {}
    throw new Error(detail)
  }
  return response.json()
}

export const nexuxApi = {
  baseUrl: API_BASE,
  health: () => request('/api/health'),
  styles: () => request('/api/styles'),
  generate: (payload) => request('/api/generate', {
    method: 'POST',
    body: JSON.stringify(payload),
  }),
  job: (jobId) => request(`/api/job/${encodeURIComponent(jobId)}`),
  cancel: (jobId) => request(`/api/job/${encodeURIComponent(jobId)}`, { method: 'DELETE' }),
  downloadUrl: (jobId) => `${API_BASE}/api/download/${encodeURIComponent(jobId)}`,
}

export function startJobPolling(jobId, onUpdate, onFinish, intervalMs = 900) {
  let stopped = false
  let timer = null

  const tick = async () => {
    if (stopped) return
    try {
      const job = await nexuxApi.job(jobId)
      onUpdate(job)
      if (['completed', 'failed', 'cancelled', 'interrupted'].includes(job.status)) {
        onFinish(job)
        return
      }
    } catch (error) {
      onFinish({
        job_id: jobId,
        status: 'failed',
        progress: 0,
        stage: 'network_error',
        output_path: null,
        error: error instanceof Error ? error.message : String(error),
        clips: [],
        broll: false,
        render_meta: [],
        analysis_bundle: null,
      })
      return
    }
    timer = setTimeout(tick, intervalMs)
  }

  void tick()
  return () => {
    stopped = true
    if (timer) clearTimeout(timer)
  }
}
