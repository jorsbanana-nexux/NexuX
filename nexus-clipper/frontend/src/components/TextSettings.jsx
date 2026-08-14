import React from 'react'

const FONTS = [
  'Arial', 'Impact', 'Helvetica', 'Georgia', 'Verdana',
  'Trebuchet MS', 'Comic Sans MS', 'Courier New', 'Tahoma', 'Times New Roman',
]

const POSITIONS = [
  { id: 'top', label: 'Atas' },
  { id: 'center', label: 'Tengah' },
  { id: 'bottom', label: 'Bawah' },
]

const ANIMATIONS = [
  { id: 'pop', label: 'Pop-up' },
  { id: 'pop_fast', label: 'Pop Fast' },
  { id: 'fade', label: 'Fade In' },
  { id: 'fade_slow', label: 'Fade Slow' },
  { id: 'bounce', label: 'Bounce' },
  { id: 'flicker', label: 'Flicker' },
  { id: 'slow_reveal', label: 'Slow Reveal' },
  { id: 'typewriter', label: 'Typewriter' },
  { id: 'none', label: 'None' },
]

export default function TextSettings({ config, updateConfig }) {
  return (
    <div className="glass-card p-5 space-y-5">
      <div className="flex items-center gap-2">
        <span className="text-lg">🔤</span>
        <h3 className="text-sm font-semibold text-gray-200">Text Settings</h3>
        <span className="badge badge-info ml-auto">10 fonts</span>
      </div>

      <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
        {/* Font */}
        <div className="glass-card p-3 !rounded-xl">
          <label className="text-[10px] text-gray-500 block mb-2">Font</label>
          <select
            value={config.font || 'Arial'}
            onChange={e => updateConfig('font', e.target.value)}
            className="w-full px-3 py-2 rounded-lg bg-white/5 border border-white/10 text-white text-sm focus:outline-none focus:border-spacex-accent/50"
          >
            {FONTS.map(f => <option key={f} value={f}>{f}</option>)}
          </select>
        </div>

        {/* Font Size */}
        <div className="glass-card p-3 !rounded-xl">
          <label className="text-[10px] text-gray-500 block mb-2">
            Font Size: <span className="text-spacex-accent">{config.font_size}px</span>
          </label>
          <input type="range" min={24} max={96}
            value={config.font_size} onChange={e => updateConfig('font_size', Number(e.target.value))}
            className="w-full"
          />
          <div className="flex justify-between text-[9px] text-gray-700 mt-0.5">
            <span>24</span><span>60</span><span>96</span>
          </div>
        </div>

        {/* Position */}
        <div className="glass-card p-3 !rounded-xl">
          <label className="text-[10px] text-gray-500 block mb-2">Position</label>
          <div className="flex gap-1">
            {POSITIONS.map(p => (
              <button key={p.id}
                onClick={() => updateConfig('position', p.id)}
                className={`flex-1 py-2 rounded-lg text-xs font-medium transition-all ${
                  config.position === p.id
                    ? 'bg-spacex-accent/10 border border-spacex-accent/30 text-spacex-accent'
                    : 'bg-white/5 border border-white/5 text-gray-500 hover:border-white/10'
                }`}
              >{p.label}</button>
            ))}
          </div>
        </div>

        {/* Animation */}
        <div className="glass-card p-3 !rounded-xl">
          <label className="text-[10px] text-gray-500 block mb-2">Animation</label>
          <select
            value={config.animation || 'pop'}
            onChange={e => updateConfig('animation', e.target.value)}
            className="w-full px-3 py-2 rounded-lg bg-white/5 border border-white/10 text-white text-sm focus:outline-none focus:border-spacex-accent/50"
          >
            {ANIMATIONS.map(a => <option key={a.id} value={a.id}>{a.label}</option>)}
          </select>
        </div>
      </div>

      {/* Stroke width */}
      <div className="glass-card p-4">
        <label className="text-xs text-gray-500 block mb-1">
          Stroke Width (Outline): <span className="text-spacex-accent">{config.stroke_width}px</span>
        </label>
        <input type="range" min={0} max={10}
          value={config.stroke_width} onChange={e => updateConfig('stroke_width', Number(e.target.value))}
          className="w-full"
        />
        <div className="flex justify-between text-[10px] text-gray-700 mt-1">
          <span>None</span><span>Thin</span><span>Med</span><span>Thick</span>
        </div>
      </div>
    </div>
  )
}
