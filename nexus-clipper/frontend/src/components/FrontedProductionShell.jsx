import React, { useEffect, useState } from 'react'
import Header from './Header.jsx'
import URLInput from './URLInput.jsx'
import StyleSelector from './StyleSelector.jsx'
import ColorCustomizer from './ColorCustomizer.jsx'
import TextSettings from './TextSettings.jsx'
import VideoSettings from './VideoSettings.jsx'
import ProgressPanel from './ProgressPanel.jsx'
import OutputPreview from './OutputPreview.jsx'

export default function FrontedProductionShell() {
  const [url, setUrl] = useState('')
  const [jobStatus, setJobStatus] = useState(null)
  const [activeSection, setActiveSection] = useState('style')
  const [config, setConfig] = useState({
    subtitle_style: 'hormozi', font: 'Arial', font_size: 48,
    primary_color: '#FFFFFF', highlight_color: '#FFD700', stroke_color: '#000000',
    stroke_width: 3, position: 'center', animation: 'pop', auto_zoom: true,
    face_tracking: true, aspect_ratio: '9:16', clip_count: 3, target_duration: 45,
    language: null, normalize_audio: true, emoji_enabled: true,
  })
  const updateConfig = (key, value) => setConfig(prev => ({ ...prev, [key]: value }))

  useEffect(() => {
    document.documentElement.dataset.nexux = 'fronted-production'
    return () => { delete document.documentElement.dataset.nexux }
  }, [])

  return (
    <div className="min-h-screen bg-[#03050a] text-white relative overflow-hidden">
      <div className="fixed inset-0 pointer-events-none bg-[radial-gradient(circle_at_50%_-10%,rgba(34,211,238,.18),transparent_45%),radial-gradient(circle_at_100%_100%,rgba(168,85,247,.12),transparent_35%)]" />
      <div className="fixed inset-0 pointer-events-none opacity-[.025] bg-[linear-gradient(rgba(255,255,255,.4)_1px,transparent_1px),linear-gradient(90deg,rgba(255,255,255,.4)_1px,transparent_1px)] bg-[size:32px_32px]" />
      <main className="relative z-10 max-w-7xl mx-auto px-4 py-6">
        <Header jobStatus={jobStatus} />
        <section className="mt-6 rounded-3xl border border-cyan-400/10 bg-black/35 backdrop-blur-xl p-5 shadow-[0_0_80px_rgba(34,211,238,.08)]">
          <div className="mb-5">
            <div className="text-xs font-mono tracking-[.35em] text-cyan-300/70">NEXUX // FRONTED PRODUCTION CONSOLE</div>
            <h1 className="text-3xl md:text-5xl font-black mt-2">Turn long-form video into ready-to-publish clips.</h1>
            <p className="text-sm text-stone-400 mt-2 max-w-2xl">Every control below is an instruction to the NexuX rendering engine.</p>
          </div>
          <div className="grid grid-cols-1 xl:grid-cols-3 gap-5">
            <div className="space-y-4"><URLInput url={url} setUrl={setUrl} config={config} setJobStatus={setJobStatus}/>{jobStatus && <ProgressPanel jobStatus={jobStatus}/>}</div>
            <div className="xl:col-span-2 space-y-4">
              <div className="flex flex-wrap gap-2">{[['style','Styles'],['text','Subtitles'],['colors','Colors'],['video','Video']].map(([id,label]) => <button key={id} onClick={() => setActiveSection(id)} className={`tab-btn ${activeSection===id?'active':''}`}>{label}</button>)}</div>
              {activeSection==='style' && <StyleSelector config={config} updateConfig={updateConfig}/>} 
              {activeSection==='text' && <TextSettings config={config} updateConfig={updateConfig}/>} 
              {activeSection==='colors' && <ColorCustomizer config={config} updateConfig={updateConfig}/>} 
              {activeSection==='video' && <VideoSettings config={config} updateConfig={updateConfig}/>} 
              {jobStatus?.output_path && <OutputPreview outputPath={jobStatus.output_path} onViewClips={() => {}} onCustomize={() => setActiveSection('style')}/>} 
            </div>
          </div>
        </section>
      </main>
    </div>
  )
}
