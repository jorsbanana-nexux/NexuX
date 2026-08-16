import React, { useEffect, useMemo, useState } from 'react'
import { motion } from 'framer-motion'

const API = String(import.meta.env.VITE_NEXUX_API_URL || '').replace(/\/$/, '')
const api = (path) => `${API}${path}`

const PRESETS = [
  ['hormozi', 'Hormozi'], ['mrbeast', 'MrBeast'], ['minimal-aesthetic', 'Minimal Aesthetic'],
  ['gamer-comic', 'Gamer Comic'], ['neon-cyberpunk', 'Neon Cyberpunk'], ['aliabdaal', 'Ali Abdaal'],
  ['iman-gadzhi', 'Iman Gadzhi'], ['anime-impact', 'Anime Impact'],
]
const ANIMATIONS = [
  ['word-by-word', 'Word by word'], ['line-by-line', 'Line by line'], ['bounce-zoom', 'Bounce zoom'],
  ['typewriter-glitch', 'Typewriter glitch'], ['kinetic-slide', 'Kinetic slide'], ['pulse-glow', 'Pulse glow'],
  ['flip-rotate', 'Flip rotate'], ['fade-drift', 'Fade drift'],
]
const ASPECTS = ['9:16', '1:1', '16:9', '4:5', '2:3', '21:9']

export default function FrontedApp() {
  const [url, setUrl] = useState('')
  const [job, setJob] = useState(null)
  const [section, setSection] = useState('workspace')
  const [health, setHealth] = useState(null)
  const [busy, setBusy] = useState(false)
  const [config, setConfig] = useState({
    subtitle_style: 'hormozi', animation: 'word-by-word', position: 'bottom',
    font: 'Arial', font_size: 58, primary_color: '#FFFFFF', highlight_color: '#FACC15',
    stroke_color: '#000000', stroke_width: 4, auto_zoom: true, face_tracking: true,
    aspect_ratio: '9:16', clip_count: 5, target_duration: 45, language: null,
    normalize_audio: true, emoji_enabled: true,
  })

  useEffect(() => {
    fetch(api('/api/health')).then(r => r.json()).then(setHealth).catch(() => setHealth({ status: 'offline' }))
  }, [])

  useEffect(() => {
    if (!job?.job_id || ['completed', 'failed', 'cancelled'].includes(job.status)) return undefined
    const timer = setInterval(async () => {
      try {
        const res = await fetch(api(`/api/job/${job.job_id}`))
        if (res.ok) setJob(await res.json())
      } catch {}
    }, 1000)
    return () => clearInterval(timer)
  }, [job?.job_id, job?.status])

  const set = (key, value) => setConfig(prev => ({ ...prev, [key]: value }))
  const canGenerate = url.trim().length > 10 && !busy
  const progress = Math.max(0, Math.min(100, Number(job?.progress || 0)))
  const outputUrl = job?.output_path ? api(job.output_path) : null

  const generate = async () => {
    if (!canGenerate) return
    setBusy(true)
    setJob({ status: 'queued', progress: 0, stage: 'queued' })
    try {
      const response = await fetch(api('/api/generate'), {
        method: 'POST', headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ youtube_url: url.trim(), ...config }),
      })
      const body = await response.json()
      if (!response.ok) throw new Error(body?.detail || 'Generation request failed')
      setJob(body)
    } catch (error) {
      setJob({ status: 'failed', error: error.message })
    } finally {
      setBusy(false)
    }
  }

  const cancel = async () => {
    if (!job?.job_id) return
    await fetch(api(`/api/job/${job.job_id}`), { method: 'DELETE' }).catch(() => {})
    setJob(prev => ({ ...(prev || {}), status: 'cancelled', stage: 'cancelled' }))
  }

  const statusLabel = useMemo(() => {
    if (!job) return health?.status === 'ok' ? 'ENGINE ONLINE' : 'ENGINE OFFLINE'
    if (job.status === 'completed') return 'CLIPS READY'
    if (job.status === 'failed') return 'GENERATION FAILED'
    if (job.status === 'cancelled') return 'CANCELLED'
    return String(job.stage || job.status || 'PROCESSING').toUpperCase()
  }, [health, job])

  return (
    <div className="min-h-screen bg-[#02040a] text-white overflow-x-hidden">
      <div className="fixed inset-0 pointer-events-none bg-[radial-gradient(circle_at_50%_0%,rgba(34,211,238,.18),transparent_40%),radial-gradient(circle_at_90%_80%,rgba(168,85,247,.14),transparent_35%)]" />
      <div className="fixed inset-0 pointer-events-none opacity-[.025] bg-[linear-gradient(rgba(255,255,255,.5)_1px,transparent_1px),linear-gradient(90deg,rgba(255,255,255,.5)_1px,transparent_1px)] bg-[size:32px_32px]" />

      <header className="relative z-20 sticky top-0 border-b border-white/10 bg-black/55 backdrop-blur-2xl">
        <div className="max-w-7xl mx-auto px-4 py-4 flex items-center justify-between gap-4">
          <div className="flex items-center gap-3">
            <div className="w-10 h-10 rounded-xl border border-cyan-400/40 bg-cyan-400/10 grid place-items-center font-black text-cyan-300">NX</div>
            <div><div className="font-black tracking-[.25em]">NEXUX</div><div className="text-[10px] font-mono text-stone-500 tracking-widest">FRONTED PRODUCTION</div></div>
          </div>
          <div className="flex items-center gap-2 text-[10px] font-mono">
            <span className={`w-2 h-2 rounded-full ${health?.status === 'ok' ? 'bg-emerald-400' : 'bg-red-400'}`} />
            <span>{statusLabel}</span>
          </div>
        </div>
      </header>

      <main className="relative z-10 max-w-7xl mx-auto px-4 py-8">
        <section className="max-w-4xl mb-8">
          <div className="text-xs font-mono tracking-[.4em] text-cyan-300/70 mb-3">AUTONOMOUS VIDEO REPURPOSING</div>
          <h1 className="text-4xl md:text-7xl font-black leading-[.95]">Long video in.<br/><span className="text-cyan-300">Publish-ready clips out.</span></h1>
          <p className="text-stone-400 mt-5 max-w-2xl">The controls below are direct instructions to the NexuX engine. Every choice is rendered into the final video.</p>
        </section>

        <div className="grid xl:grid-cols-[1.1fr_.9fr] gap-5">
          <section className="rounded-3xl border border-white/10 bg-white/[.035] backdrop-blur-xl p-5 md:p-7">
            <div className="flex gap-2 mb-6">
              {['workspace', 'subtitles', 'visual', 'export'].map(id => (
                <button key={id} onClick={() => setSection(id)} className={`px-4 py-2 rounded-xl text-xs font-mono border ${section===id?'border-cyan-300/50 bg-cyan-300/10 text-cyan-200':'border-white/10 text-stone-400'}`}>{id}</button>
              ))}
            </div>

            {section === 'workspace' && <div className="space-y-5">
              <label className="block text-xs font-mono text-stone-400">SOURCE VIDEO</label>
              <div className="flex gap-2">
                <input value={url} onChange={e => setUrl(e.target.value)} placeholder="Paste YouTube URL…" className="flex-1 rounded-2xl border border-white/10 bg-black/40 px-4 py-4 outline-none focus:border-cyan-300/50" />
                <button onClick={generate} disabled={!canGenerate} className="rounded-2xl px-6 bg-cyan-300 text-black font-black disabled:opacity-30">Generate</button>
              </div>
              <div className="grid md:grid-cols-3 gap-3">
                <Field label="CLIPS"><input type="number" min="1" max="10" value={config.clip_count} onChange={e => set('clip_count', Number(e.target.value))}/></Field>
                <Field label="TARGET SECONDS"><input type="number" min="20" max="60" value={config.target_duration} onChange={e => set('target_duration', Number(e.target.value))}/></Field>
                <Field label="ASPECT"><select value={config.aspect_ratio} onChange={e => set('aspect_ratio', e.target.value)}>{ASPECTS.map(x => <option key={x}>{x}</option>)}</select></Field>
              </div>
            </div>}

            {section === 'subtitles' && <div className="space-y-5">
              <Field label="VISUAL PRESET"><select value={config.subtitle_style} onChange={e => set('subtitle_style', e.target.value)}>{PRESETS.map(([id,name]) => <option key={id} value={id}>{name}</option>)}</select></Field>
              <div className="grid md:grid-cols-2 gap-3">
                <Field label="ANIMATION"><select value={config.animation} onChange={e => set('animation', e.target.value)}>{ANIMATIONS.map(([id,name]) => <option key={id} value={id}>{name}</option>)}</select></Field>
                <Field label="POSITION"><select value={config.position} onChange={e => set('position', e.target.value)}>{['top','center','bottom'].map(x => <option key={x}>{x}</option>)}</select></Field>
              </div>
              <div className="grid md:grid-cols-3 gap-3">
                <Field label="FONT"><input value={config.font} onChange={e => set('font', e.target.value)}/></Field>
                <Field label="SIZE"><input type="number" min="20" max="96" value={config.font_size} onChange={e => set('font_size', Number(e.target.value))}/></Field>
                <Field label="STROKE"><input type="number" min="1" max="12" value={config.stroke_width} onChange={e => set('stroke_width', Number(e.target.value))}/></Field>
              </div>
            </div>}

            {section === 'visual' && <div className="space-y-5">
              <div className="grid md:grid-cols-2 gap-3">
                <Field label="PRIMARY"><input type="color" value={config.primary_color} onChange={e => set('primary_color', e.target.value)}/></Field>
                <Field label="HIGHLIGHT"><input type="color" value={config.highlight_color} onChange={e => set('highlight_color', e.target.value)}/></Field>
                <Field label="STROKE COLOR"><input type="color" value={config.stroke_color} onChange={e => set('stroke_color', e.target.value)}/></Field>
                <Toggle label="AUTO ZOOM" value={config.auto_zoom} onChange={v => set('auto_zoom', v)} />
                <Toggle label="FACE TRACKING" value={config.face_tracking} onChange={v => set('face_tracking', v)} />
                <Toggle label="NORMALIZE AUDIO" value={config.normalize_audio} onChange={v => set('normalize_audio', v)} />
              </div>
            </div>}

            {section === 'export' && <div className="space-y-5">
              <div className="grid md:grid-cols-2 gap-3">
                <Field label="LANGUAGE"><input placeholder="auto" value={config.language || ''} onChange={e => set('language', e.target.value || null)}/></Field>
                <Toggle label="EMOJI METADATA" value={config.emoji_enabled} onChange={v => set('emoji_enabled', v)} />
              </div>
              <div className="rounded-2xl border border-white/10 bg-black/30 p-5 text-sm text-stone-400">NexuX applies render QA and A/V sync validation before a job can be marked complete.</div>
            </div>}

            {job && <div className="mt-7 rounded-2xl border border-white/10 bg-black/35 p-5">
              <div className="flex items-center justify-between text-xs font-mono mb-3"><span>{String(job.stage || job.status).toUpperCase()}</span><span>{Math.round(progress)}%</span></div>
              <div className="h-2 rounded-full bg-white/10 overflow-hidden"><motion.div animate={{ width: `${progress}%` }} className="h-full bg-cyan-300" /></div>
              {job.error && <div className="mt-3 text-sm text-red-300">{job.error}</div>}
              {!['completed','failed','cancelled'].includes(job.status) && job.job_id && <button onClick={cancel} className="mt-4 text-xs font-mono border border-red-400/30 text-red-300 rounded-xl px-3 py-2">Cancel job</button>}
            </div>}
          </section>

          <aside className="rounded-3xl border border-white/10 bg-black/35 backdrop-blur-xl p-5 md:p-7 min-h-[560px]">
            <div className="text-xs font-mono tracking-[.35em] text-stone-500 mb-4">OUTPUT PREVIEW</div>
            {outputUrl ? <div className="space-y-4">
              <div className="rounded-2xl overflow-hidden bg-black border border-white/10"><video src={outputUrl} controls className="w-full aspect-[9/16] object-contain bg-black" /></div>
              <a href={api(`/api/download/${job.job_id}`)} className="block text-center rounded-2xl py-3 bg-white text-black font-black">Download MP4</a>
              <div className="text-[11px] font-mono text-stone-500">{job.clips?.length || 0} clip(s) generated • Render QA passed</div>
            </div> : <div className="h-full min-h-[480px] rounded-2xl border border-dashed border-white/10 grid place-items-center text-center text-stone-500"><div><div className="text-5xl mb-4">✦</div><div className="font-mono text-xs tracking-widest">WAITING FOR SOURCE</div><div className="text-sm mt-2">Your finished clip will appear here.</div></div></div>}
          </aside>
        </div>
      </main>
    </div>
  )
}

function Field({ label, children }) {
  return <label className="block"><div className="text-[10px] font-mono tracking-[.2em] text-stone-500 mb-2">{label}</div><div className="rounded-xl border border-white/10 bg-black/35 px-3 py-2 [&>input]:w-full [&>input]:bg-transparent [&>input]:outline-none [&>select]:w-full [&>select]:bg-transparent [&>select]:outline-none">{children}</div></label>
}
function Toggle({ label, value, onChange }) {
  return <button type="button" onClick={() => onChange(!value)} className="w-full rounded-xl border border-white/10 bg-black/35 px-3 py-3 text-left"><div className="text-[10px] font-mono text-stone-500">{label}</div><div className={`mt-2 text-sm font-bold ${value?'text-emerald-300':'text-stone-500'}`}>{value?'ENABLED':'DISABLED'}</div></button>
}
