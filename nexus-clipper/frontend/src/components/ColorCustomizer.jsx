import React from 'react'

const COLOR_PRESETS = [
  { name: 'Hormozi', primary: '#FFFFFF', highlight: '#FFD700', stroke: '#000000' },
  { name: 'MrBeast', primary: '#FFFFFF', highlight: '#00FF88', stroke: '#000000' },
  { name: 'Neon Purple', primary: '#E040FB', highlight: '#FFD700', stroke: '#4A0072' },
  { name: 'Fire', primary: '#FF6D00', highlight: '#FFD600', stroke: '#BF360C' },
  { name: 'Ocean', primary: '#00E5FF', highlight: '#00FF88', stroke: '#004D40' },
  { name: 'Rose', primary: '#FF80AB', highlight: '#FFD700', stroke: '#880E4F' },
  { name: 'Mint', primary: '#69F0AE', highlight: '#FFFF00', stroke: '#1B5E20' },
  { name: 'Coral', primary: '#FF8A80', highlight: '#FFEA00', stroke: '#B71C1C' },
]

export default function ColorCustomizer({ config, updateConfig }) {
  return (
    <div className="glass-card p-5 space-y-5">
      <div className="flex items-center gap-2">
        <span className="text-lg">🌈</span>
        <h3 className="text-sm font-semibold text-gray-200">Colors & Effects</h3>
        <span className="badge badge-info ml-auto">8 palettes</span>
      </div>

      {/* Color Presets */}
      <div className="grid grid-cols-4 gap-2">
        {COLOR_PRESETS.map(preset => (
          <button
            key={preset.name}
            onClick={() => {
              updateConfig('primary_color', preset.primary)
              updateConfig('highlight_color', preset.highlight)
              updateConfig('stroke_color', preset.stroke)
            }}
            className="p-2.5 rounded-xl border border-white/5 bg-white/[0.02] hover:bg-white/[0.06] hover:border-white/10 transition-all text-center group"
          >
            <div className="flex justify-center gap-1 mb-1.5">
              <div className="w-4 h-4 rounded-full ring-1 ring-white/10" style={{ backgroundColor: preset.primary }} />
              <div className="w-4 h-4 rounded-full ring-1 ring-white/10" style={{ backgroundColor: preset.highlight }} />
              <div className="w-4 h-4 rounded-full ring-1 ring-white/10" style={{ backgroundColor: preset.stroke }} />
            </div>
            <div className="text-[10px] text-gray-500 group-hover:text-gray-300 transition-colors">{preset.name}</div>
          </button>
        ))}
      </div>

      {/* Custom color pickers */}
      <div className="grid grid-cols-3 gap-4">
        <div className="glass-card p-3 !rounded-xl">
          <label className="text-[10px] text-gray-500 block mb-2">Text Color</label>
          <div className="flex items-center gap-2">
            <input
              type="color"
              value={config.primary_color || '#FFFFFF'}
              onChange={e => updateConfig('primary_color', e.target.value)}
              className="w-9 h-9 rounded-lg border border-white/20 cursor-pointer bg-transparent"
            />
            <input
              type="text"
              value={config.primary_color || '#FFFFFF'}
              onChange={e => updateConfig('primary_color', e.target.value)}
              className="flex-1 px-2 py-1.5 rounded-lg bg-white/5 border border-white/10 text-white text-xs font-mono focus:outline-none focus:border-spacex-accent/50"
            />
          </div>
        </div>

        <div className="glass-card p-3 !rounded-xl">
          <label className="text-[10px] text-gray-500 block mb-2">Highlight</label>
          <div className="flex items-center gap-2">
            <input
              type="color"
              value={config.highlight_color || '#FFD700'}
              onChange={e => updateConfig('highlight_color', e.target.value)}
              className="w-9 h-9 rounded-lg border border-white/20 cursor-pointer bg-transparent"
            />
            <input
              type="text"
              value={config.highlight_color || '#FFD700'}
              onChange={e => updateConfig('highlight_color', e.target.value)}
              className="flex-1 px-2 py-1.5 rounded-lg bg-white/5 border border-white/10 text-white text-xs font-mono focus:outline-none focus:border-spacex-accent/50"
            />
          </div>
        </div>

        <div className="glass-card p-3 !rounded-xl">
          <label className="text-[10px] text-gray-500 block mb-2">Stroke</label>
          <div className="flex items-center gap-2">
            <input
              type="color"
              value={config.stroke_color || '#000000'}
              onChange={e => updateConfig('stroke_color', e.target.value)}
              className="w-9 h-9 rounded-lg border border-white/20 cursor-pointer bg-transparent"
            />
            <input
              type="text"
              value={config.stroke_color || '#000000'}
              onChange={e => updateConfig('stroke_color', e.target.value)}
              className="flex-1 px-2 py-1.5 rounded-lg bg-white/5 border border-white/10 text-white text-xs font-mono focus:outline-none focus:border-spacex-accent/50"
            />
          </div>
        </div>
      </div>
    </div>
  )
}
