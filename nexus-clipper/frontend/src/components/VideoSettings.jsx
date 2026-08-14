import React from 'react'

const RATIOS = [
  { id: '9:16', label: '9:16', desc: 'TikTok / Shorts', icon: '📱' },
  { id: '1:1', label: '1:1', desc: 'Instagram Feed', icon: '◻️' },
  { id: '16:9', label: '16:9', desc: 'YouTube Wide', icon: '🖥️' },
  { id: '4:5', label: '4:5', desc: 'IG Portrait', icon: '📲' },
]

export default function VideoSettings({ config, updateConfig }) {
  return (
    <div className="glass-card p-5 space-y-5">
      <div className="flex items-center gap-2">
        <span className="text-lg">🎬</span>
        <h3 className="text-sm font-semibold text-gray-200">Video Settings</h3>
        <span className="badge badge-info ml-auto">8 options</span>
      </div>

      <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
        {/* Aspect Ratio */}
        <div className="glass-card p-4 col-span-2 md:col-span-1">
          <label className="text-[10px] text-gray-500 block mb-3">Aspect Ratio</label>
          <div className="grid grid-cols-2 gap-2">
            {RATIOS.map(r => {
              const isActive = config.aspect_ratio === r.id
              return (
                <button key={r.id}
                  onClick={() => updateConfig('aspect_ratio', r.id)}
                  className={`p-2.5 rounded-xl border text-center transition-all ${
                    isActive
                      ? 'border-spacex-accent bg-spacex-accent/5 text-white'
                      : 'border-white/5 bg-white/[0.02] text-gray-500 hover:border-white/10'
                  }`}
                >
                  <div className="text-lg mb-0.5">{r.icon}</div>
                  <div className="text-[10px] font-semibold">{r.label}</div>
                  <div className="text-[8px] opacity-50">{r.desc}</div>
                </button>
              )
            })}
          </div>
        </div>

        {/* Clip Duration */}
        <div className="glass-card p-4">
          <label className="text-[10px] text-gray-500 block mb-2">
            Clip Duration: <span className="text-spacex-accent">{config.target_duration}s</span>
          </label>
          <input type="range" min={15} max={180} step={5}
            value={config.target_duration} onChange={e => updateConfig('target_duration', Number(e.target.value))}
            className="w-full"
          />
          <div className="flex justify-between text-[9px] text-gray-700 mt-1">
            <span>15s</span><span>60s</span><span>180s</span>
          </div>
        </div>

        {/* Clips Count */}
        <div className="glass-card p-4">
          <label className="text-[10px] text-gray-500 block mb-2">
            Clips to Generate: <span className="text-spacex-accent">{config.clip_count}</span>
          </label>
          <input type="range" min={1} max={10}
            value={config.clip_count} onChange={e => updateConfig('clip_count', Number(e.target.value))}
            className="w-full"
          />
          <div className="flex justify-between text-[9px] text-gray-700 mt-1">
            <span>1</span><span>5</span><span>10</span>
          </div>
        </div>

        {/* Language */}
        <div className="glass-card p-4">
          <label className="text-[10px] text-gray-500 block mb-2">Language</label>
          <select
            value={config.language || ''}
            onChange={e => updateConfig('language', e.target.value || null)}
            className="w-full px-3 py-2 rounded-lg bg-white/5 border border-white/10 text-white text-sm focus:outline-none focus:border-spacex-accent/50"
          >
            <option value="">Auto-detect</option>
            <option value="en">English</option>
            <option value="id">Indonesian</option>
            <option value="es">Spanish</option>
            <option value="fr">French</option>
            <option value="de">German</option>
            <option value="pt">Portuguese</option>
            <option value="ja">Japanese</option>
            <option value="ko">Korean</option>
          </select>
        </div>
      </div>

      {/* Toggles row */}
      <div className="grid grid-cols-2 gap-3">
        <label className="glass-card p-3 flex items-center justify-between cursor-pointer">
          <div>
            <p className="text-xs font-medium text-gray-300">Auto Zoom</p>
            <p className="text-[9px] text-gray-600">Face-tracking auto zoom</p>
          </div>
          <button
            onClick={(e) => { e.preventDefault(); updateConfig('auto_zoom', !config.auto_zoom) }}
            className={`w-11 h-6 rounded-full transition-all relative ${
              config.auto_zoom ? 'bg-spacex-accent' : 'bg-white/10'
            }`}
          >
            <div className={`w-4 h-4 rounded-full bg-white absolute top-1 shadow-md transition-transform ${
              config.auto_zoom ? 'translate-x-[22px]' : 'translate-x-[2px]'
            }`} />
          </button>
        </label>

        <label className="glass-card p-3 flex items-center justify-between cursor-pointer">
          <div>
            <p className="text-xs font-medium text-gray-300">Face Tracking</p>
            <p className="text-[9px] text-gray-600">Detect & follow speaker</p>
          </div>
          <button
            onClick={(e) => { e.preventDefault(); updateConfig('face_tracking', !config.face_tracking) }}
            className={`w-11 h-6 rounded-full transition-all relative ${
              config.face_tracking !== false ? 'bg-spacex-accent' : 'bg-white/10'
            }`}
          >
            <div className={`w-4 h-4 rounded-full bg-white absolute top-1 shadow-md transition-transform ${
              config.face_tracking !== false ? 'translate-x-[22px]' : 'translate-x-[2px]'
            }`} />
          </button>
        </label>
      </div>
    </div>
  )
}
