import React from 'react'
import { motion } from 'framer-motion'

// Style definitions with FULL config — pilih style → auto-set semua
const STYLES = [
  { 
    id: 'hormozi', name: 'Hormozi', desc: 'Kata per kata, highlight kuning, pop-up', 
    icon: '💛', color: '#FFD700',
    config: { font: 'Arial', font_size: 52, primary_color: '#FFFFFF', highlight_color: '#FFD700', 
              stroke_color: '#000000', stroke_width: 3, position: 'center', animation: 'pop' }
  },
  { 
    id: 'mrbeast', name: 'MrBeast', desc: 'Teks tebal, stroke hitam tebal, dinamis', 
    icon: '🦁', color: '#00FF88',
    config: { font: 'Impact', font_size: 56, primary_color: '#FFFFFF', highlight_color: '#00FF88', 
              stroke_color: '#000000', stroke_width: 6, position: 'center', animation: 'pop_fast' }
  },
  { 
    id: 'aliabdaal', name: 'Ali Abdaal', desc: 'Bersih, minimalis, elegan', 
    icon: '✨', color: '#F5F5F5',
    config: { font: 'Helvetica', font_size: 42, primary_color: '#F5F5F5', highlight_color: '#FFD700', 
              stroke_color: '#1A1A2E', stroke_width: 2, position: 'center', animation: 'fade' }
  },
  { 
    id: 'minimalist', name: 'Minimalist', desc: 'Teks putih kecil, tanpa animasi berlebih', 
    icon: '🤍', color: '#CCCCCC',
    config: { font: 'Helvetica', font_size: 34, primary_color: '#CCCCCC', highlight_color: '#FFFFFF', 
              stroke_color: '#000000', stroke_width: 1, position: 'bottom', animation: 'none' }
  },
  { 
    id: 'gaming', name: 'Gaming', desc: 'Font bold, warna kontras, animasi bounce', 
    icon: '🎮', color: '#FF4444',
    config: { font: 'Impact', font_size: 58, primary_color: '#FF4444', highlight_color: '#FFFF00', 
              stroke_color: '#000000', stroke_width: 5, position: 'center', animation: 'bounce' }
  },
  { 
    id: 'cinematic', name: 'Cinematic', desc: 'Serif elegan, fade lambat, premium', 
    icon: '🎬', color: '#8888FF',
    config: { font: 'Georgia', font_size: 44, primary_color: '#EEEEFF', highlight_color: '#8888FF', 
              stroke_color: '#000011', stroke_width: 4, position: 'bottom', animation: 'fade_slow' }
  },
  { 
    id: 'neon', name: 'Neon', desc: 'Glow effect, warna neon flicker', 
    icon: '💜', color: '#FF00FF',
    config: { font: 'Arial', font_size: 48, primary_color: '#FF00FF', highlight_color: '#00FFFF', 
              stroke_color: '#4A0072', stroke_width: 3, position: 'center', animation: 'flicker' }
  },
  { 
    id: 'typewriter', name: 'Typewriter', desc: 'Huruf muncul satu per satu, retro', 
    icon: '⌨️', color: '#88FF88',
    config: { font: 'Courier New', font_size: 44, primary_color: '#88FF88', highlight_color: '#AAFFAA', 
              stroke_color: '#003300', stroke_width: 2, position: 'bottom', animation: 'typewriter' }
  },
  { 
    id: 'tiktok_viral', name: 'TikTok Viral', desc: 'Posisi acak, warna cerah, high energy', 
    icon: '🔥', color: '#FF6600',
    config: { font: 'Arial', font_size: 50, primary_color: '#FF6600', highlight_color: '#FFD700', 
              stroke_color: '#000000', stroke_width: 4, position: 'center', animation: 'pop' }
  },
  { 
    id: 'documentary', name: 'Documentary', desc: 'Serif klasik, posisi bawah, fade lambat', 
    icon: '📜', color: '#DDCCAA',
    config: { font: 'Georgia', font_size: 38, primary_color: '#DDCCAA', highlight_color: '#FFEEDD', 
              stroke_color: '#1A1A0A', stroke_width: 2, position: 'bottom', animation: 'fade_slow' }
  },
  { 
    id: 'comedy', name: 'Comedy', desc: 'Bouncy text, Comic Sans, timing komedi', 
    icon: '😂', color: '#FFCC00',
    config: { font: 'Comic Sans MS', font_size: 48, primary_color: '#FFCC00', highlight_color: '#FF6600', 
              stroke_color: '#000000', stroke_width: 3, position: 'center', animation: 'bounce' }
  },
  { 
    id: 'horror', name: 'Horror', desc: 'Flickering text, merah darah, Impact bold', 
    icon: '👻', color: '#FF0000',
    config: { font: 'Impact', font_size: 52, primary_color: '#FF0000', highlight_color: '#FF4444', 
              stroke_color: '#330000', stroke_width: 5, position: 'center', animation: 'flicker' }
  },
  { 
    id: 'motivational', name: 'Motivational', desc: 'Bold white, slow reveal, inspiring', 
    icon: '💪', color: '#FFFFFF',
    config: { font: 'Helvetica', font_size: 46, primary_color: '#FFFFFF', highlight_color: '#EEEEEE', 
              stroke_color: '#000000', stroke_width: 3, position: 'center', animation: 'slow_reveal' }
  },
  { 
    id: 'educational', name: 'Educational', desc: 'Top position, highlight key terms, biru clean', 
    icon: '📚', color: '#66BBFF',
    config: { font: 'Verdana', font_size: 40, primary_color: '#66BBFF', highlight_color: '#FFD700', 
              stroke_color: '#0D47A1', stroke_width: 2, position: 'top', animation: 'fade' }
  },
  { 
    id: 'custom', name: 'Custom', desc: 'Atur sendiri semua pengaturan manual', 
    icon: '🎨', color: '#A855F7',
    config: {} // custom = no auto-override
  },
]

const container = {
  hidden: { opacity: 0 },
  show: { opacity: 1, transition: { staggerChildren: 0.03 } },
}
const item = {
  hidden: { opacity: 0, y: 6 },
  show: { opacity: 1, y: 0 },
}

export default function StyleSelector({ config, updateConfig }) {
  const handleSelect = (style) => {
    // Set subtitle_style ID
    updateConfig('subtitle_style', style.id)

    // Auto-apply ALL preset config (kecuali custom)
    if (style.config && Object.keys(style.config).length > 0) {
      for (const [key, value] of Object.entries(style.config)) {
        updateConfig(key, value)
      }
    }
  }

  return (
    <div className="glass-card p-5">
      <div className="flex items-center gap-2 mb-4">
        <span className="text-lg">🎨</span>
        <h3 className="text-sm font-semibold text-gray-200">Style Presets</h3>
        <span className="badge badge-warning ml-auto">15 templates • auto-config</span>
      </div>

      <motion.div
        variants={container}
        initial="hidden"
        animate="show"
        className="grid grid-cols-2 sm:grid-cols-3 lg:grid-cols-5 gap-2.5"
      >
        {STYLES.map(style => {
          const isActive = config.subtitle_style === style.id
          return (
            <motion.button
              key={style.id}
              variants={item}
              whileHover={{ scale: 1.03, y: -2 }}
              whileTap={{ scale: 0.97 }}
              onClick={() => handleSelect(style)}
              className={`group relative p-3 rounded-xl border text-left transition-all duration-200 ${
                isActive
                  ? 'border-[#CCFF00]/40 bg-[#CCFF00]/5 shadow-lg shadow-[#CCFF00]/5'
                  : 'border-white/5 bg-white/[0.02] hover:border-white/10 hover:bg-white/[0.04]'
              }`}
            >
              {/* Active indicator */}
              {isActive && (
                <div className="absolute top-2 right-2 w-2 h-2 rounded-full bg-[#CCFF00] shadow-[0_0_8px_#CCFF00]" />
              )}

              {/* Preview color dot */}
              <div className="flex items-center gap-1.5 mb-1.5">
                <div className="w-7 h-7 rounded-lg flex items-center justify-center text-sm"
                  style={{ backgroundColor: style.color + '20' }}>
                  {style.icon}
                </div>
                {style.config?.font && (
                  <span className="text-[9px] text-gray-600 font-mono truncate max-w-[60px]">
                    {style.config.font}
                  </span>
                )}
              </div>

              <div className={`text-xs font-semibold mb-0.5 ${isActive ? 'text-white' : 'text-gray-300'}`}>
                {style.name}
              </div>
              <div className="text-[10px] text-gray-600 leading-tight">
                {style.desc.slice(0, 40)}{style.desc.length > 40 ? '...' : ''}
              </div>

              {/* Quick preview of colors */}
              {style.config?.primary_color && (
                <div className="flex gap-0.5 mt-1.5">
                  <div className="w-3 h-3 rounded-full border border-white/20" 
                    style={{ backgroundColor: style.config.primary_color }} />
                  <div className="w-3 h-3 rounded-full border border-white/20" 
                    style={{ backgroundColor: style.config.highlight_color }} />
                  <div className="w-3 h-3 rounded-full border border-white/20" 
                    style={{ backgroundColor: style.config.stroke_color }} />
                </div>
              )}
            </motion.button>
          )
        })}
      </motion.div>

      {/* Currently selected info */}
      <div className="mt-4 p-3 rounded-xl bg-white/[0.02] border border-white/5">
        <div className="flex items-center gap-4 text-[11px] text-gray-500 flex-wrap">
          <span>Font: <b className="text-gray-300">{config.font || 'Arial'}</b></span>
          <span>Size: <b className="text-gray-300">{config.font_size}px</b></span>
          <span>Position: <b className="text-gray-300">{config.position || 'center'}</b></span>
          <span>Anim: <b className="text-gray-300">{config.animation || 'pop'}</b></span>
          <span>Stroke: <b className="text-gray-300">{config.stroke_width}px</b></span>
        </div>
      </div>
    </div>
  )
}
