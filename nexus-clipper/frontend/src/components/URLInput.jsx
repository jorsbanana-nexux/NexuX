import React, { useEffect, useRef, useState } from 'react'
import { motion } from 'framer-motion'
import { FiLink, FiPlay, FiLoader, FiClipboard, FiX } from 'react-icons/fi'
import { nexuxApi, startJobPolling } from '../api/nexuxApi.js'

const YOUTUBE_HOSTS = new Set(['youtube.com', 'www.youtube.com', 'm.youtube.com', 'youtu.be', 'www.youtu.be'])

export default function URLInput({ url, setUrl, config, setJobStatus }) {
  const [generating, setGenerating] = useState(false)
  const [currentJobId, setCurrentJobId] = useState(null)
  const stopPollingRef = useRef(null)

  const clearPolling = () => {
    stopPollingRef.current?.()
    stopPollingRef.current = null
  }

  useEffect(() => () => clearPolling(), [])

  const isValidUrl = (str) => {
    try {
      const parsed = new URL(str)
      const host = (parsed.hostname || '').toLowerCase().replace(/\.$/, '')
      if (!YOUTUBE_HOSTS.has(host) || parsed.username || parsed.password) return false
      if (host === 'youtu.be' || host === 'www.youtu.be') return Boolean(parsed.pathname.replace(/^\//, ''))
      return parsed.pathname === '/watch' || parsed.pathname.startsWith('/shorts/') || parsed.pathname.startsWith('/live/') || parsed.pathname.startsWith('/embed/')
    } catch {
      return false
    }
  }

  const handlePaste = async () => {
    try { setUrl(await navigator.clipboard.readText()) } catch {}
  }

  const handleGenerate = async () => {
    if (!url.trim() || !isValidUrl(url) || generating) return
    clearPolling()
    setGenerating(true)
    setCurrentJobId(null)
    setJobStatus({ status: 'queued', progress: 0, stage: 'Submitting to NexuX...' })

    try {
      const payload = {
        youtube_url: url.trim(),
        target_duration: Math.max(20, Math.min(60, Number(config.target_duration ?? 45))),
        aspect_ratio: config.aspect_ratio ?? '9:16',
        subtitle_style: config.subtitle_style ?? 'hormozi',
        font: config.font || 'Arial',
        font_size: Math.max(20, Math.min(96, Number(config.font_size ?? 48))),
        primary_color: config.primary_color || '#FFFFFF',
        highlight_color: config.highlight_color || '#FFD700',
        stroke_color: config.stroke_color || '#000000',
        stroke_width: Math.max(1, Math.min(12, Number(config.stroke_width ?? 3))),
        position: ['top', 'center', 'bottom'].includes(config.position) ? config.position : 'center',
        animation: config.animation || 'pop',
        auto_zoom: Boolean(config.auto_zoom ?? true),
        face_tracking: Boolean(config.auto_zoom ?? true),
        clip_count: Math.max(1, Math.min(10, Number(config.clip_count ?? 3))),
        language: config.language || null,
        normalize_audio: true,
        emoji_enabled: Boolean(config.emoji_enabled ?? false),
      }

      const created = await nexuxApi.generate(payload)
      setCurrentJobId(created.job_id)
      setJobStatus(created)
      stopPollingRef.current = startJobPolling(
        created.job_id,
        (job) => setJobStatus(job),
        (job) => {
          setJobStatus(job)
          setGenerating(false)
          setCurrentJobId(null)
          stopPollingRef.current = null
        },
      )
    } catch (error) {
      setJobStatus({ status: 'failed', error: error instanceof Error ? error.message : String(error) })
      setGenerating(false)
      setCurrentJobId(null)
    }
  }

  const handleCancel = async () => {
    if (!currentJobId) return
    const jobId = currentJobId
    clearPolling()
    setGenerating(false)
    setCurrentJobId(null)
    try {
      const result = await nexuxApi.cancel(jobId)
      setJobStatus(prev => ({ ...(prev || {}), ...result, status: 'cancelled', stage: 'Cancelled' }))
    } catch (error) {
      setJobStatus(prev => ({ ...(prev || {}), status: 'failed', error: error instanceof Error ? error.message : String(error) }))
    }
  }

  return (
    <motion.div initial={{ opacity: 0, y: 8 }} animate={{ opacity: 1, y: 0 }} className="glass-card p-5 space-y-4">
      <div className="flex items-center gap-2">
        <FiLink className="text-spacex-accent" size={16} />
        <h3 className="text-sm font-semibold text-gray-200">Video Source</h3>
      </div>

      <div className="glass-capsule flex items-center px-4 py-2 gap-2">
        <input type="url" value={url} onChange={e => setUrl(e.target.value)} onKeyDown={e => e.key === 'Enter' && handleGenerate()} placeholder="Paste YouTube URL here..." className="flex-1 bg-transparent outline-none text-sm text-white placeholder-gray-600 py-1" />
        <button onClick={handlePaste} className="p-1.5 rounded-lg hover:bg-white/5 text-gray-500 hover:text-gray-300 transition-colors" title="Paste from clipboard"><FiClipboard size={14} /></button>
        {url && <span className={`w-2 h-2 rounded-full flex-shrink-0 ${isValidUrl(url) ? 'bg-spacex-success' : 'bg-spacex-danger'}`} />}
      </div>

      <div className="flex gap-2">
        <button onClick={handleGenerate} disabled={generating || !isValidUrl(url)} className="btn-primary flex-1 flex items-center justify-center gap-2">
          {generating ? <><FiLoader className="animate-spin" size={16} />Processing...</> : <><FiPlay size={16} />Generate with NexuX</>}
        </button>
        {generating && currentJobId && <button onClick={handleCancel} className="px-4 rounded-lg border border-red-500/30 text-red-300 hover:bg-red-500/10 transition-colors" title="Cancel current job" aria-label="Cancel current job"><FiX size={16} /></button>}
      </div>

      {!url && <p className="text-[11px] text-gray-600 text-center">Paste a YouTube link to start the canonical NexuX pipeline.</p>}
    </motion.div>
  )
}
