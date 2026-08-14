import React, { useState } from 'react'
import { motion, AnimatePresence } from 'framer-motion'
import { 
  FiPlay, FiDownload, FiEdit3, FiCheckSquare, FiSquare,
  FiZap, FiTrendingUp
} from 'react-icons/fi'
import { SiTiktok, SiInstagram, SiYoutube } from 'react-icons/si'

// ─── Viral Score Badge ───
function ViralBadge({ score }) {
  const getColor = (s) => {
    if (s >= 95) return { bg: 'bg-spacex-accent/15', text: 'text-spacex-accent', border: 'border-spacex-accent/30', glow: 'shadow-[0_0_15px_rgba(204,255,0,0.3)]' }
    if (s >= 85) return { bg: 'bg-spacex-cyan/15', text: 'text-spacex-cyan', border: 'border-spacex-cyan/30', glow: 'shadow-[0_0_10px_rgba(0,240,255,0.3)]' }
    if (s >= 70) return { bg: 'bg-spacex-purple/15', text: 'text-spacex-purple', border: 'border-spacex-purple/30', glow: '' }
    return { bg: 'bg-white/5', text: 'text-gray-400', border: 'border-white/10', glow: '' }
  }
  const c = getColor(score)
  return (
    <div className={`badge inline-flex items-center gap-1 px-3 py-1.5 rounded-full text-xs font-bold ${c.bg} ${c.text} ${c.border} ${c.glow}`}>
      <FiZap size={12} />
      {score} SCORE
    </div>
  )
}

// ─── Platform Badge ───
function PlatformBadge({ platform }) {
  const icons = {
    tiktok:  <SiTiktok size={12} />,
    reels:   <SiInstagram size={12} />,
    shorts:  <SiYoutube size={12} />,
  }
  const labels = { tiktok: 'TikTok', reels: 'Reels', shorts: 'Shorts' }
  const colors = {
    tiktok:  'bg-pink-500/10 text-pink-400 border-pink-500/20',
    reels:   'bg-purple-500/10 text-purple-400 border-purple-500/20',
    shorts:  'bg-red-500/10 text-red-400 border-red-500/20',
  }
  return (
    <span className={`inline-flex items-center gap-1 px-2 py-0.5 rounded-full text-[10px] font-medium border ${colors[platform]}`}>
      {icons[platform]} {labels[platform]}
    </span>
  )
}

// ─── Clip Card ───
function ClipCard({ clip, index, isSelected, onSelect, onCustomize }) {
  const [isHovering, setIsHovering] = useState(false)

  return (
    <motion.div
      initial={{ opacity: 0, y: 20 }}
      animate={{ opacity: 1, y: 0 }}
      transition={{ delay: index * 0.06 }}
      onMouseEnter={() => setIsHovering(true)}
      onMouseLeave={() => setIsHovering(false)}
      className={`group relative glass-card overflow-hidden transition-all duration-300 ${
        isSelected ? 'ring-2 ring-spacex-accent ring-offset-2 ring-offset-[#07080B]' : ''
      }`}
    >
      {/* Selection checkbox */}
      <div className="absolute top-3 left-3 z-20">
        <button
          onClick={(e) => { e.stopPropagation(); onSelect(clip.id) }}
          className={`w-6 h-6 rounded-md flex items-center justify-center transition-all ${
            isSelected 
              ? 'bg-spacex-accent text-black' 
              : 'bg-black/40 text-white/0 group-hover:text-white/50 border border-white/20'
          }`}
        >
          {isSelected ? <FiCheckSquare size={14} /> : <FiSquare size={14} />}
        </button>
      </div>

      {/* Thumbnail */}
      <div className="relative aspect-[9/16] bg-gradient-to-br from-white/5 to-white/[0.02] overflow-hidden">
        {/* Placeholder thumbnail */}
        <div className="absolute inset-0 flex items-center justify-center">
          <div className="text-center">
            <span className="text-5xl opacity-10">
              {['🎙️','🎬','🔥','💡','🎯','⚡','🌟','💎','🎪','🎤'][index]}
            </span>
          </div>
        </div>

        {/* Hover play overlay */}
        <AnimatePresence>
          {isHovering && (
            <motion.div
              initial={{ opacity: 0 }}
              animate={{ opacity: 1 }}
              exit={{ opacity: 0 }}
              className="absolute inset-0 bg-black/60 flex items-center justify-center"
            >
              <motion.div
                whileHover={{ scale: 1.1 }}
                className="w-14 h-14 rounded-full bg-spacex-accent/90 flex items-center justify-center cursor-pointer shadow-[0_0_30px_rgba(204,255,0,0.4)]"
              >
                <FiPlay className="text-black ml-0.5" size={22} />
              </motion.div>
            </motion.div>
          )}
        </AnimatePresence>

        {/* Viral score — top right */}
        <div className="absolute top-3 right-3 z-10">
          <ViralBadge score={clip.score} />
        </div>

        {/* Duration */}
        <div className="absolute bottom-3 left-3 z-10">
          <span className="bg-black/70 text-white text-[10px] px-2 py-0.5 rounded font-mono">
            {clip.duration || '0:30'}
          </span>
        </div>
      </div>

      {/* Card body */}
      <div className="p-4 space-y-3">
        {/* AI Hook Title */}
        <h4 className="text-sm font-semibold text-white leading-tight line-clamp-2">
          {clip.title || 'Untitled Clip'}
        </h4>

        {/* Platform badges */}
        <div className="flex gap-1.5 flex-wrap">
          {clip.platforms?.map(p => (
            <PlatformBadge key={p} platform={p} />
          )) || (
            <>
              <PlatformBadge platform="tiktok" />
              <PlatformBadge platform="reels" />
              <PlatformBadge platform="shorts" />
            </>
          )}
        </div>

        {/* Action buttons */}
        <div className="flex gap-2">
          <button className="btn-primary flex-1 py-2 text-xs flex items-center justify-center gap-1.5">
            <FiDownload size={12} />
            Quick Export
          </button>
          <button
            onClick={() => onCustomize(clip)}
            className="btn-secondary flex-1 py-2 text-xs flex items-center justify-center gap-1.5"
          >
            <FiEdit3 size={12} />
            Edit
          </button>
        </div>
      </div>
    </motion.div>
  )
}

// ─── MAIN DASHBOARD ───
export default function ClipsDashboard({ clips = [], onCustomize, onClose }) {
  const [selected, setSelected] = useState(new Set())
  const [selectAll, setSelectAll] = useState(false)

  // Generate dummy clips if none provided
  const displayClips = clips.length > 0 ? clips : Array.from({ length: 10 }, (_, i) => ({
    id: `clip-${i + 1}`,
    title: [
      'Podcast Terpendek di Dunia?! 😱',
      'Rahasia Sukses yang Tak Terduga',
      'Momen Kocak yang Bikin Ngakak',
      'Fakta Mengejutkan Tentang AI',
      'Tips Produktifitas Level Dewa',
      'Kesalahan Fatal Content Creator',
      'Viral Hack yang Jarang Diketahui',
      'Story Time: Kejadian Aneh Malam Ini',
      'Tutorial Cepat yang Wajib Kamu Tahu',
      'Review Jujur Setelah 1 Tahun Pakai',
    ][i],
    score: [98, 95, 92, 88, 85, 82, 79, 75, 71, 68][i],
    duration: ['0:30', '0:45', '0:28', '0:55', '0:32', '0:40', '0:25', '0:50', '0:35', '0:42'][i],
    platforms: [
      ['tiktok', 'reels', 'shorts'],
      ['tiktok', 'shorts'],
      ['tiktok', 'reels', 'shorts'],
      ['reels', 'shorts'],
      ['tiktok', 'reels', 'shorts'],
      ['tiktok'],
      ['tiktok', 'reels', 'shorts'],
      ['shorts'],
      ['tiktok', 'reels', 'shorts'],
      ['tiktok', 'reels'],
    ][i],
    start: i * 60,
    end: (i + 1) * 60,
  }))

  const toggleSelect = (id) => {
    const next = new Set(selected)
    if (next.has(id)) next.delete(id)
    else next.add(id)
    setSelected(next)
    setSelectAll(next.size === displayClips.length)
  }

  const toggleSelectAll = () => {
    if (selectAll) {
      setSelected(new Set())
      setSelectAll(false)
    } else {
      setSelected(new Set(displayClips.map(c => c.id)))
      setSelectAll(true)
    }
  }

  const handleBatchExport = () => {
    const count = selected.size || displayClips.length
    alert(`Exporting ${count} clips... (simulated)`)
  }

  return (
    <motion.div
      initial={{ opacity: 0 }}
      animate={{ opacity: 1 }}
      exit={{ opacity: 0 }}
      className="fixed inset-0 z-50 bg-[#07080B]/95 backdrop-blur-xl overflow-y-auto"
    >
      <div className="max-w-7xl mx-auto px-4 py-6">
        {/* Header */}
        <div className="flex items-center justify-between mb-6">
          <div>
            <motion.h1
              initial={{ opacity: 0, y: -10 }}
              animate={{ opacity: 1, y: 0 }}
              className="text-2xl font-bold text-white flex items-center gap-2"
            >
              <FiTrendingUp className="text-spacex-accent" />
              Top 10 Viral Clips
            </motion.h1>
            <p className="text-sm text-gray-600 mt-1">
              AI-curated clips dengan virality score tertinggi
            </p>
          </div>
          <div className="flex items-center gap-3">
            <button
              onClick={toggleSelectAll}
              className="btn-secondary text-sm flex items-center gap-2"
            >
              {selectAll ? <FiCheckSquare size={16} /> : <FiSquare size={16} />}
              {selectAll ? 'Deselect All' : 'Select All'}
            </button>
            <motion.button
              whileHover={{ scale: 1.03 }}
              whileTap={{ scale: 0.97 }}
              onClick={handleBatchExport}
              className="btn-primary flex items-center gap-2 animate-pulse-glow"
            >
              <FiDownload size={16} />
              Export {selected.size > 0 ? selected.size : 'All'} {displayClips.length} Clips
            </motion.button>
            {onClose && (
              <button onClick={onClose} className="btn-secondary text-sm">
                ✕ Close
              </button>
            )}
          </div>
        </div>

        {/* Grid */}
        <motion.div
          initial="hidden"
          animate="show"
          className="grid grid-cols-2 sm:grid-cols-3 md:grid-cols-4 lg:grid-cols-5 gap-4"
        >
          {displayClips.map((clip, i) => (
            <ClipCard
              key={clip.id}
              clip={clip}
              index={i}
              isSelected={selected.has(clip.id)}
              onSelect={toggleSelect}
              onCustomize={onCustomize}
            />
          ))}
        </motion.div>
      </div>
    </motion.div>
  )
}
