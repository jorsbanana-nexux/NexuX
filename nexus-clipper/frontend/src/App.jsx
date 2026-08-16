import { useEffect, useMemo, useState } from 'react'
import { motion } from 'framer-motion'

const API = (import.meta.env.VITE_NEXUX_API_URL || 'http://127.0.0.1:8000').replace(/\/$/, '')

async function request(path, init) {
  const res = await fetch(`${API}${path}`, {
    ...init,
    headers: { Accept: 'application/json', ...(init?.body ? { 'Content-Type': 'application/json' } : {}), ...(init?.headers || {}) },
  })
  if (!res.ok) {
    let message = res.statusText || `HTTP ${res.status}`
    try { message = (await res.json())?.detail || message } catch {}
    throw new Error(message)
  }
  return res.json()
}

const presets = [
  ['hormozi', 'HORMOZI'],
  ['minimal', 'MINIMAL'],
  ['gamer', 'GAMER'],
  ['karaoke', 'KARAOKE'],
]

export default function App() {
  const [url, setUrl] = useState('')
  const [duration, setDuration] = useState(45)
  const [preset, setPreset] = useState('hormozi')
  const [ratio, setRatio] = useState('9:16')
  const [clipCount, setClipCount] = useState(3)
  const [autoZoom, setAutoZoom] = useState(true)
  const [faceTracking, setFaceTracking] = useState(true)
  const [emoji, setEmoji] = useState(false)
  const [health, setHealth] = useState(null)
  const [job, setJob] = useState(null)
  const [error, setError] = useState('')
  const [busy, setBusy] = useState(false)

  useEffect(() => {
    request('/api/health').then(setHealth).catch(() => setHealth(null))
  }, [])

  useEffect(() => {
    if (!job?.job_id || ['completed', 'failed', 'cancelled'].includes(job.status)) return
    const timer = setInterval(async () => {
      try { setJob(await request(`/api/job/${encodeURIComponent(job.job_id)}`)) } catch (e) { setError(e.message) }
    }, 1600)
    return () => clearInterval(timer)
  }, [job?.job_id, job?.status])

  const progress = Math.max(0, Math.min(100, Number(job?.progress || 0)))
  const statusLabel = useMemo(() => {
    if (!job) return 'SYSTEM READY'
    if (job.status === 'completed') return 'MISSION COMPLETE'
    if (job.status === 'failed') return 'PIPELINE ERROR'
    return String(job.stage || job.status || 'PROCESSING').toUpperCase()
  }, [job])

  async function launch() {
    if (!url.trim()) return
    setBusy(true); setError(''); setJob(null)
    try {
      const payload = {
        youtube_url: url.trim(), target_duration: duration, aspect_ratio: ratio,
        subtitle_style: preset, font: 'Arial', font_size: 48,
        primary_color: '#FFFFFF', highlight_color: '#22D3EE', stroke_color: '#000000', stroke_width: 3,
        position: 'center', animation: 'bounce', auto_zoom: autoZoom, face_tracking: faceTracking,
        clip_count: clipCount, language: null, normalize_audio: true, emoji_enabled: emoji,
      }
      setJob(await request('/api/generate', { method: 'POST', body: JSON.stringify(payload) }))
    } catch (e) { setError(e.message) }
    finally { setBusy(false) }
  }

  const downloadUrl = job?.job_id ? `${API}/api/download/${encodeURIComponent(job.job_id)}` : null

  return (
    <div className="nexus-shell">
      <div className="stars" />
      <header className="topbar">
        <div className="brand"><span className="brand-mark">N</span><span>NEXU<span className="cyan">X</span></span><small>NEURAL VIDEO REPURPOSING</small></div>
        <div className="status"><i className={health?.status === 'ok' ? 'live' : ''} /> {health?.status === 'ok' ? 'ENGINE ONLINE' : 'ENGINE OFFLINE'}</div>
      </header>

      <main>
        <section className="hero" id="hero">
          <div className="eyebrow">AUTONOMOUS AI VIDEO INFRASTRUCTURE // 06.3</div>
          <h1>Turn long-form video into <span className="cyan">short-form gravity.</span></h1>
          <p>Fronted UI, canonical NexuX engine. One command center for ingestion, editorial selection, subtitles, reframing and render QA.</p>
        </section>

        <section className="cockpit" id="workspace-console">
          <div className="section-head"><div><span className="label">01 / INGEST</span><h2>Mission Console</h2></div><span className="telemetry">LOCAL-FIRST // API LINK ACTIVE</span></div>
          <div className="ingest-row">
            <input value={url} onChange={e => setUrl(e.target.value)} placeholder="Paste a YouTube URL to initialize the pipeline…" />
            <button className="primary" onClick={launch} disabled={busy || !url.trim()}>{busy ? 'INITIALIZING…' : 'LAUNCH CLIPPER →'}</button>
          </div>

          <div className="control-grid">
            <div className="control-card"><span>DURATION</span><strong>{duration}s</strong><input type="range" min="20" max="60" value={duration} onChange={e => setDuration(Number(e.target.value))} /></div>
            <div className="control-card"><span>ASPECT</span><div className="segmented">{['9:16', '1:1', '16:9'].map(v => <button key={v} className={ratio === v ? 'selected' : ''} onClick={() => setRatio(v)}>{v}</button>)}</div></div>
            <div className="control-card"><span>CLIPS</span><div className="segmented">{[1,3,5].map(v => <button key={v} className={clipCount === v ? 'selected' : ''} onClick={() => setClipCount(v)}>{v}</button>)}</div></div>
          </div>

          <div className="studio" id="subtitle-engine">
            <div><span className="label">02 / EDITORIAL</span><h3>Subtitle Engine</h3></div>
            <div className="preset-grid">{presets.map(([id, name]) => <button key={id} className={preset === id ? 'preset selected' : 'preset'} onClick={() => setPreset(id)}><span>{name}</span><small>LIVE RENDER STYLE</small></button>)}</div>
          </div>

          <div className="toggle-grid">
            <button onClick={() => setAutoZoom(!autoZoom)} className={autoZoom ? 'toggle on' : 'toggle'}><span>Auto Zoom</span><b>{autoZoom ? 'ON' : 'OFF'}</b></button>
            <button onClick={() => setFaceTracking(!faceTracking)} className={faceTracking ? 'toggle on' : 'toggle'}><span>Face Tracking</span><b>{faceTracking ? 'ON' : 'OFF'}</b></button>
            <button onClick={() => setEmoji(!emoji)} className={emoji ? 'toggle on' : 'toggle'}><span>Emoji Layer</span><b>{emoji ? 'ON' : 'OFF'}</b></button>
          </div>
        </section>

        <section className="results" id="capabilities">
          <div className="section-head"><div><span className="label">03 / TELEMETRY</span><h2>{statusLabel}</h2></div><span className="telemetry">{progress}%</span></div>
          <div className="progress"><motion.div animate={{ width: `${progress}%` }} /></div>
          {job && <div className="result-panel">
            <div><span className="muted">JOB ID</span><code>{job.job_id}</code></div>
            <div><span className="muted">STAGE</span><strong>{job.stage || job.status}</strong></div>
            <div><span className="muted">OUTPUT</span>{downloadUrl && job.status === 'completed' ? <a className="download" href={downloadUrl}>DOWNLOAD MP4 ↗</a> : <span className="muted">PIPELINE ACTIVE</span>}</div>
          </div>}
          {error && <div className="error">{error}</div>}
        </section>
      </main>

      <footer><span>NEXUX / FRONTED PRODUCTION UI</span><span>CANONICAL ENGINE PRESERVED</span><span>© 2026</span></footer>
    </div>
  )
}
