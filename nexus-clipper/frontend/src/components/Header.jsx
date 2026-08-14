import React from 'react'
import { motion } from 'framer-motion'

export default function Header({ jobStatus }) {
  return (
    <motion.header
      initial={{ opacity: 0, y: -10 }}
      animate={{ opacity: 1, y: 0 }}
      className="flex items-center justify-between py-2"
    >
      {/* Logo */}
      <div className="flex items-center gap-3">
        <motion.div
          whileHover={{ rotate: 10 }}
          className="w-9 h-9 rounded-xl bg-gradient-to-br from-spacex-accent to-spacex-cyan flex items-center justify-center shadow-lg shadow-spacex-accent/20"
        >
          <span className="text-black font-black text-sm">NC</span>
        </motion.div>
        <div>
          <h1 className="text-lg font-bold text-white tracking-tight">
            Nexus<span className="text-spacex-accent">Clipper</span>
          </h1>
          <p className="text-[10px] text-gray-600 tracking-wide">AI ULTRA v2.0</p>
        </div>
      </div>

      {/* Status badge */}
      {jobStatus && (
        <motion.div
          initial={{ opacity: 0, scale: 0.9 }}
          animate={{ opacity: 1, scale: 1 }}
          className="flex items-center gap-2"
        >
          <div className={`
            px-3 py-1.5 rounded-full text-xs font-semibold border
            ${jobStatus.status === 'completed'
              ? 'bg-spacex-success/10 text-spacex-success border-spacex-success/20'
              : jobStatus.status === 'failed'
              ? 'bg-spacex-danger/10 text-spacex-danger border-spacex-danger/20'
              : jobStatus.status === 'queued'
              ? 'bg-spacex-accent/10 text-spacex-accent border-spacex-accent/20'
              : 'bg-spacex-cyan/10 text-spacex-cyan border-spacex-cyan/20'
            }
          `}>
            {jobStatus.status === 'completed' ? '✓ Ready' :
             jobStatus.status === 'failed' ? '✗ Error' :
             jobStatus.status === 'queued' ? '⏳ Queued' :
             '⚙ Processing'}
          </div>
        </motion.div>
      )}
    </motion.header>
  )
}
