import React, { useState } from 'react';
import './NexusX.css';

const SUBTITLE_STYLES = [
  { id: "hormozi", icon: "💛", name: "Hormozi", desc: "Kata per kata, highlight kuning" },
  { id: "mrbeast", icon: "🦁", name: "MrBeast", desc: "Tebal, dinamis" },
  { id: "aliabdaal", icon: "✨", name: "Ali Abdaal", desc: "Elegan, bersih" },
  { id: "minimalist", icon: "🤍", name: "Minimalist", desc: "Kecil putih" },
  { id: "gaming", icon: "🎮", name: "Gaming", desc: "Bold, kontras" },
  { id: "cinematic", icon: "🎬", name: "Cinematic", desc: "Lebar, fade" },
  { id: "neon", icon: "💜", name: "Neon", desc: "Glow effect" },
  { id: "typewriter", icon: "⌨️", name: "Typewriter", desc: "Huruf satu-satu" },
  { id: "tiktok_viral", icon: "🔥", name: "TikTok Viral", desc: "Acak, cerah" },
  { id: "documentary", icon: "📜", name: "Documentary", desc: "Serif, bawah" },
  { id: "comedy", icon: "😂", name: "Comedy", desc: "Bouncy" },
  { id: "horror", icon: "👻", name: "Horror", desc: "Flicker, merah" },
  { id: "motivational", icon: "💪", name: "Motivational", desc: "Bold, slow" },
  { id: "educational", icon: "📚", name: "Educational", desc: "Top, highlight" },
  { id: "custom", icon: "🎨", name: "Custom", desc: "Atur sendiri" },
];

const FONTS = ['Arial','Impact','Helvetica','Georgia','Verdana','Trebuchet MS','Comic Sans MS','Courier New','Tahoma','Times New Roman'];
const ANIMATIONS = ['pop','fade','slide_up','none'];
const POSITIONS = ['top','center','bottom'];
const ASPECT_RATIOS = [
  { id:"9:16", label:"9:16", icon:"📱", desc:"TikTok" },
  { id:"1:1", label:"1:1", icon:"◻️", desc:"IG Feed" },
  { id:"16:9", label:"16:9", icon:"🖥️", desc:"YouTube" },
  { id:"4:5", label:"4:5", icon:"📲", desc:"IG Portrait" },
];
const COLOR_PRESETS = [
  { name:"Default",p:"#FFFFFF",h:"#FFD700",s:"#000000" },
  { name:"Neon Gold",p:"#FFD700",h:"#FFA000",s:"#000000" },
  { name:"Fire Red",p:"#FF4444",h:"#FFD600",s:"#8B0000" },
  { name:"Ocean Blue",p:"#00E5FF",h:"#00FF88",s:"#003344" },
  { name:"Purple Haze",p:"#E040FB",h:"#FFD700",s:"#4A0072" },
  { name:"Mint Green",p:"#69F0AE",h:"#FFFF00",s:"#1B5E20" },
  { name:"Coral",p:"#FF8A80",h:"#FFEA00",s:"#B71C1C" },
  { name:"Ice",p:"#82B1FF",h:"#FFD700",s:"#0D47A1" },
];

export default function NexusXLab({ config, setConfig, onGenerate, generating, url }) {
  const [activeTab, setActiveTab] = useState('style');
  const u = (key, val) => setConfig(prev => ({ ...prev, [key]: val }));

  const tabs = [
    { id:'style', label:'🎨 Styles', count: SUBTITLE_STYLES.length },
    { id:'text', label:'🔤 Text', count: '10+' },
    { id:'colors', label:'🌈 Colors', count: COLOR_PRESETS.length },
    { id:'video', label:'🎬 Video', count: '8+' },
  ];

  return (
    <section className="nx-lab">
      <h2>🧪 Customization <span style={{color:'#6366f1'}}>Lab</span></h2>

      {/* Tabs */}
      <div className="nx-lab-tabs">
        {tabs.map(t => (
          <button key={t.id} className={`nx-lab-tab ${activeTab===t.id?'active':''}`}
            onClick={() => setActiveTab(activeTab===t.id?'':t.id)}>
            {t.label}
          </button>
        ))}
      </div>

      {/* ── STYLE ── */}
      {activeTab === 'style' && (
        <div className="nx-lab-grid">
          {SUBTITLE_STYLES.map(s => (
            <div key={s.id}
              className={`nx-style-card ${config.subtitle_style===s.id?'selected':''}`}
              onClick={() => u('subtitle_style', s.id)}>
              <div className="icon">{s.icon}</div>
              <div className="name">{s.name}</div>
              <div className="desc">{s.desc}</div>
            </div>
          ))}
        </div>
      )}

      {/* ── TEXT ── */}
      {activeTab === 'text' && (
        <div>
          <div className="nx-settings-row">
            <div className="nx-setting">
              <label>Font</label>
              <select value={config.font} onChange={e => u('font', e.target.value)}>
                {FONTS.map(f => <option key={f}>{f}</option>)}
              </select>
            </div>
            <div className="nx-setting">
              <label>Size: {config.font_size}px</label>
              <input type="range" min={24} max={96} value={config.font_size}
                onChange={e => u('font_size', Number(e.target.value))} />
            </div>
            <div className="nx-setting">
              <label>Position</label>
              <select value={config.position} onChange={e => u('position', e.target.value)}>
                {POSITIONS.map(p => <option key={p}>{p}</option>)}
              </select>
            </div>
            <div className="nx-setting">
              <label>Animation</label>
              <select value={config.animation} onChange={e => u('animation', e.target.value)}>
                {ANIMATIONS.map(a => <option key={a}>{a}</option>)}
              </select>
            </div>
          </div>
          <div className="nx-setting">
            <label>Stroke: {config.stroke_width}px</label>
            <input type="range" min={0} max={10} value={config.stroke_width}
              onChange={e => u('stroke_width', Number(e.target.value))} />
          </div>
        </div>
      )}

      {/* ── COLORS ── */}
      {activeTab === 'colors' && (
        <div>
          <div className="nx-color-row">
            {COLOR_PRESETS.map(p => (
              <div key={p.name} className="nx-color-preset"
                onClick={() => { u('primary_color',p.p); u('highlight_color',p.h); u('stroke_color',p.s); }}>
                <div className="dot" style={{background:p.p}} />
                <div className="dot" style={{background:p.h}} />
                <div className="dot" style={{background:p.s}} />
                <span className="name">{p.name}</span>
              </div>
            ))}
          </div>
          <div className="nx-settings-row">
            {['primary_color','highlight_color','stroke_color'].map(key => (
              <div className="nx-setting" key={key}>
                <label>{key.replace('_',' ')}</label>
                <div style={{display:'flex',gap:8,alignItems:'center'}}>
                  <input type="color" value={config[key]} onChange={e => u(key, e.target.value)}
                    style={{width:36,height:36,borderRadius:8,border:'1px solid rgba(255,255,255,0.2)',cursor:'pointer'}} />
                  <input type="text" value={config[key]} onChange={e => u(key, e.target.value)}
                    style={{flex:1,padding:'8px',borderRadius:'var(--nx-radius)',border:'1px solid var(--nx-border)',
                      background:'var(--nx-deep)',color:'#fff',fontSize:'0.75rem',fontFamily:'monospace'}} />
                </div>
              </div>
            ))}
          </div>
        </div>
      )}

      {/* ── VIDEO ── */}
      {activeTab === 'video' && (
        <div>
          <div className="nx-lab-grid" style={{gridTemplateColumns:'repeat(auto-fill, minmax(120px, 1fr))'}}>
            {ASPECT_RATIOS.map(r => (
              <div key={r.id} className={`nx-style-card ${config.aspect_ratio===r.id?'selected':''}`}
                onClick={() => u('aspect_ratio', r.id)}>
                <div className="icon">{r.icon}</div>
                <div className="name">{r.label}</div>
                <div className="desc">{r.desc}</div>
              </div>
            ))}
          </div>
          <div className="nx-settings-row">
            <div className="nx-setting">
              <label>Duration: {config.target_duration}s</label>
              <input type="range" min={15} max={180} step={5} value={config.target_duration}
                onChange={e => u('target_duration', Number(e.target.value))} />
            </div>
            <div className="nx-setting">
              <label>Clips: {config.clip_count}</label>
              <input type="range" min={1} max={10} value={config.clip_count}
                onChange={e => u('clip_count', Number(e.target.value))} />
            </div>
            <div className="nx-setting">
              <label>Language</label>
              <select value={config.language} onChange={e => u('language', e.target.value)}>
                <option value="">Auto Detect</option>
                <option value="en">English</option><option value="id">Indonesian</option>
                <option value="es">Spanish</option><option value="fr">French</option>
                <option value="pt">Portuguese</option><option value="ja">Japanese</option>
                <option value="ko">Korean</option>
              </select>
            </div>
          </div>

          {/* Advanced toggles */}
          <div style={{marginTop:16}}>
            {[
              { key:'face_tracking', label:'Face Tracking & Auto-Zoom', desc:'MediaPipe AI — smooth zoom to speaker face', icon:'👤' },
              { key:'diarization', label:'Multi-Speaker Detection', desc:'Each speaker gets unique subtitle color', icon:'🎙️' },
              { key:'dynamic_subtitle_position', label:'Dynamic Subtitle Position', desc:'Subtitles follow speaker automatically', icon:'🎯' },
            ].map(t => (
              <div key={t.key} className="nx-toggle" onClick={() => u(t.key, !config[t.key])}>
                <div>
                  <div className="label">{t.icon} {t.label}</div>
                  <div className="desc">{t.desc}</div>
                </div>
                <div className={`nx-toggle-switch ${config[t.key] ? 'on' : ''}`} />
              </div>
            ))}
          </div>
        </div>
      )}

      {/* Generate CTA */}
      <div style={{marginTop:32, textAlign:'center'}}>
        <button className="nx-input-btn"
          onClick={onGenerate}
          disabled={generating || !url.trim()}
          style={{padding:'18px 48px', fontSize:'1rem'}}>
          {generating ? '⏳ PROCESSING...' : '🚀 Generate Clips Now'}
        </button>
      </div>
    </section>
  );
}
