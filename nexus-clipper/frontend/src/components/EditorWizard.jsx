import React, { useState, useCallback, useEffect } from 'react'
import { motion, AnimatePresence } from 'framer-motion'
import { 
  FiChevronLeft, FiChevronRight, FiCheck, FiDownload, 
  FiCrop, FiLayout, FiType, FiVolume2, FiFilm,
  FiPlay, FiPause
} from 'react-icons/fi'

const STEPS = [
  { id: 1, label: 'Trim & Ratio',   icon: '✂️' },
  { id: 2, label: 'AI Reframe',     icon: '🖼️' },
  { id: 3, label: 'Captions',       icon: '💬' },
  { id: 4, label: 'Audio',          icon: '🎵' },
  { id: 5, label: 'Render',         icon: '🎬' },
]

const ASPECT_RATIOS = [
  { id: '9:16', label: '9:16', desc: 'TikTok / Reels / Shorts', icon: '📱', w: 1080, h: 1920 },
  { id: '1:1',  label: '1:1',  desc: 'Instagram Feed',          icon: '◻️', w: 1080, h: 1080 },
  { id: '16:9', label: '16:9', desc: 'YouTube Landscape',       icon: '🖥️', w: 1920, h: 1080 },
  { id: '4:5',  label: '4:5',  desc: 'Instagram Portrait',      icon: '📲', w: 1080, h: 1350 },
]

const LAYOUTS = [
  { id: 'fill',      label: 'Fill',        desc: 'Speaker full frame',            icon: '🧑',   preview: '1' },
  { id: 'split',     label: 'Split 50/50', desc: 'Two speakers side by side',     icon: '👥',   preview: '2h' },
  { id: 'triple',    label: 'Triple Stack',desc: 'Three speakers stacked',         icon: '👥👤', preview: '3v' },
  { id: 'gameplay',  label: 'Gameplay',    desc: 'Face over gameplay footage',    icon: '🎮',   preview: 'fg' },
  { id: 'screenshare',label:'Screen Share',desc: 'Face + screen recording',       icon: '💻',   preview: 'fs' },
]

const CAPTION_STYLES = [
  { id: 'karaoke',   name: 'Karaoke',   desc: 'Highlight per kata menyala',       color: '#FFD700' },
  { id: 'podp',      name: 'Pod P',     desc: 'Hitam transparan, bawah',          color: '#333333' },
  { id: 'deepdiver', name: 'Deep Diver',desc: 'Kata muncul dari bawah',           color: '#00F0FF' },
  { id: 'mozi',      name: 'Mozi',      desc: 'Pop kuning Hormozi style',         color: '#CCFF00' },
  { id: 'youshael',  name: 'Youshael',  desc: 'Clean white, elegant minimal',     color: '#FFFFFF' },
]

// ─── Utility: Simple Waveform Simulator ───
function Waveform({ duration = 60, startTime, endTime, onTrimChange }) {
  const bars = 120
  const pixelsPerBar = 4
  
  const handleBarClick = (e) => {
    const rect = e.currentTarget.getBoundingClientRect()
    const x = e.clientX - rect.left
    const ratio = x / rect.width
    const time = ratio * duration
    // Toggle: if closer to start, set start; else set end
    const distStart = Math.abs(time - startTime)
    const distEnd = Math.abs(time - endTime)
    if (distStart < distEnd) {
      onTrimChange(Math.max(0, Math.min(time, endTime - 1)), endTime)
    } else {
      onTrimChange(startTime, Math.min(duration, Math.max(time, startTime + 1)))
    }
  }

  return (
    <div className="space-y-2">
      {/* Time labels */}
      <div className="flex justify-between text-[10px] text-gray-600 font-mono">
        <span>{formatTime(startTime)}</span>
        <span>{formatTime(endTime)}</span>
        <span>{formatTime(duration)}</span>
      </div>

      {/* Waveform container */}
      <div
        onClick={handleBarClick}
        className="relative h-16 bg-white/[0.03] rounded-xl overflow-hidden cursor-pointer border border-white/5 hover:border-white/10 transition-colors"
      >
        {/* Waveform bars */}
        <div className="absolute inset-0 flex items-end px-1 gap-px">
          {Array.from({ length: bars }).map((_, i) => {
            const h = 15 + Math.sin(i * 0.4) * 25 + Math.sin(i * 0.13) * 15 + Math.random() * 8
            const timeAtBar = (i / bars) * duration
            const inSelection = timeAtBar >= startTime && timeAtBar <= endTime
            return (
              <div
                key={i}
                className={`flex-1 rounded-t-sm transition-colors ${
                  inSelection ? 'bg-spacex-accent/60' : 'bg-white/10'
                }`}
                style={{ height: `${h}%` }}
              />
            )
          })}
        </div>

        {/* Selection overlay */}
        <div
          className="absolute top-0 bottom-0 bg-spacex-accent/10 border-l border-r border-spacex-accent/30"
          style={{
            left: `${(startTime / duration) * 100}%`,
            width: `${((endTime - startTime) / duration) * 100}%`,
          }}
        />

        {/* Handles */}
        <div
          className="absolute top-0 bottom-0 w-2 bg-spacex-accent cursor-ew-resize rounded-sm shadow-[0_0_10px_rgba(204,255,0,0.4)] z-10"
          style={{ left: `${(startTime / duration) * 100}%`, transform: 'translateX(-50%)' }}
        />
        <div
          className="absolute top-0 bottom-0 w-2 bg-spacex-accent cursor-ew-resize rounded-sm shadow-[0_0_10px_rgba(204,255,0,0.4)] z-10"
          style={{ left: `${(endTime / duration) * 100}%`, transform: 'translateX(-50%)' }}
        />
      </div>
    </div>
  )
}

function formatTime(s) {
  const m = Math.floor(s / 60)
  const sec = Math.floor(s % 60)
  return `${m}:${sec.toString().padStart(2, '0')}`
}

// ─── Step Content Components ───

function Step1Trim({ config, updateConfig }) {
  const duration = 60 // simulation
  const [startTime, setStartTime] = useState(0)
  const [endTime, setEndTime] = useState(config.target_duration || 30)

  // Live viewport dimensions
  const ratioMap = {
    '9:16': { w: 1080, h: 1920, label: '9:16' },
    '1:1':  { w: 1080, h: 1080, label: '1:1' },
    '16:9': { w: 1920, h: 1080, label: '16:9' },
    '4:5':  { w: 1080, h: 1350, label: '4:5' },
  }
  const activeRatio = ratioMap[config.aspect_ratio] || ratioMap['9:16']
  const previewScale = 0.12
  const previewW = Math.round(activeRatio.w * previewScale)
  const previewH = Math.round(activeRatio.h * previewScale)

  const handleTrim = (s, e) => {
    setStartTime(s)
    setEndTime(e)
    updateConfig('target_duration', Math.round(e - s))
  }

  return (
    <div className="space-y-5">
      <h2 className="text-lg font-bold text-white">✂️ Trim & Aspect Ratio</h2>
      <p className="text-sm text-gray-500">Potong klip ke bagian terbaik dan pilih format output.</p>

      {/* Live viewport preview */}
      <div className="glass-card p-4">
        <p className="text-xs text-gray-500 mb-3">
          Live Viewport — <span className="text-spacex-accent">{activeRatio.label}</span>
          {' '}({activeRatio.w}×{activeRatio.h})
        </p>
        <div className="flex justify-center">
          <motion.div
            animate={{ width: previewW, height: previewH }}
            transition={{ type: 'spring', stiffness: 200, damping: 20 }}
            className="bg-black rounded-lg border border-white/10 flex items-center justify-center overflow-hidden relative"
            style={{ minWidth: 60, minHeight: 80 }}
          >
            <span className="text-2xl opacity-20">🎬</span>
            <div className="absolute bottom-2 right-2 text-[8px] text-gray-600 font-mono">
              {activeRatio.w}×{activeRatio.h}
            </div>
          </motion.div>
        </div>
      </div>

      {/* Waveform */}
      <div className="glass-card p-4">
        <p className="text-xs text-gray-500 mb-3">Audio Timeline</p>
        <Waveform
          duration={duration}
          startTime={startTime}
          endTime={endTime}
          onTrimChange={handleTrim}
        />
        <div className="flex justify-between mt-2 text-xs text-gray-600">
          <span>Duration: <b className="text-spacex-accent">{Math.round(endTime - startTime)}s</b></span>
          <span className="text-spacex-cyan">{formatTime(startTime)} – {formatTime(endTime)}</span>
        </div>
      </div>

      {/* Aspect Ratio Selector */}
      <div>
        <p className="text-xs text-gray-500 mb-2">Aspect Ratio</p>
        <div className="grid grid-cols-4 gap-2">
          {ASPECT_RATIOS.map(r => {
            const isActive = config.aspect_ratio === r.id
            const previewW = r.w / 60
            const previewH = r.h / 60
            return (
              <motion.button
                key={r.id}
                whileHover={{ scale: 1.03 }}
                whileTap={{ scale: 0.97 }}
                onClick={() => updateConfig('aspect_ratio', r.id)}
                className={`p-3 rounded-xl border text-center transition-all ${
                  isActive
                    ? 'border-spacex-accent bg-spacex-accent/5 shadow-lg shadow-spacex-accent/10'
                    : 'border-white/5 bg-white/[0.02] hover:border-white/10'
                }`}
              >
                <div
                  className="mx-auto mb-1.5 border border-white/20 rounded-sm"
                  style={{ width: Math.min(previewW, 40), height: Math.min(previewH, 40) }}
                />
                <div className="text-lg">{r.icon}</div>
                <div className={`text-xs font-semibold ${isActive ? 'text-spacex-accent' : 'text-gray-300'}`}>
                  {r.label}
                </div>
                <div className="text-[9px] text-gray-600">{r.desc}</div>
              </motion.button>
            )
          })}
        </div>
      </div>
    </div>
  )
}

function Step2Reframe({ config, updateConfig }) {
  return (
    <div className="space-y-5">
      <h2 className="text-lg font-bold text-white">🖼️ AI Reframe & Smart Layout</h2>
      <p className="text-sm text-gray-500">Pilih layout otomatis untuk multi-speaker atau screen share.</p>

      {/* Preview container */}
      <div className="glass-card p-4">
        <p className="text-xs text-gray-500 mb-3">
          Live Preview — <span className="text-spacex-accent capitalize">{config.layout || 'fill'}</span>
        </p>
        <div className="aspect-[9/16] bg-black rounded-lg mx-auto max-w-[220px] border border-white/5 flex items-center justify-center relative overflow-hidden">
          {/* Simulate layout masks */}
          <div className="absolute inset-0 flex items-center justify-center">
            <div className="text-6xl opacity-20">🧑</div>
          </div>
          <AnimatePresence mode="wait">
            <motion.div
              key={config.layout || 'fill'}
              initial={{ opacity: 0 }}
              animate={{ opacity: 1 }}
              exit={{ opacity: 0 }}
              transition={{ duration: 0.25 }}
              className="absolute inset-0"
            >
              {config.layout === 'split' && (
                <>
                  <div className="absolute top-0 left-0 right-0 h-1/2 bg-spacex-cyan/10 border-b border-spacex-cyan/20" />
                  <div className="absolute bottom-0 left-0 right-0 h-1/2 bg-spacex-purple/10" />
                </>
              )}
              {config.layout === 'triple' && (
                <>
                  <div className="absolute top-0 left-0 right-0 h-1/3 bg-spacex-cyan/10 border-b border-spacex-cyan/20" />
                  <div className="absolute top-1/3 left-0 right-0 h-1/3 bg-spacex-purple/10 border-b border-spacex-purple/20" />
                  <div className="absolute bottom-0 left-0 right-0 h-1/3 bg-spacex-accent/10" />
                </>
              )}
              {config.layout === 'gameplay' && (
                <motion.div
                  initial={{ scale: 0.8, opacity: 0 }}
                  animate={{ scale: 1, opacity: 1 }}
                  className="absolute bottom-4 right-4 w-16 h-20 bg-spacex-accent/20 rounded-lg border border-spacex-accent/30"
                />
              )}
              {config.layout === 'screenshare' && (
                <motion.div
                  initial={{ scale: 0.9, opacity: 0 }}
                  animate={{ scale: 1, opacity: 1 }}
                  className="absolute top-4 left-4 right-4 bottom-16 bg-spacex-cyan/10 rounded border border-spacex-cyan/20"
                />
              )}
            </motion.div>
          </AnimatePresence>
        </div>
      </div>

      {/* Layout selector */}
      <div>
        <p className="text-xs text-gray-500 mb-2">Layout Presets</p>
        <div className="grid grid-cols-2 sm:grid-cols-3 gap-2">
          {LAYOUTS.map(l => {
            const isActive = config.layout === l.id
            return (
              <motion.button
                key={l.id}
                whileHover={{ scale: 1.03 }}
                whileTap={{ scale: 0.97 }}
                onClick={() => updateConfig('layout', l.id)}
                className={`p-3 rounded-xl border text-left transition-all ${
                  isActive
                    ? 'border-spacex-accent bg-spacex-accent/5'
                    : 'border-white/5 bg-white/[0.02] hover:border-white/10'
                }`}
              >
                <div className="text-xl mb-1">{l.icon}</div>
                <div className={`text-xs font-semibold ${isActive ? 'text-spacex-accent' : 'text-gray-300'}`}>
                  {l.label}
                </div>
                <div className="text-[10px] text-gray-600">{l.desc}</div>
              </motion.button>
            )
          })}
        </div>
      </div>
    </div>
  )
}

function Step3Captions({ config, updateConfig }) {
  return (
    <div className="space-y-5">
      <h2 className="text-lg font-bold text-white">💬 Captions & Style</h2>
      <p className="text-sm text-gray-500">Pilih style teks, warna highlight, dan posisi subtitle.</p>

      {/* Caption style presets */}
      <div>
        <p className="text-xs text-gray-500 mb-2">Caption Style</p>
        <div className="flex gap-2 flex-wrap">
          {CAPTION_STYLES.map(cs => {
            const isActive = config.subtitle_style === cs.id
            return (
              <motion.button
                key={cs.id}
                whileHover={{ scale: 1.03 }}
                whileTap={{ scale: 0.97 }}
                onClick={() => updateConfig('subtitle_style', cs.id)}
                className={`px-4 py-3 rounded-xl border text-left transition-all ${
                  isActive
                    ? 'border-spacex-accent bg-spacex-accent/5'
                    : 'border-white/5 bg-white/[0.02] hover:border-white/10'
                }`}
              >
                <div className="flex items-center gap-2 mb-1">
                  <div className="w-3 h-3 rounded-full" style={{ backgroundColor: cs.color }} />
                  <span className={`text-sm font-semibold ${isActive ? 'text-white' : 'text-gray-300'}`}>
                    {cs.name}
                  </span>
                </div>
                <div className="text-[10px] text-gray-600">{cs.desc}</div>
              </motion.button>
            )
          })}
        </div>
      </div>

      {/* Auto-Censorship Toggle */}
      <motion.div
        whileHover={{ scale: 1.01 }}
        className="glass-card p-4 flex items-center justify-between"
      >
        <div className="flex items-center gap-3">
          <span className="text-xl">🤬</span>
          <div>
            <p className="text-sm font-medium text-gray-200">Auto-Censorship</p>
            <p className="text-[11px] text-gray-600">Filter kata kasar menjadi "f***", "s***", dll.</p>
          </div>
        </div>
        <button
          onClick={() => updateConfig('censorship', !config.censorship)}
          className={`w-12 h-7 rounded-full transition-all relative ${
            config.censorship ? 'bg-spacex-accent' : 'bg-white/10'
          }`}
        >
          <motion.div
            animate={{ x: config.censorship ? 22 : 2 }}
            className="w-5 h-5 rounded-full bg-white absolute top-1 shadow-md"
          />
        </button>
      </motion.div>

      {/* Live Caption Preview */}
      <div className="glass-card p-4">
        <div className="flex items-center justify-between mb-3">
          <p className="text-xs text-gray-500">Live Caption Preview</p>
          <span className="text-[10px] text-gray-700">Updates real-time</span>
        </div>
        <div className={`relative mx-auto border border-white/5 overflow-hidden bg-black rounded-lg`}
          style={{
            aspectRatio: config.aspect_ratio || '9/16',
            maxWidth: '200px',
          }}>
          {/* Video placeholder */}
          <div className="absolute inset-0 flex items-center justify-center">
            <div className="text-4xl opacity-15">🎬</div>
          </div>
          {/* Caption overlay — dynamic position */}
          <div className={`absolute left-0 right-0 flex justify-center px-3 ${
            config.position === 'top' ? 'top-4' : config.position === 'bottom' ? 'bottom-12' : 'bottom-12'
          }`}>
            <div 
              className="text-center px-3 py-2 rounded-lg transition-all duration-200"
              style={{
                fontFamily: config.font || 'Arial',
                fontSize: `${Math.max(9, (config.font_size || 48) * 0.22)}px`,
                color: config.primary_color || '#FFFFFF',
                textShadow: [
                  `0 0 ${config.stroke_width || 3}px ${config.stroke_color || '#000'}`,
                  `-${config.stroke_width || 3}px -${config.stroke_width || 3}px 0 ${config.stroke_color || '#000'}`,
                  `${config.stroke_width || 3}px -${config.stroke_width || 3}px 0 ${config.stroke_color || '#000'}`,
                  `-${config.stroke_width || 3}px ${config.stroke_width || 3}px 0 ${config.stroke_color || '#000'}`,
                  `${config.stroke_width || 3}px ${config.stroke_width || 3}px 0 ${config.stroke_color || '#000'}`,
                ].join(', '),
              }}
            >
              <motion.span
                animate={{ opacity: [0.6, 1, 0.6] }}
                transition={{ duration: 1.5, repeat: Infinity }}
              >
                Podcast Terpendek
              </motion.span>
              {' '}
              <motion.span
                animate={{ scale: [1, 1.15, 1] }}
                transition={{ duration: 0.6, repeat: Infinity, delay: 0.3 }}
                style={{ color: config.highlight_color || '#FFD700' }}
              >
                di Dunia?!
              </motion.span>
            </div>
          </div>
        </div>
      </div>

      {/* Options */}
      <div className="space-y-4">
        {/* Word Highlight Color */}
        <div className="glass-card p-4">
          <label className="text-xs text-gray-500 block mb-2">Word Highlight Color</label>
          <div className="flex gap-2">
            {[
              { color: '#FFD700', label: 'Neon Yellow' },
              { color: '#CCFF00', label: 'Lime' },
              { color: '#00F0FF', label: 'Cyan' },
              { color: '#00FF88', label: 'Green' },
              { color: '#FF4444', label: 'Red' },
            ].map(c => {
              const isActive = config.highlight_color === c.color
              return (
                <button
                  key={c.color}
                  onClick={() => updateConfig('highlight_color', c.color)}
                  className={`flex-1 py-2 rounded-lg text-[10px] font-medium transition-all border ${
                    isActive
                      ? 'border-spacex-accent bg-spacex-accent/10 text-white scale-105 shadow-lg shadow-spacex-accent/10'
                      : 'border-white/5 bg-white/[0.02] text-gray-500 hover:border-white/10'
                  }`}
                >
                  <div className="w-5 h-5 rounded-full mx-auto mb-1" style={{ backgroundColor: c.color }} />
                  {c.label}
                </button>
              )
            })}
          </div>
        </div>

        {/* Font size + Position sliders */}
        <div className="grid grid-cols-2 gap-4">
          <div className="glass-card p-4">
            <label className="text-xs text-gray-500 block mb-1">
              Font Size: <span className="text-spacex-accent">{config.font_size}px</span>
            </label>
            <input type="range" min={24} max={96}
              value={config.font_size} onChange={e => updateConfig('font_size', Number(e.target.value))}
              className="w-full"
            />
            <div className="flex justify-between text-[9px] text-gray-700 mt-0.5">
              <span>24</span><span>48</span><span>72</span><span>96</span>
            </div>
          </div>
          <div className="glass-card p-4">
            <label className="text-xs text-gray-500 block mb-1">
              Position (Safe Zone Y): <span className="text-spacex-accent capitalize">{config.position || 'center'}</span>
            </label>
            <input type="range" min={0} max={100}
              value={config.position === 'top' ? 20 : config.position === 'bottom' ? 80 : 50}
              onChange={e => {
                const v = Number(e.target.value)
                if (v < 33) updateConfig('position', 'top')
                else if (v > 66) updateConfig('position', 'bottom')
                else updateConfig('position', 'center')
              }}
              className="w-full"
            />
            <div className="flex justify-between text-[9px] text-gray-700 mt-0.5">
              <span>Top</span><span>Center</span><span>Bottom</span>
            </div>
          </div>
        </div>
      </div>
    </div>
  )
}

function Step4Audio({ config, updateConfig }) {
  return (
    <div className="space-y-5">
      <h2 className="text-lg font-bold text-white">🎵 Audio & Magic Enhancements</h2>
      <p className="text-sm text-gray-500">Tingkatkan kualitas audio dan tambahkan efek otomatis.</p>

      {/* Toggle switches */}
      <div className="space-y-3">
        {[
          { key: 'noise_removal', label: 'AI Noise Removal', desc: 'Hapus background noise otomatis', icon: '🔇' },
          { key: 'bgm_ducking', label: 'Auto BGM Ducking', desc: 'Musik mengecil saat ada suara', icon: '🎚️' },
          { key: 'broll_insert', label: 'Auto B-Roll Insertion', desc: 'Sisipkan footage pendukung otomatis', icon: '🎞️' },
        ].map(toggle => {
          const isOn = config[toggle.key] ?? false
          return (
            <motion.div
              key={toggle.key}
              whileHover={{ scale: 1.01 }}
              className="glass-card p-4 flex items-center justify-between"
            >
              <div className="flex items-center gap-3">
                <span className="text-xl">{toggle.icon}</span>
                <div>
                  <p className="text-sm font-medium text-gray-200">{toggle.label}</p>
                  <p className="text-[11px] text-gray-600">{toggle.desc}</p>
                </div>
              </div>
              <button
                onClick={() => updateConfig(toggle.key, !isOn)}
                className={`w-12 h-7 rounded-full transition-all relative ${
                  isOn ? 'bg-spacex-accent' : 'bg-white/10'
                }`}
              >
                <motion.div
                  animate={{ x: isOn ? 22 : 2 }}
                  className="w-5 h-5 rounded-full bg-white absolute top-1 shadow-md"
                />
              </button>
            </motion.div>
          )
        })}
      </div>

      {/* BGM Volume */}
      <div className="glass-card p-4">
        <label className="text-xs text-gray-500 block mb-1 flex items-center justify-between">
          <span>BGM Volume</span>
          <span className="text-spacex-accent font-mono">{config.bgm_volume ?? -16} dB</span>
        </label>
        <input
          type="range" min={-22} max={-10} step={1}
          value={config.bgm_volume ?? -16}
          onChange={e => updateConfig('bgm_volume', Number(e.target.value))}
          className="w-full"
        />
        <div className="flex justify-between text-[10px] text-gray-700 mt-1">
          <span>-22dB</span><span>-18dB</span><span>-14dB</span><span>-10dB</span>
        </div>
      </div>

      {/* Render & Download MP4 CTA */}
      <div className="text-center pt-2">
        <motion.button
          whileHover={{ scale: 1.03 }}
          whileTap={{ scale: 0.97 }}
          onClick={() => {
            updateConfig('_renderNow', true)
            // Auto-transition to Step 5
            const event = new CustomEvent('nexus-goto-step', { detail: 5 })
            window.dispatchEvent(event)
          }}
          className="btn-primary text-lg px-10 py-4 inline-flex items-center gap-3 animate-pulse-glow"
        >
          <FiFilm size={24} />
          Render & Download MP4
        </motion.button>
        <p className="text-[11px] text-gray-600 mt-2">Proses render ~2-5 menit</p>
      </div>
    </div>
  )
}

function Step5Render({ config, autoStart = true }) {
  const [progress, setProgress] = useState(0)
  const [statusText, setStatusText] = useState('')
  const [isRendering, setIsRendering] = useState(false)
  const [isComplete, setIsComplete] = useState(false)
  const [hasAutoStarted, setHasAutoStarted] = useState(false)

  const startRender = useCallback(() => {
    setIsRendering(true)
    setProgress(0)
    setStatusText(renderStages[0].text)
    let currentStage = 0
    const interval = setInterval(() => {
      setProgress(prev => {
        const next = prev + Math.random() * 3 + 1
        const stage = renderStages.find(s => next >= s.pct) || renderStages[renderStages.length - 1]
        setStatusText(stage.text)
        if (next >= 100) {
          clearInterval(interval)
          setIsRendering(false)
          setIsComplete(true)
          setStatusText('Render Complete! 🎉')
          return 100
        }
        return Math.min(next, 99)
      })
    }, 200)
  }, [])

  // Auto-start render when entering Step 5
  useEffect(() => {
    if (autoStart && !hasAutoStarted) {
      setHasAutoStarted(true)
      startRender()
    }
  }, [autoStart, hasAutoStarted, startRender])

  const renderStages = [
    { pct: 0,   text: 'Slicing video source...' },
    { pct: 25,  text: 'Burning in animated captions...' },
    { pct: 50,  text: 'Applying audio enhancements...' },
    { pct: 70,  text: 'Adding auto-reframe & layout...' },
    { pct: 90,  text: 'Encoding final video...' },
    { pct: 100, text: 'Finalizing MP4 export...' },
  ]

  // (startRender now defined above with useCallback + useEffect)

  return (
    <div className="space-y-5">
      <h2 className="text-lg font-bold text-white">🎬 Render & Download</h2>

      {!isRendering && !isComplete && (
        <div className="text-center py-8">
          <motion.button
            whileHover={{ scale: 1.03 }}
            whileTap={{ scale: 0.97 }}
            onClick={startRender}
            className="btn-primary text-lg px-10 py-4 inline-flex items-center gap-3 animate-pulse-glow"
          >
            <FiFilm size={24} />
            Render Video
          </motion.button>
          <p className="text-xs text-gray-600 mt-3">Proses render ~2-5 menit tergantung durasi</p>
        </div>
      )}

      {/* Cinematic render progress */}
      <AnimatePresence>
        {isRendering && (
          <motion.div
            initial={{ opacity: 0, scale: 0.95 }}
            animate={{ opacity: 1, scale: 1 }}
            className="glass-card p-6 space-y-4"
          >
            {/* Glowing progress ring */}
            <div className="flex justify-center">
              <div className="relative w-24 h-24">
                <svg className="w-24 h-24 transform -rotate-90" viewBox="0 0 100 100">
                  <circle cx="50" cy="50" r="42" fill="none" stroke="rgba(255,255,255,0.05)" strokeWidth="6" />
                  <motion.circle
                    cx="50" cy="50" r="42" fill="none"
                    stroke="url(#grad)" strokeWidth="6" strokeLinecap="round"
                    strokeDasharray={`${2 * Math.PI * 42}`}
                    initial={{ strokeDashoffset: 2 * Math.PI * 42 }}
                    animate={{ strokeDashoffset: (1 - progress / 100) * (2 * Math.PI * 42) }}
                    transition={{ duration: 0.3 }}
                  />
                  <defs>
                    <linearGradient id="grad" x1="0" y1="0" x2="1" y2="1">
                      <stop offset="0%" stopColor="#CCFF00" />
                      <stop offset="100%" stopColor="#00F0FF" />
                    </linearGradient>
                  </defs>
                </svg>
                <div className="absolute inset-0 flex items-center justify-center">
                  <span className="text-xl font-bold font-mono text-spacex-accent">{Math.round(progress)}%</span>
                </div>
              </div>
            </div>

            {/* Stage text */}
            <motion.p
              key={statusText}
              initial={{ opacity: 0, y: 4 }}
              animate={{ opacity: 1, y: 0 }}
              className="text-sm text-gray-400 text-center"
            >
              {statusText}
            </motion.p>

            {/* Linear progress */}
            <div className="w-full bg-white/5 rounded-full h-1.5 overflow-hidden">
              <motion.div
                className="h-full rounded-full bg-gradient-to-r from-spacex-accent to-spacex-cyan"
                animate={{ width: `${progress}%` }}
                transition={{ duration: 0.3 }}
              />
            </div>
          </motion.div>
        )}
      </AnimatePresence>

      {/* Complete state */}
      <AnimatePresence>
        {isComplete && (
          <motion.div
            initial={{ opacity: 0, y: 20 }}
            animate={{ opacity: 1, y: 0 }}
            className="glass-card p-6 space-y-4 text-center"
          >
            {/* Success badge */}
            <motion.div
              initial={{ scale: 0 }}
              animate={{ scale: 1 }}
              transition={{ type: 'spring', stiffness: 200, damping: 15 }}
              className="inline-flex items-center gap-2 px-4 py-2 rounded-full bg-spacex-success/10 border border-spacex-success/30"
            >
              <FiCheck className="text-spacex-success" size={18} />
              <span className="text-sm font-bold text-spacex-success">Render Complete!</span>
            </motion.div>

            {/* Video preview placeholder */}
            <div className="aspect-[9/16] bg-black rounded-xl mx-auto max-w-[260px] border border-white/5 flex items-center justify-center">
              <div className="text-center space-y-2">
                <FiPlay size={40} className="text-white/30 mx-auto" />
                <p className="text-xs text-gray-600">Your viral clip is ready</p>
              </div>
            </div>

            {/* Download button */}
            <motion.button
              whileHover={{ scale: 1.03 }}
              whileTap={{ scale: 0.97 }}
              className="btn-primary text-lg px-8 py-4 inline-flex items-center gap-3 animate-pulse-glow"
            >
              <FiDownload size={22} />
              Download Video
            </motion.button>

            {/* Secondary actions */}
            <div className="flex justify-center gap-3">
              <button className="btn-secondary text-xs">Share to TikTok</button>
              <button className="btn-secondary text-xs">Share to Instagram</button>
              <button onClick={onClose} className="btn-secondary text-xs">Return to Dashboard</button>
            </div>
          </motion.div>
        )}
      </AnimatePresence>
    </div>
  )
}

// ─── MAIN WIZARD COMPONENT ───

export default function EditorWizard({ config, updateConfig, onClose }) {
  const [step, setStep] = useState(1)
  const totalSteps = STEPS.length

  const handleNext = () => { if (step < totalSteps) setStep(s => s + 1) }
  const handlePrev = () => { if (step > 1) setStep(s => s - 1) }

  // Listen for render-triggered step nav
  useEffect(() => {
    const handler = (e) => setStep(e.detail)
    window.addEventListener('nexus-goto-step', handler)
    return () => window.removeEventListener('nexus-goto-step', handler)
  }, [])

  return (
    <motion.div
      initial={{ opacity: 0 }}
      animate={{ opacity: 1 }}
      exit={{ opacity: 0 }}
      className="fixed inset-0 z-50 bg-[#07080B]/95 backdrop-blur-xl overflow-y-auto"
    >
      <div className="max-w-4xl mx-auto px-4 py-6">
        {/* Close button */}
        <div className="flex justify-end mb-4">
          <button onClick={onClose} className="btn-secondary text-sm">
            ✕ Close Editor
          </button>
        </div>

        {/* Stepper */}
        <div className="flex items-center justify-center mb-8">
          {STEPS.map((s, i) => (
            <React.Fragment key={s.id}>
              {i > 0 && (
                <div className={`stepper-line ${i < step ? 'done' : ''}`} />
              )}
              <div className="flex flex-col items-center gap-1">
                <div
                  className={`stepper-dot ${
                    step > s.id ? 'done' : step === s.id ? 'active' : 'pending'
                  }`}
                >
                  {step > s.id ? '✓' : s.icon}
                </div>
                <span className={`text-[10px] ${
                  step === s.id ? 'text-spacex-accent' : 'text-gray-600'
                }`}>
                  {s.label}
                </span>
              </div>
            </React.Fragment>
          ))}
        </div>

        {/* Step content */}
        <AnimatePresence mode="wait">
          <motion.div
            key={step}
            initial={{ opacity: 0, x: 20 }}
            animate={{ opacity: 1, x: 0 }}
            exit={{ opacity: 0, x: -20 }}
            transition={{ duration: 0.2 }}
            className="glass-card p-6"
          >
            {step === 1 && <Step1Trim config={config} updateConfig={updateConfig} />}
            {step === 2 && <Step2Reframe config={config} updateConfig={updateConfig} />}
            {step === 3 && <Step3Captions config={config} updateConfig={updateConfig} />}
            {step === 4 && <Step4Audio config={config} updateConfig={updateConfig} />}
            {step === 5 && <Step5Render config={config} />}
          </motion.div>
        </AnimatePresence>

        {/* Navigation */}
        <div className="flex justify-between mt-6">
          <button
            onClick={handlePrev}
            disabled={step === 1}
            className="btn-secondary flex items-center gap-2 disabled:opacity-30"
          >
            <FiChevronLeft size={16} />
            Back
          </button>

          <span className="text-xs text-gray-600 self-center">
            Step {step} of {totalSteps}
          </span>

          {step < totalSteps ? (
            <button onClick={handleNext} className="btn-primary flex items-center gap-2">
              Next
              <FiChevronRight size={16} />
            </button>
          ) : (
            <button onClick={onClose} className="btn-primary flex items-center gap-2">
              <FiCheck size={16} />
              Finish
            </button>
          )}
        </div>
      </div>
    </motion.div>
  )
}
