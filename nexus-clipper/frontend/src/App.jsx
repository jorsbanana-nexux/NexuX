import React, { useState } from 'react'
import { motion, AnimatePresence } from 'framer-motion'
import Header from './components/Header.jsx'
import URLInput from './components/URLInput.jsx'
import StyleSelector from './components/StyleSelector.jsx'
import ColorCustomizer from './components/ColorCustomizer.jsx'
import TextSettings from './components/TextSettings.jsx'
import VideoSettings from './components/VideoSettings.jsx'
import ProgressPanel from './components/ProgressPanel.jsx'
import OutputPreview from './components/OutputPreview.jsx'
import EditorWizard from './components/EditorWizard.jsx'
import ClipsDashboard from './components/ClipsDashboard.jsx'

export default function App() {
  const [youtubeUrl, setYoutubeUrl] = useState('')
  const [jobStatus, setJobStatus] = useState(null)
  const [activeSection, setActiveSection] = useState('style')
  const [showEditor, setShowEditor] = useState(false)
  const [showDashboard, setShowDashboard] = useState(false)
  const [editorClip, setEditorClip] = useState(null)

  const [styleConfig, setStyleConfig] = useState({
    subtitle_style: 'hormozi',
    font: '',
    font_size: 48,
    primary_color: '',
    highlight_color: '',
    stroke_color: '',
    stroke_width: 3,
    position: '',
    animation: '',
    highlight_active_word: true,
    auto_zoom: true,
    aspect_ratio: '9:16',
    clip_count: 3,
    target_duration: 60,
    language: '',
    layout: 'fill',
    noise_removal: false,
    bgm_ducking: false,
    broll_insert: false,
    bgm_volume: -16,
  })

  const updateConfig = (key, value) => {
    setStyleConfig(prev => ({ ...prev, [key]: value }))
  }

  const activeConfig = () => {
    const clean = {}
    for (const [k, v] of Object.entries(styleConfig)) {
      if (v !== '' && v !== null) clean[k] = v
    }
    return clean
  }

  return (
    <div className="min-h-screen bg-[#07080B] text-[#E4E4E7]">
      <div className="fixed inset-0 overflow-hidden pointer-events-none">
        <div className="absolute inset-0 bg-[radial-gradient(ellipse_80%_60%_at_50%_0%,rgba(204,255,0,0.04),transparent_60%)]" />
        <div className="absolute inset-0 bg-[radial-gradient(ellipse_60%_50%_at_100%_50%,rgba(0,240,255,0.03),transparent_60%)]" />
        <div className="absolute inset-0 bg-[radial-gradient(ellipse_40%_40%_at_0%_100%,rgba(168,85,247,0.04),transparent_60%)]" />
        <div className="absolute inset-0 opacity-[0.015]" style={{ backgroundImage: 'radial-gradient(circle, rgba(255,255,255,0.5) 1px, transparent 1px)', backgroundSize: '32px 32px' }} />
      </div>

      <div className="relative z-10 max-w-7xl mx-auto px-4 py-6">
        <Header jobStatus={jobStatus} />
        <div className="grid grid-cols-1 lg:grid-cols-3 gap-6 mt-6">
          <div className="lg:col-span-1 space-y-4">
            <URLInput url={youtubeUrl} setUrl={setYoutubeUrl} config={activeConfig()} setJobStatus={setJobStatus} />
            <AnimatePresence>{jobStatus && <motion.div initial={{ opacity: 0, y: 10 }} animate={{ opacity: 1, y: 0 }} exit={{ opacity: 0, y: -10 }}><ProgressPanel jobStatus={jobStatus} /></motion.div>}</AnimatePresence>
            {jobStatus?.status === 'completed' && !showDashboard && !showEditor && <motion.div initial={{ opacity: 0, y: 10 }} animate={{ opacity: 1, y: 0 }} className="glass-card p-4 text-center"><p className="text-sm text-spacex-success mb-2">✓ Clip siap! Lihat semua klip:</p><button onClick={() => setShowDashboard(true)} className="btn-primary text-sm">🎬 View All Clips</button></motion.div>}
          </div>

          <div className="lg:col-span-2 space-y-4">
            <div className="flex gap-2 flex-wrap">{[
              { id: 'style', label: '🎨 Styles', count: '15 presets' },
              { id: 'text', label: '🔤 Text', count: '10 options' },
              { id: 'colors', label: '🌈 Colors', count: '8 palettes' },
              { id: 'video', label: '🎬 Video', count: '8 settings' },
            ].map(tab => <button key={tab.id} onClick={() => setActiveSection(activeSection === tab.id ? '' : tab.id)} className={`tab-btn ${activeSection === tab.id ? 'active' : ''}`}>{tab.label}<span className="ml-1.5 text-[10px] opacity-40">{tab.count}</span></button>)}</div>

            <AnimatePresence mode="wait">
              {activeSection === 'style' && <motion.div key="style" initial={{ opacity: 0, y: 8 }} animate={{ opacity: 1, y: 0 }} exit={{ opacity: 0, y: -8 }} transition={{ duration: 0.2 }}><StyleSelector config={styleConfig} updateConfig={updateConfig} /></motion.div>}
              {activeSection === 'text' && <motion.div key="text" initial={{ opacity: 0, y: 8 }} animate={{ opacity: 1, y: 0 }} exit={{ opacity: 0, y: -8 }} transition={{ duration: 0.2 }}><TextSettings config={styleConfig} updateConfig={updateConfig} /></motion.div>}
              {activeSection === 'colors' && <motion.div key="colors" initial={{ opacity: 0, y: 8 }} animate={{ opacity: 1, y: 0 }} exit={{ opacity: 0, y: -8 }} transition={{ duration: 0.2 }}><ColorCustomizer config={styleConfig} updateConfig={updateConfig} /></motion.div>}
              {activeSection === 'video' && <motion.div key="video" initial={{ opacity: 0, y: 8 }} animate={{ opacity: 1, y: 0 }} exit={{ opacity: 0, y: -8 }} transition={{ duration: 0.2 }}><VideoSettings config={styleConfig} updateConfig={updateConfig} /></motion.div>}
            </AnimatePresence>

            <AnimatePresence>{jobStatus?.output_path && <motion.div initial={{ opacity: 0, y: 20 }} animate={{ opacity: 1, y: 0 }} transition={{ delay: 0.2 }}><OutputPreview outputPath={jobStatus.output_path} onViewClips={() => setShowDashboard(true)} onCustomize={() => { setEditorClip(null); setShowEditor(true) }} /></motion.div>}</AnimatePresence>
          </div>
        </div>
      </div>

      <AnimatePresence>{showDashboard && <ClipsDashboard clips={jobStatus?.clips || []} onCustomize={(clip) => { setShowDashboard(false); setEditorClip(clip); setShowEditor(true) }} onClose={() => setShowDashboard(false)} />}</AnimatePresence>
      <AnimatePresence>{showEditor && <EditorWizard config={styleConfig} updateConfig={updateConfig} onClose={() => setShowEditor(false)} />}</AnimatePresence>
    </div>
  )
}
