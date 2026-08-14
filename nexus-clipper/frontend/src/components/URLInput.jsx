import React, { useState } from 'react'
import { motion } from 'framer-motion'
import { FiLink, FiPlay, FiLoader, FiClipboard } from 'react-icons/fi'

export default function URLInput({ url, setUrl, config, setJobStatus }) {
  const [generating, setGenerating] = useState(false)

  const isValidUrl = (str) => {
    try { new URL(str); return true } catch { return false }
  }

  const handlePaste = async () => {
    try {
      const text = await navigator.clipboard.readText()
      setUrl(text)
    } catch {}
  }

  const handleGenerate = async () => {
    if (!url.trim() || !isValidUrl(url)) return
    setGenerating(true)
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

      // Poll job status
      const poll = setInterval(async () => {
        try {
          const jRes = await fetch(`/api/job/${job_id}`)
          const job = await jRes.json()
          setJobStatus(job)
          if (job.status === 'completed' || job.status === 'failed') {
            clearInterval(poll)
            setGenerating(false)
          }
        } catch {
          clearInterval(poll)
          setGenerating(false)
          setJobStatus({ status: 'failed', error: 'Lost connection to backend' })
        }
      }, 1000)
    } catch (e) {
      setJobStatus({ status: 'failed', error: e.message })
      setGenerating(false)
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

      {/* URL Input Capsule */}
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
          <span
            className={`w-2 h-2 rounded-full flex-shrink-0 ${
              isValidUrl(url) ? 'bg-spacex-success' : 'bg-spacex-danger'
            }`}
          />
        )}
      </div>

      {/* Generate Button */}
      <button
        onClick={handleGenerate}
        disabled={generating || !isValidUrl(url)}
        className="btn-primary w-full flex items-center justify-center gap-2"
      >
        {generating ? (
          <>
            <FiLoader className="animate-spin" size={16} />
            Processing...
          </>
        ) : (
          <>
            <FiPlay size={16} />
            Get Clips
          </>
        )}
      </button>

      {!url && (
        <p className="text-[11px] text-gray-600 text-center">
          Paste link YouTube untuk mulai generate klip viral
        </p>
      )}
    </motion.div>
  )
}
