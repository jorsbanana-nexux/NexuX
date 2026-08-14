import React, { useState, useEffect, useRef } from 'react';
import './NexusX.css';
import NexusXLab from './NexusXLab';

const STAGES = ['downloading', 'face_tracking', 'transcribing', 'analyzing', 'rendering', 'completed'];
const STAGE_LABELS = {
  downloading: 'Download', face_tracking: 'Face Track', transcribing: 'Transcribe',
  analyzing: 'Analyze', rendering: 'Render', completed: 'Complete'
};
const STAGE_ICONS = {
  downloading: '⬇️', face_tracking: '👤', transcribing: '🎙️',
  analyzing: '🔍', rendering: '🎬', completed: '✅'
};

const FEATURES = [
  { icon: '🎯', title: 'AI Smart Clipping', desc: 'Whisper AI analyzes your video, finds the most viral-worthy moments, and extracts them automatically.' },
  { icon: '👤', title: 'Face Tracking Auto-Zoom', desc: 'MediaPipe AI tracks speaker faces and smoothly zooms to keep them perfectly framed — Opus Clip style.' },
  { icon: '🎨', title: '15+ Caption Styles', desc: 'Hormozi, MrBeast, TikTok Viral, Neon, Cinematic — professional captions that boost watch time 300%.' },
  { icon: '🎙️', title: 'Multi-Speaker Detection', desc: 'WhisperX diarization identifies every speaker. Each gets unique subtitle colors automatically.' },
  { icon: '⚡', title: 'Real FFmpeg Render', desc: 'H.264 + AAC encoding. No simulation. Your video is actually rendered with all effects applied.' },
  { icon: '🆓', title: '100% Free Forever', desc: 'No API keys, no subscriptions, no limits. Everything runs locally on your machine.' },
];

export default function NexusX() {
  const [url, setUrl] = useState('');
  const [generating, setGenerating] = useState(false);
  const [job, setJob] = useState(null);
  const [jobId, setJobId] = useState('');
  const [showLab, setShowLab] = useState(false);
  const [config, setConfig] = useState({
    subtitle_style: 'hormozi', font: 'Arial', font_size: 48,
    primary_color: '#FFFFFF', highlight_color: '#FFD700', stroke_color: '#000000',
    stroke_width: 3, position: 'center', animation: 'pop',
    auto_zoom: true, aspect_ratio: '9:16', clip_count: 3, target_duration: 60,
    language: '', face_tracking: true, dynamic_subtitle_position: true, diarization: false,
  });
  const pollRef = useRef(null);
  const labRef = useRef(null);

  useEffect(() => () => { if (pollRef.current) clearInterval(pollRef.current); }, []);

  const handleGenerate = async () => {
    if (!url.trim()) return;
    setGenerating(true);
    setJob({ status: 'queued', progress: 0, stage: 'queued' });
    setShowLab(false);

    try {
      const res = await fetch('/api/generate', {
        method: 'POST', headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ youtube_url: url, ...config }),
      });
      if (!res.ok) throw new Error(await res.text());
      const { job_id } = await res.json();
      setJobId(job_id);

      let attempts = 0;
      pollRef.current = setInterval(async () => {
        try {
          const jr = await fetch(`/api/job/${job_id}`);
          const j = await jr.json();
          setJob(j);
          attempts++;
          if (j.status === 'completed' || j.status === 'failed' || attempts > 600) {
            clearInterval(pollRef.current);
            setGenerating(false);
          }
        } catch {
          if (++attempts > 30) { clearInterval(pollRef.current); setGenerating(false); }
        }
      }, 1000);
    } catch (e) {
      setJob({ status: 'failed', error: e.message });
      setGenerating(false);
    }
  };

  const scrollToLab = () => {
    setShowLab(true);
    setTimeout(() => labRef.current?.scrollIntoView({ behavior: 'smooth' }), 100);
  };

  const currentStageIdx = STAGES.indexOf(job?.stage || '');
  const progress = job?.progress || 0;

  return (
    <div>
      {/* ─── STARFIELD BG ─── */}
      <div className="nx-starfield" />

      {/* ─── NAV ─── */}
      <nav className="nx-nav">
        <div className="nx-nav-logo">
          <svg width="28" height="28" viewBox="0 0 28 28" fill="none">
            <path d="M14 2L25 22H3L14 2Z" fill="url(#nxGrad)" />
            <defs><linearGradient id="nxGrad" x1="0" y1="0" x2="28" y2="28">
              <stop stopColor="#6366f1"/><stop offset="1" stopColor="#ec4899"/>
            </linearGradient></defs>
          </svg>
          NEXUS<span style={{fontWeight:300}}>X</span>
        </div>
        <div className="nx-nav-links">
          <a href="#" className="nx-nav-link">Features</a>
          <a href="#" className="nx-nav-link" onClick={(e) => { e.preventDefault(); scrollToLab(); }}>Lab</a>
          <a href="#" className="nx-nav-link">Docs</a>
          <button className="nx-nav-cta" onClick={scrollToLab}>Open Lab →</button>
        </div>
      </nav>

      {/* ─── HERO ─── */}
      <section className="nx-hero">
        <div className="nx-hero-badge">
          <div className="nx-hero-badge-dot" />
          AI VIDEO CLIPPING — v2.0
        </div>
        <h1 className="nx-hero-title">
          1 long video.<br /><span>10 viral clips.</span>
        </h1>
        <p className="nx-hero-sub">
          NexusX turns any YouTube video into TikTok-ready viral shorts — 
          with AI face tracking, smart captions, and cinematic rendering. All free.
        </p>

        {/* INPUT (Opus Clip style) */}
        <div className="nx-input-group">
          <input
            type="text"
            value={url}
            onChange={e => setUrl(e.target.value)}
            placeholder="Paste YouTube link here..."
            disabled={generating}
            onKeyDown={e => e.key === 'Enter' && handleGenerate()}
          />
          <button className="nx-input-btn" onClick={handleGenerate} disabled={generating || !url.trim()}>
            {generating ? 'PROCESSING...' : 'Generate Clips →'}
          </button>
        </div>
        <div className="nx-input-platforms">
          Supports <span>YouTube</span> · <span>Google Drive</span> · <span>Vimeo</span> · <span>Twitch</span> — and more coming
        </div>

        {/* STATS */}
        <div className="nx-stats">
          <div className="nx-stat">
            <div className="nx-stat-num">15+</div>
            <div className="nx-stat-label">Caption Styles</div>
          </div>
          <div className="nx-stat">
            <div className="nx-stat-num">100%</div>
            <div className="nx-stat-label">Free Forever</div>
          </div>
          <div className="nx-stat">
            <div className="nx-stat-num">4K</div>
            <div className="nx-stat-label">Render Quality</div>
          </div>
          <div className="nx-stat">
            <div className="nx-stat-num">0</div>
            <div className="nx-stat-label">API Keys Needed</div>
          </div>
        </div>
      </section>

      {/* ─── PROCESSING ─── */}
      {job && (
        <section className="nx-processing">
          <div className="nx-processing-panel">
            <h3 style={{fontSize:'0.85rem', marginBottom: 4}}>
              {job.status === 'completed' ? '✅ Video Ready!' :
               job.status === 'failed' ? '❌ Generation Failed' :
               `⏳ Processing: ${progress}%`}
            </h3>
            <p style={{fontSize:'0.65rem', color:'#555566'}}>Job: {jobId}</p>

            <div className="nx-progress-bar">
              <div className="nx-progress-fill" style={{width:`${progress}%`}} />
            </div>

            <div className="nx-stage-indicator">
              {STAGES.map((s, i) => {
                const done = job.status === 'completed' || currentStageIdx > i;
                const active = currentStageIdx === i;
                return (
                  <div key={s} className={`nx-stage ${active ? 'active' : ''} ${done ? 'done' : ''}`}>
                    <div style={{fontSize:'0.9rem'}}>{STAGE_ICONS[s]}</div>
                    <div>{STAGE_LABELS[s]}</div>
                  </div>
                );
              })}
            </div>

            {/* Preview */}
            {job.output_path && (
              <div className="nx-output-preview" style={{marginTop:16}}>
                <video controls src={`/output/${job.output_path.split('/').slice(-2).join('/')}`} />
              </div>
            )}
            {job.output_path && (
              <a className="nx-download-btn" href={`/output/${job.output_path.split('/').slice(-2).join('/')}`} download>
                ⬇ Download Video
              </a>
            )}

            {/* Error */}
            {job.error && (
              <div className="nx-error">{job.error}</div>
            )}
          </div>
        </section>
      )}

      {/* ─── FEATURES ─── */}
      <section className="nx-features">
        <h2>Why Nexus<span style={{color:'#6366f1'}}>X</span>?</h2>
        <div className="nx-feature-grid">
          {FEATURES.map((f, i) => (
            <div key={i} className="nx-feature-card">
              <div className="nx-feature-icon">{f.icon}</div>
              <h3>{f.title}</h3>
              <p>{f.desc}</p>
            </div>
          ))}
        </div>
      </section>

      {/* ─── LAB ─── */}
      <div ref={labRef}>
        {showLab && (
          <NexusXLab config={config} setConfig={setConfig} onGenerate={handleGenerate} generating={generating} url={url} />
        )}
      </div>

      {/* ─── FOOTER ─── */}
      <footer className="nx-footer">
        <p>NexusX · Whisper AI + MediaPipe + FFmpeg · 100% Free & Open Source</p>
      </footer>
    </div>
  );
}
