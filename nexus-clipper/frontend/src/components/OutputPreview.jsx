import React from 'react'
import { motion } from 'framer-motion'
import { FiDownload, FiShare2, FiRefreshCw } from 'react-icons/fi'

export default function OutputPreview({ outputPath, onViewClips, onCustomize }) {
  const videoUrl = outputPath.startsWith('http')
    ? outputPath
    : `/output/${outputPath.replace(/\\/g, '/').split('/output/').pop()}`

  const handleDownload = () => {
    const a = document.createElement('a')
    a.href = videoUrl
    a.download = 'nexus-clip.mp4'
    document.body.appendChild(a)
    a.click()
    document.body.removeChild(a)
  }

  return (
    <motion.div
      initial={{ opacity: 0, y: 20 }}
      animate={{ opacity: 1, y: 0 }}
      className="glass-card p-5 space-y-4"
    >
      {/* Title */}
      <div className="flex items-center gap-2">
        <span className="badge badge-success">✓ Complete</span>
        <h3 className="text-sm font-semibold text-gray-200">Your Viral Clip</h3>
        <span className="text-[11px] text-gray-600 ml-auto">Ready to download</span>
      </div>

      {/* Video player */}
      <div className="relative rounded-xl overflow-hidden border border-white/5 bg-black">
        <video
          src={videoUrl}
          controls
          className="w-full max-h-[400px] object-contain"
          poster=""
        >
          Your browser does not support the video tag.
        </video>
      </div>

      {/* Action buttons */}
      <div className="flex gap-3">
        <motion.button
          whileHover={{ scale: 1.02 }}
          whileTap={{ scale: 0.98 }}
          onClick={handleDownload}
          className="btn-primary flex-1 flex items-center justify-center gap-2 animate-pulse-glow"
        >
          <FiDownload size={18} />
          Download MP4
        </motion.button>
        {onViewClips && (
          <button
            onClick={onViewClips}
            className="btn-secondary flex items-center gap-2"
          >
            🎬 All Clips
          </button>
        )}
        <button
          onClick={() => window.location.reload()}
          className="btn-secondary flex items-center gap-2"
        >
          <FiRefreshCw size={16} />
          New
        </button>
      </div>
    </motion.div>
  )
}
