import React from 'react'
import { motion } from 'framer-motion'
import { FiCheckCircle, FiAlertCircle, FiLoader } from 'react-icons/fi'

const STAGES = [
  { id: 'downloading',  label: 'Downloading High-Res Source...',      icon: '⬇️' },
  { id: 'downloading',  label: 'Transcribing Audio via Whisper AI...', icon: '🎙️' },
  { id: 'transcribing', label: 'Analyzing Virality Hooks...',          icon: '🔍' },
  { id: 'analyzing',    label: 'Generating Clip Candidates...',        icon: '✨' },
  { id: 'rendering',    label: 'Rendering Final Video...',             icon: '🎬' },
  { id: 'completed',    label: 'Render Complete! 🎉',                  icon: '✅' },
]

export default function ProgressPanel({ jobStatus }) {
  const stages = ['downloading', 'transcribing', 'analyzing', 'rendering', 'completed']
  const isComplete = jobStatus.status === 'completed'
  const isFailed = jobStatus.status === 'failed'
  const isProcessing = !isComplete && !isFailed

  // Map stage to cinematic message
  const stageMessages = {
    queued:        'Initializing pipeline...',
    downloading:   'Downloading high-resolution source video...',
    face_tracking: 'Detecting faces for smart auto-zoom...',
    transcribing:  'Transcribing audio with Whisper AI...',
    analyzing:     'Analyzing virality hooks & narrative structure...',
    rendering:     'Burning in animated captions & effects...',
    completed:     'Your viral clip is ready! 🚀',
  }

  const currentMsg = stageMessages[jobStatus.stage] || `${jobStatus.stage}...`

  return (
    <motion.div
      initial={{ opacity: 0, y: 10 }}
      animate={{ opacity: 1, y: 0 }}
      className="glass-card p-5 space-y-4"
    >
      {/* Status header */}
      <div className="flex items-center gap-2">
        {isComplete ? (
          <FiCheckCircle className="text-spacex-success" size={18} />
        ) : isFailed ? (
          <FiAlertCircle className="text-spacex-danger" size={18} />
        ) : (
          <motion.div
            animate={{ rotate: 360 }}
            transition={{ duration: 2, repeat: Infinity, ease: 'linear' }}
          >
            <FiLoader className="text-spacex-accent" size={18} />
          </motion.div>
        )}
        <h3 className="text-sm font-semibold text-gray-200">
          {isComplete ? 'Complete!' : isFailed ? 'Failed' : 'Processing'}
        </h3>
        <span className="text-[11px] text-gray-600 ml-auto font-mono">
          {jobStatus.job_id || ''}
        </span>
      </div>

      {/* Progress bar */}
      <div className="w-full bg-white/5 rounded-full h-2 overflow-hidden">
        <motion.div
          className={`h-full rounded-full ${
            isFailed ? 'bg-spacex-danger' :
            isComplete ? 'bg-spacex-success' :
            'bg-gradient-to-r from-spacex-accent to-spacex-cyan'
          }`}
          initial={{ width: 0 }}
          animate={{
            width: `${jobStatus.progress}%`,
            boxShadow: isProcessing ? '0 0 12px rgba(204,255,0,0.4)' : 'none',
          }}
          transition={{ duration: 0.6, ease: 'easeOut' }}
        />
      </div>

      {/* Percentage + message */}
      <div className="flex items-center justify-between">
        <span className={`text-lg font-bold font-mono ${
          isComplete ? 'text-spacex-success' :
          isFailed ? 'text-spacex-danger' :
          'text-spacex-accent'
        }`}>
          {jobStatus.progress}%
        </span>
        <motion.span
          key={currentMsg}
          initial={{ opacity: 0, y: 4 }}
          animate={{ opacity: 1, y: 0 }}
          className="text-[12px] text-gray-500"
        >
          {currentMsg}
        </motion.span>
      </div>

      {/* Pipeline stages */}
      <div className="flex justify-between items-center pt-1">
        {stages.map((stage, i) => {
          const stageIdx = stages.indexOf(jobStatus.stage)
          const isDone = i < stageIdx || isComplete
          const isCurrent = i === stageIdx && !isComplete && !isFailed
          const stageInfo = {
            downloading:  { label: 'Download', icon: '⬇️' },
            transcribing: { label: 'Transcribe', icon: '🎙️' },
            analyzing:    { label: 'Analyze', icon: '🔍' },
            rendering:    { label: 'Render', icon: '🎬' },
            completed:    { label: 'Done', icon: '✅' },
          }[stage]

          return (
            <React.Fragment key={stage}>
              {i > 0 && (
                <div className={`flex-1 h-px mx-1 ${
                  isDone || isCurrent ? 'bg-spacex-success/40' : 'bg-white/5'
                }`} />
              )}
              <div className="flex flex-col items-center gap-1">
                <motion.div
                  animate={isCurrent ? { scale: [1, 1.15, 1] } : {}}
                  transition={{ duration: 1.5, repeat: Infinity }}
                  className={`w-8 h-8 rounded-full flex items-center justify-center text-xs font-bold ${
                    isDone ? 'bg-spacex-success/15 text-spacex-success border border-spacex-success/30' :
                    isCurrent ? 'bg-spacex-accent/15 text-spacex-accent border border-spacex-accent/40 shadow-[0_0_10px_rgba(204,255,0,0.3)]' :
                    'bg-white/5 text-gray-700 border border-white/5'
                  }`}
                >
                  {isDone ? '✓' : stageInfo.icon}
                </motion.div>
                <span className={`text-[9px] ${
                  isDone ? 'text-spacex-success/60' :
                  isCurrent ? 'text-spacex-accent/80' :
                  'text-gray-700'
                }`}>
                  {stageInfo.label}
                </span>
              </div>
            </React.Fragment>
          )
        })}
      </div>

      {/* Error message */}
      {isFailed && (
        <motion.div
          initial={{ opacity: 0 }}
          animate={{ opacity: 1 }}
          className="p-3 rounded-xl bg-spacex-danger/5 border border-spacex-danger/20"
        >
          <p className="text-xs text-spacex-danger">{jobStatus.error}</p>
        </motion.div>
      )}
    </motion.div>
  )
}
