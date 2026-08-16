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
  ['hormozi', 'HORMOZI'], ['mrbeast', 'MRBEAST'], ['minimalist', 'MINIMAL'], ['gaming', 'GAMING'],
  ['cinematic', 'CINEMATIC'], ['neon', 'NEON'], ['karaoke', 'KARAOKE'], ['documentary', 'DOC'],
]
const animations = ['none', 'pop', 'pop_fast', 'fade', 'fade_slow', 'slow_reveal', 'flicker', 'bounce', 'typewriter']
const positions = ['top', 'center', 'bottom']
const ratios = ['9:16', '1:1', '16:9', '4:5', '2:3', '21:9']

export default function App() {
  const [url, setUrl] = useState('')
  const [duration, setDuration] = useState(45)
  const [preset, setPreset] = useState('hormozi')
  const [ratio, setRatio] = useState('9:16')
  const [clipCount, setClipCount] = useState(5)
  const [font, setFont] = useState('Arial')
  const [fontSize, setFontSize] = useState(48)
  const [primaryColor, setPrimaryColor] = useState('#FFFFFF')
  const [highlightColor, setHighlightColor] = useState('#22D3EE')
  const [strokeColor, setStrokeColor] = useState('#000000')
  const [strokeWidth, setStrokeWidth] = useState(3)
  const [position, setPosition] = useState('center')
  const [animation, setAnimation] = useState('bounce')
  const [autoZoom, setAutoZoom] = useState(true)
  const [faceTracking, setFaceTracking] = useState(true)
  const [emoji, setEmoji] = useState(false)
  const [normalizeAudio, setNormalizeAudio] = useState(true)
  const [language, setLanguage] = useState('')
  const [health, setHealth] = useState(null)
  const [job, setJob] = useState(null)
  const [error, setError] = useState('')
  const [busy, setBusy] = useState(false)
  const progress = Math.max(0, Math.min(100, Number(job?.progress || 0)))

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
        subtitle_style: preset, font: font.trim() || 'Arial', font_size: fontSize,
        primary_color: primaryColor.toUpperCase(), highlight_color: highlightColor.toUpperCase(),
        stroke_color: strokeColor.toUpperCase(), stroke_width: strokeWidth,
        position, animation, auto_zoom: autoZoom, face_tracking: faceTracking,
        clip_count: clipCount, language: language.trim() || null,
        normalize_audio: normalizeAudio, emoji_enabled: emoji,
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
          <p>Fronted controls drive the canonical NexuX renderer. Every visible setting is forwarded to the engine as a real render parameter.</p>
        </section>

        <section className="cockpit" id="workspace-console">
          <div className="section-head"><div><span className="label">01 / INGEST</span><h2>Mission Console</h2></div><span className="telemetry">LOCAL-FIRST // API LINK ACTIVE</span></div>
          <div className="ingest-row">
            <input value={url} onChange={e => setUrl(e.target.value)} placeholder="Paste a YouTube URL to initialize the pipeline…" />
            <button className="primary" onClick={launch} disabled={busy || !url.trim()}>{busy ? 'INITIALIZING…' : 'LAUNCH CLIPPER →'}</button>
          </div>

          <div className="control-grid">
            <div className="control-card"><span>DURATION</span><strong>{duration}s</strong><input type="range" min="20" max="60" value={duration} onChange={e => setDuration(Number(e.target.value))} /></div>
            <div className="control-card"><span>ASPECT</span><div className="segmented">{ratios.map(v => <button key={v} className={ratio === v ? 'selected' : ''} onClick={() => setRatio(v)}>{v}</button>)}</div></div>
            <div className="control-card"><span>CLIPS</span><div className="segmented">{Array.from({ length: 10 }, (_, i) => i + 1).map(v => <button key={v} className={clipCount === v ? 'selected' : ''} onClick={() => setClipCount(v)}>{v}</button>)}</div></div>
          </div>

          <div className="studio" id="subtitle-engine">
            <div><span className="label">02 / SUBTITLE</span><h3>Style + Typography</h3></div>
            <div className="preset-grid">{presets.map(([id, name]) => <button key={id} className={preset === id ? 'preset selected' : 'preset'} onClick={() => setPreset(id)}><span>{name}</span><small>ENGINE PRESET</small></button>)}</div>
            <div className="control-grid typography">
              <label className="control-card"><span>FONT</span><input value={font} onChange={e => setFont(e.target.value)} /></label>
              <label className="control-card"><span>SIZE {fontSize}</span><input type="range" min="20" max="96" value={fontSize} onChange={e => setFontSize(Number(e.target.value))} /></label>
              <label className="control-card"><span>STROKE {strokeWidth}</span><input type="range" min="1" max="12" value={strokeWidth} onChange={e => setStrokeWidth(Number(e.target.value))} /></label>
            </div>
            <div className="color-row">
              <label>PRIMARY <input type="color" value={primaryColor} onChange={e => setPrimaryColor(e.target.value)} /></label>
              <label>HIGHLIGHT <input type="color" value={highlightColor} onChange={e => setHighlightColor(e.target.value)} /></label>
              <label>STROKE <input type="color" value={strokeColor} onChange={e => setStrokeColor(e.target.value)} /></label>
            </div>
            <div className="segmented wide">{animations.map(v => <button key={v} className={animation === v ? 'selected' : ''} onClick={() => setAnimation(v)}>{v}</button>)}</div>
            <div className="segmented wide">{positions.map(v => <button key={v} className={position === v ? 'selected' : ''} onClick={() => setPosition(v)}>{v}</button>)}</div>
          </div>

          <div className="toggle-grid">
            <button onClick={() => setAutoZoom(!autoZoom)} className={autoZoom ? 'toggle on' : 'toggle'}><span>Auto Zoom</span><b>{autoZoom ? 'ON' : 'OFF'}</b></button>
            <button onClick={() => setFaceTracking(!faceTracking)} className={faceTracking ? 'toggle on' : 'toggle'}><span>Face Tracking</span><b>{faceTracking ? 'ON' : 'OFF'}</b></button>
            <button onClick={() => setNormalizeAudio(!normalizeAudio)} className={normalizeAudio ? 'toggle on' : 'toggle'}><span>Audio Normalize</span><b>{normalizeAudio ? 'ON' : 'OFF'}</b></button>
            <button onClick={() => setEmoji(!emoji)} className={emoji ? 'toggle on' : 'toggle'}><span>Emoji Layer</span><b>{emoji ? 'ON' : 'OFF'}</b></button>
          </div>
          <div className="control-card language"><span>LANGUAGE (OPTIONAL)</span><input value={language} onChange={e => setLanguage(e.target.value)} placeholder="auto" /></div>
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
      <footer><span>NEXUX / FRONTED PRODUCTION UI</span><span>CONTROL FIDELITY: STRICT</span><span>© 2026</span></footer>
    </div>
  )
}
