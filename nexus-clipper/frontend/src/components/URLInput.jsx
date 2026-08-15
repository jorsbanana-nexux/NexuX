import React, { useEffect, useRef, useState } from 'react'
import { motion } from 'framer-motion'
import { FiLink, FiPlay, FiLoader, FiClipboard, FiX } from 'react-icons/fi'

const TERMINAL_STATUSES = new Set(['completed', 'failed', 'cancelled'])
const POLL_INTERVAL_MS = 1000

const YOUTUBE_HOSTS = new Set(['youtube.com', 'www.youtube.com', 'm.youtube.com', 'youtu.be', 'www.youtu.be'])

export default function URLInput({ url, setUrl, config, setJobStatus }) {
  const [generating, setGenerating] = useState(false)
  const [currentJobId, setCurrentJobId] = useState(null)
  const pollRef = useRef(null)
  const abortRef = useRef(null)

  const clearPolling = () => {
    if (pollRef.current) {
      clearInterval(pollRef.current)
      pollRef.current = null
    }
    if (abortRef.current) {
      abortRef.current.abort()
      abortRef.current = null
    }
  }

  useEffect(() => () => clearPolling(), [])

  const isValidUrl = (str) => {
    try {
      const parsed = new URL(str)
      const host = (parsed.hostname || '').toLowerCase().replace(/\.$/, '')
      if (!YOUTUBE_HOSTS.has(host)) return false
      if (parsed.username || parsed.password) return false
      if (host === 'youtu.be' || host === 'www.youtu.be') return Boolean(parsed.pathname.replace(/^\//, ''))
      return parsed.pathname === '/watch' || parsed.pathname.startsWith('/shorts/') || parsed.pathname.startsWith('/live/') || parsed.pathname.startsWith('/embed/')
    } catch {
      return false
    }
  }

  const handlePaste = async () => {
    try {
      const text = await navigator.clipboard.readText()
      setUrl(text)
    } catch {}
  }

  const pollJob = (jobId) => {
    clearPolling()

    const poll = async () => {
      const controller = new AbortController()
      abortRef.current = controller
      try {
        const jRes = await fetch(`/api/job/${jobId}`, { signal: controller.signal })
        if (!jRes.ok) throw new Error(`Job status request failed (${jRes.status})`)

        const job = await jRes.json()
        setJobStatus(job)

        if (TERMINAL_STATUSES.has(job.status)) {
          clearPolling()
          setGenerating(false)
          setCurrentJobId(null)
        }
      } catch (error) {
        if (error?.name === 'AbortError') return
        clearPolling()
        setGenerating(false)
        setCurrentJobId(null)
        setJobStatus({ status: 'failed', error: 'Lost connection to backend' })
      } finally {
        if (abortRef.current === controller) abortRef.current = null
      }
    }

    void poll()
    pollRef.current = setInterval(poll, POLL_INTERVAL_MS)
  }

  const handleGenerate = async () => {
    if (!url.trim() || !isValidUrl(url) || generating) return

    clearPolling()
    setGenerating(true)
    setCurrentJobId(null)
    setJobStatus({ status: 'queued', progress: 0, stage: 'Starting...' })

    try {
      const res = await fetch('/api/generate', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ youtube_url: url, ...config }),
      })

      if (!res.ok) {
        const err = await res.text()
        throw new Error(err)
      }

      const { job_id } = await res.json()
      setCurrentJobId(job_id)
      pollJob(job_id)
    } catch (e) {
      setJobStatus({ status: 'failed', error: e.message })
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
    setJobStatus(prev => ({ ...(prev || {}), status: 'cancelled', stage: 'Cancelled' }))

    try {
      const res = await fetch(`/api/job/${jobId}`, { method: 'DELETE' })
      if (!res.ok && res.status !== 404) throw new Error(`Cancellation failed (${res.status})`)
    } catch (error) {
      setJobStatus(prev => ({ ...(prev || {}), status: 'failed', error: error.message }))
    }
  }

  return (
    <motion.div
      initial={{ opacity: 0, y: 8 }}
      animate={{ opacity: 1, y: 0 }}
      className="glass-card p-5 space-y-4"
    >
      <div className="flex items-center gap-2">
        <FiLink className="text-spacex-accent" size={16} />
        <h3 className="text-sm font-semibold text-gray-200">Video Source</h3>
      </div>

      <div className="glass-capsule flex items-center px-4 py-2 gap-2">
        <input
          type="url"
          value={url}
          onChange={e => setUrl(e.target.value)}
          onKeyDown={e => e.key === 'Enter' && handleGenerate()}
          placeholder="Paste YouTube URL here..."
          className="flex-1 bg-transparent outline-none text-sm text-white placeholder-gray-600 py-1"
        />
        <button
          onClick={handlePaste}
          className="p-1.5 rounded-lg hover:bg-white/5 text-gray-500 hover:text-gray-300 transition-colors"
          title="Paste from clipboard"
        >
          <FiClipboard size={14} />
        </button>
        {url && (
          <span className={`w-2 h-2 rounded-full flex-shrink-0 ${isValidUrl(url) ? 'bg-spacex-success' : 'bg-spacex-danger'}`} />
        )}
      </div>

      <div className="flex gap-2">
        <button
          onClick={handleGenerate}
          disabled={generating || !isValidUrl(url)}
          className="btn-primary flex-1 flex items-center justify-center gap-2"
        >
          {generating ? <><FiLoader className="animate-spin" size={16} />Processing...</> : <><FiPlay size={16} />Get Clips</>}
        </button>

        {generating && currentJobId && (
          <button
            onClick={handleCancel}
            className="px-4 rounded-lg border border-red-500/30 text-red-300 hover:bg-red-500/10 transition-colors"
            title="Cancel current job"
            aria-label="Cancel current job"
          >
            <FiX size={16} />
          </button>
        )}
      </div>

      {!url && (
        <p className="text-[11px] text-gray-600 text-center">Paste link YouTube untuk mulai generate klip viral</p>
      )}
    </motion.div>
  )
}
