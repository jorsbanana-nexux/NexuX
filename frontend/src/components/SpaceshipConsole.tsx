import React, { useState, useRef, useEffect, useCallback } from 'react';
import { motion, AnimatePresence } from 'motion/react';
import { 
  UploadCloud, 
  Sparkles, 
  Link as LinkIcon, 
  Scissors, 
  ArrowRight, 
  FileVideo, 
  X, 
  Clock, 
  Terminal,
  Activity,
  Gauge,
  SlidersHorizontal,
  CheckCircle2,
  AlertTriangle,
  Download,
  RotateCcw,
  Loader2,
} from 'lucide-react';
import { ProcessingLoadingState } from './ProcessingLoadingState';
import { ResultsMosaicGrid } from './ResultsMosaicGrid';
import { GeneratedClip } from './VideoResultCard';
import { sound } from '../utils/soundEffects';
import { MagneticElement } from './MagneticElement';
import { useScrollVelocityBlur, VelocityTelemetry } from '../utils/useScrollVelocityBlur';
import { subtitleStore } from '../utils/subtitleStore';
import { SubtitleConfig } from '../types/subtitles';
import { VideoModal } from './VideoModal';
import { Mode2Console } from './Mode2Console';
import { ClipEditorStudio } from './ClipEditorStudio';
import { TimelineEditorStudio } from './TimelineEditorStudio';
import { nexuxApi, buildOutputUrl, startJobPolling, type NexuXJob, type GenerateRequest } from '../api/nexuxApi';

interface SpaceshipConsoleProps {
  onProcessComplete?: (data: NexuXJob) => void;
}

const HOOK_CATEGORIES = [
  '🔥 High-Retention Hook',
  '⚡ Pattern Interrupt',
  '💡 Golden Insight',
  '📈 Viral Momentum',
  '🎯 Precision Cut',
  '✨ Story Beat',
];

function formatDuration(seconds: number): string {
  const mins = Math.floor(seconds / 60);
  const secs = Math.floor(seconds % 60);
  return `${mins}:${secs.toString().padStart(2, '0')}`;
}

function formatTimestamp(start: number, end: number): string {
  return `${formatDuration(start)} - ${formatDuration(end)}`;
}

function mapJobToClips(job: NexuXJob): GeneratedClip[] {
  if (!job.clips || job.clips.length === 0) return [];

  return job.clips.map((clipPath, idx) => {
    const meta = job.render_meta?.[idx] || {};
    const videoUrl = buildOutputUrl(clipPath) || '';

    // Extract data from render_meta
    const virality = typeof meta.virality === 'number' ? meta.virality : 0;
    const editorialEvidence = typeof meta.editorial_evidence === 'string' ? meta.editorial_evidence : '';
    const timeline = meta.timeline as Record<string, unknown> | undefined;
    const render = meta.render as Record<string, unknown> | undefined;
    const retrieval = meta.retrieval as Record<string, unknown> | undefined;

    // Extract timing info from timeline or retrieval
    const startSec = typeof retrieval?.retrieved_start === 'number' ? retrieval.retrieved_start : 0;
    const endSec = typeof retrieval?.retrieved_end === 'number' ? retrieval.retrieved_end : 0;
    const duration = endSec - startSec;

    // Use editorial evidence as subtitle snippet, or fallback
    const subtitleSnippet = editorialEvidence || 'Clip ready for preview';

    // Map hook category based on editorial signals
    const hookCategory = HOOK_CATEGORIES[idx % HOOK_CATEGORIES.length];

    // Build tags from genre and editorial context
    const genre = typeof meta.genre === 'string' ? meta.genre : 'auto';
    const tags = [genre, '9:16', idx === 0 ? 'Top Pick' : `Clip ${idx + 1}`].filter(Boolean) as string[];

    // V9.6: surface Smart Cut stats (dead air removed) as a card tag
    const smartCut = (meta as any).smart_cut as { removed_seconds?: number; filler_count?: number; silence_count?: number } | undefined;
    if (smartCut && (smartCut.removed_seconds ?? 0) >= 1) {
      tags.push(`✂ −${smartCut.removed_seconds!.toFixed(1)}s dead air`);
    }

    return {
      id: `${job.job_id}-clip-${idx + 1}`,
      title: editorialEvidence ? editorialEvidence.slice(0, 60) + (editorialEvidence.length > 60 ? '...' : '') : `Clip ${idx + 1}`,
      hookCategory,
      duration: duration > 0 ? formatDuration(duration) : '0:45',
      viralScore: Math.min(99, Math.max(0, Math.round(virality * 100))),
      timestampRange: duration > 0 ? formatTimestamp(startSec, endSec) : '—',
      subtitleSnippet,
      aspectRatio: '9:16',
      videoUrl,
      tags,
    };
  });
}

export const SpaceshipConsole: React.FC<SpaceshipConsoleProps> = () => {
  // V8.5: Post-render editor state
  const [showEditor, setShowEditor] = useState(false);
  // V9.0: Full timeline editor (Opus-Clip-style, more complete)
  const [showTimelineEditor, setShowTimelineEditor] = useState(false);
  const [mode, setMode] = useState<'mode1' | 'mode2'>('mode1');
  const [stage, setStage] = useState<'input' | 'loading' | 'results' | 'error'>('input');
  const [isDragOver, setIsDragOver] = useState(false);
  const [uploadedFile, setUploadedFile] = useState<File | null>(null);
  const [inputUrl, setInputUrl] = useState('');
  
  // Customization controls
  const [targetDuration, setTargetDuration] = useState<'auto' | '<30s' | '30-60s' | '60-90s'>('auto');
  const [captionTheme, setCaptionTheme] = useState<'cyber' | 'minimal' | 'bold-yellow'>('cyber');
  const [autoReframe, setAutoReframe] = useState(true);
  const [clipCount, setClipCount] = useState(3);

  // Job state
  const [job, setJob] = useState<NexuXJob | null>(null);
  const [errorMsg, setErrorMsg] = useState('');
  const [generatedClips, setGeneratedClips] = useState<GeneratedClip[]>([]);
  const [manualRanges, setManualRanges] = useState<Array<{ start: number; end: number }>>([]);
  const [showManualRanges, setShowManualRanges] = useState(false);
  const [rangeStart, setRangeStart] = useState('');
  const [rangeEnd, setRangeEnd] = useState('');
  const stopPollingRef = useRef<(() => void) | null>(null);
  const autoEditorOpenedRef = useRef(false);

  // Velocity blur telemetry state
  const [telemetry, setTelemetry] = useState<VelocityTelemetry>({
    velocity: 0,
    blur: 0,
    fps: 120,
  });

  // Synced Subtitle Configuration from Subtitle Engine Studio
  const [activeSubtitleConfig, setActiveSubtitleConfig] = useState<SubtitleConfig>(subtitleStore.get());

  useEffect(() => {
    const unsubscribe = subtitleStore.subscribe((newConfig) => {
      setActiveSubtitleConfig(newConfig);
    });
    return () => unsubscribe();
  }, []);

  // Cleanup polling on unmount
  useEffect(() => {
    return () => {
      if (stopPollingRef.current) stopPollingRef.current();
    };
  }, []);

  useEffect(() => {
    // Auto-open editor when render completes and clips are ready
    if (stage === 'results' && generatedClips.length > 0 && !autoEditorOpenedRef.current && !showEditor) {
      const timer = setTimeout(() => {
        sound.playClick();
        setShowEditor(true);
        autoEditorOpenedRef.current = true;
      }, 2000); // 2 second delay to let user see the results grid first
      return () => clearTimeout(timer);
    }
  }, [stage, generatedClips.length, showEditor]);

  const consoleContainerRef = useRef<HTMLDivElement>(null);
  const fileInputRef = useRef<HTMLInputElement>(null);
  const [selectedPreviewClip, setSelectedPreviewClip] = useState<GeneratedClip | null>(null);

  // Hook scroll velocity motion blur to console container
  useScrollVelocityBlur(consoleContainerRef, (data) => {
    setTelemetry(data);
  });

  const durationMap: Record<string, number> = {
    'auto': 45,
    '<30s': 30,
    '30-60s': 45,
    '60-90s': 60,
  };

  const captionThemeMap: Record<string, string> = {
    'cyber': 'hormozi',
    'minimal': 'minimalist',
    'bold-yellow': 'hormozi',
  };

  const handleStartGeneration = async () => {
    sound.playClick();
    sound.playSwoosh();

    // Determine the URL to use
    let url = inputUrl.trim();
    if (!url && !uploadedFile) {
      setErrorMsg('Please provide a YouTube URL or upload a video file.');
      setStage('error');
      return;
    }

    // V9.5: real local upload — POST /api/upload returns a local:// token
    if (uploadedFile && !url) {
      try {
        setErrorMsg('');
        setStage('loading');
        const uploaded = await nexuxApi.upload(uploadedFile);
        url = uploaded.local_url;
      } catch (e) {
        setErrorMsg(`Upload failed: ${e instanceof Error ? e.message : 'unknown error'}`);
        setStage('error');
        return;
      }
    }

    setErrorMsg('');
    setStage('loading');
    setGeneratedClips([]);
    setJob(null);

    try {
      // V8.0: Use subtitleStore settings (from SubtitleEngineStudio) — NOT hardcoded
      const fontSizeMap: Record<string, number> = { compact: 32, normal: 48, large: 60, huge: 72 };
      const fontMap: Record<string, string> = { sans: 'Arial', display: 'Impact', mono: 'Courier New', serif: 'Georgia' };
      const animMap: Record<string, string> = {
        'word-by-word': 'pop', 'line-by-line': 'fade', 'bounce-zoom': 'bounce',
        'typewriter-glitch': 'typewriter', 'kinetic-slide': 'slide', 'pulse-glow': 'glow',
        'flip-rotate': 'flip', 'fade-drift': 'drift',
      };

      const payload: GenerateRequest = {
        youtube_url: url,
        target_duration: durationMap[targetDuration] || 45,
        aspect_ratio: '9:16',
        subtitle_style: activeSubtitleConfig.visualPreset || 'hormozi',
        font: fontMap[activeSubtitleConfig.fontFamily] || 'Arial',
        font_size: fontSizeMap[activeSubtitleConfig.fontSize] || 48,
        primary_color: '#FFFFFF',
        highlight_color: activeSubtitleConfig.highlightColor || '#FFD700',
        stroke_color: '#000000',
        stroke_width: 3,
        position: activeSubtitleConfig.position || 'center',
        animation: animMap[activeSubtitleConfig.animationStyle] || 'pop',
        auto_zoom: autoReframe,
        face_tracking: autoReframe,
        clip_count: clipCount,
        language: null,
        normalize_audio: true,
        emoji_enabled: activeSubtitleConfig.showEmojis || false,
        manual_ranges: manualRanges.length > 0 ? manualRanges : null,
      };

      const created = await nexuxApi.generate(payload);
      setJob(created);

      // Start real job polling
      const stopPolling = startJobPolling(
        created.job_id,
        (updatedJob) => {
          setJob(updatedJob);
        },
        (finishedJob) => {
          setJob(finishedJob);
          if (finishedJob.status === 'completed') {
            const clips = mapJobToClips(finishedJob);
            setGeneratedClips(clips);
            setStage('results');
            sound.playSuccess();
          } else {
            setErrorMsg(finishedJob.error || `Job ${finishedJob.status}.`);
            setStage('error');
          }
        },
      );

      stopPollingRef.current = stopPolling;
    } catch (error) {
      setErrorMsg(error instanceof Error ? error.message : 'Failed to start generation.');
      setStage('error');
    }
  };

  const handleCancelJob = async () => {
    if (!job?.job_id) return;
    sound.playClick();
    try {
      await nexuxApi.cancel(job.job_id);
      if (stopPollingRef.current) {
        stopPollingRef.current();
        stopPollingRef.current = null;
      }
      setErrorMsg('Job cancelled by user.');
      setStage('error');
    } catch (error) {
      setErrorMsg(error instanceof Error ? error.message : 'Failed to cancel job.');
    }
  };

  const handleResetToInput = () => {
    sound.playClick();
    if (stopPollingRef.current) {
      stopPollingRef.current();
      stopPollingRef.current = null;
    }
    autoEditorOpenedRef.current = false;
    setStage('input');
    setUploadedFile(null);
    setInputUrl('');
    setJob(null);
    setErrorMsg('');
    setGeneratedClips([]);
    setManualRanges([]);
    setRangeStart('');
    setRangeEnd('');
  };

  const handleAddRange = () => {
    const start = parseFloat(rangeStart);
    const end = parseFloat(rangeEnd);
    if (isNaN(start) || isNaN(end) || start >= end || start < 0) return;
    setManualRanges([...manualRanges, { start, end }]);
    setRangeStart('');
    setRangeEnd('');
  };

  const handleRemoveRange = (idx: number) => {
    setManualRanges(manualRanges.filter((_, i) => i !== idx));
  };

  const handleDrop = (e: React.DragEvent) => {
    e.preventDefault();
    setIsDragOver(false);
    if (e.dataTransfer.files && e.dataTransfer.files.length > 0) {
      sound.playClick();
      setUploadedFile(e.dataTransfer.files[0]);
    }
  };

  const handleDragOver = (e: React.DragEvent) => {
    e.preventDefault();
    setIsDragOver(true);
  };

  const handleDragLeave = () => {
    setIsDragOver(false);
  };

  const handleFileSelect = (e: React.ChangeEvent<HTMLInputElement>) => {
    if (e.target.files && e.target.files.length > 0) {
      sound.playClick();
      setUploadedFile(e.target.files[0]);
    }
  };

  // Real progress from API
  const progress = Math.max(0, Math.min(100, Math.round(job?.progress ?? 0)));
  const stageLabel = job?.stage || 'queued';

  return (
    <section 
      id="workspace-console" 
      className="relative py-24 px-6 sm:px-10 max-w-6xl mx-auto z-10 select-none"
    >
      <div className="space-y-12">
        {/* Section Header with Japanese Subtitle */}
        <div className="text-center max-w-2xl mx-auto space-y-3">
          <div className="inline-flex items-center gap-2 px-3.5 py-1 rounded-full border border-cyan-500/30 bg-cyan-950/20 text-cyan-300 font-mono text-[11px] uppercase tracking-widest shadow-[0_0_15px_rgba(34,211,238,0.15)]">
            <Terminal className="w-3.5 h-3.5 text-cyan-400" />
            <span>AI Cockpit // コックピット</span>
          </div>

          <h2 className="text-3xl sm:text-5xl font-display font-bold text-white tracking-tight">
            Ingest & Repurpose
          </h2>

          <p className="text-stone-400 text-sm sm:text-base leading-relaxed">
            Feed any long video or URL. NexuX extracts high-virality short clips with auto reframing and animated captions.
          </p>
        </div>

        {/* Modern Astronaut Glassmorphism Visor Frame with Scroll Velocity Blur Target */}
        <div 
          ref={consoleContainerRef}
          className="relative rounded-2xl hud-glass-panel p-6 sm:p-10 shadow-2xl spacex-cyan-border transition-all duration-300 gpu-accel"
        >
          {/* Header Status Bar with Velocity & Cockpit Telemetry */}
          <div className="flex flex-wrap items-center justify-between pb-6 mb-8 border-b border-white/10 text-xs font-mono text-stone-400 gap-3">
            <div className="flex items-center gap-3">
              <span className={`w-2.5 h-2.5 rounded-full animate-ping ${stage === 'loading' ? 'bg-amber-400' : stage === 'results' ? 'bg-emerald-400' : stage === 'error' ? 'bg-red-400' : 'bg-cyan-400'}`}></span>
              <span className="text-white font-semibold tracking-wider flex items-center gap-1.5">
                STAGE: <span className="text-cyan-400 text-glow-cyan">{stage.toUpperCase()}</span>
              </span>
              {job && (
                <span className="text-stone-400 ml-2">
                  ENGINE: <span className="text-cyan-300">{stageLabel}</span>
                </span>
              )}
            </div>

            {/* Live Lenis / Scroll Velocity Telemetry Badge */}
            <div className="flex items-center gap-4 text-[11px] text-stone-400 font-mono">
              <div className="hidden sm:flex items-center gap-1.5 px-2.5 py-1 rounded-md bg-black/60 border border-white/10">
                <Gauge className="w-3.5 h-3.5 text-cyan-400" />
                <span>VELOCITY: <strong className="text-cyan-300">{telemetry.velocity} px/s</strong></span>
              </div>
              <div className="hidden md:flex items-center gap-1.5 px-2.5 py-1 rounded-md bg-black/60 border border-white/10">
                <Activity className="w-3.5 h-3.5 text-purple-400" />
                <span>MOTION BLUR: <strong className="text-purple-300">{telemetry.blur} px</strong></span>
              </div>
              <div className="text-[11px] text-stone-400 font-mono">
                ENGINE: <span className="text-stone-300">V8.0 CANONICAL</span>
              </div>
            </div>
          </div>

          {/* DYNAMIC STAGES */}
          <AnimatePresence mode="wait">
            {/* STAGE 1: INPUT STATE */}
            {stage === 'input' && (
              <>
                <div className="flex items-center justify-center gap-3 mb-6">
                  <button
                    onClick={() => setMode('mode1')}
                    className={`px-5 py-2 rounded-full text-sm font-medium transition-all ${mode === 'mode1' ? 'bg-gradient-to-r from-cyan-500/20 to-blue-500/20 border border-cyan-500/30 text-cyan-300' : 'text-gray-500 hover:text-white border border-transparent'}`}
                  >
                    🎙️ Mode 1 — Podcast Pro
                  </button>
                  <button
                    onClick={() => setMode('mode2')}
                    className={`px-5 py-2 rounded-full text-sm font-medium transition-all ${mode === 'mode2' ? 'bg-gradient-to-r from-purple-500/20 to-pink-500/20 border border-purple-500/30 text-purple-300' : 'text-gray-500 hover:text-white border border-transparent'}`}
                  >
                    ✨ Mode 2 — Creative Viral
                  </button>
                </div>
              <motion.div
                key="input-stage"
                initial={{ opacity: 0 }}
                animate={{ opacity: 1 }}
                exit={{ opacity: 0 }}
                transition={{ duration: 0.2 }}
                className="space-y-8"
              >
                {/* URL Input as primary ingestion method */}
                <div className="space-y-3">
                  <label className="text-xs font-mono text-stone-300 uppercase tracking-wider block">
                    YouTube / Video URL
                  </label>
                  <div className="flex gap-3">
                    <div className="flex-1 relative">
                      <input
                        type="url"
                        value={inputUrl}
                        onChange={(e) => setInputUrl(e.target.value)}
                        onKeyDown={(e) => {
                          if (e.key === 'Enter' && inputUrl.trim()) {
                            handleStartGeneration();
                          }
                        }}
                        placeholder="https://youtube.com/watch?v=..."
                        className="w-full bg-black/60 border border-white/15 rounded-xl px-4 py-3.5 text-sm text-white placeholder-stone-600 focus:outline-none focus:border-cyan-400 transition-colors font-mono"
                      />
                    </div>
                    <button
                      onClick={handleStartGeneration}
                      onMouseEnter={() => sound.playHover()}
                      disabled={!inputUrl.trim()}
                      data-cursor-text="GO"
                      className="px-6 py-3.5 rounded-xl bg-white text-black font-mono font-bold uppercase tracking-widest text-xs hover:bg-stone-200 transition-all flex items-center justify-center gap-2 shadow-[0_0_25px_rgba(255,255,255,0.4)] disabled:opacity-30 disabled:cursor-not-allowed"
                    >
                      <Scissors className="w-4 h-4" />
                      <span>Clip It</span>
                    </button>
                  </div>
                </div>

                {/* Divider */}
                <div className="flex items-center gap-4">
                  <div className="flex-1 h-px bg-white/10" />
                  <span className="text-xs font-mono text-stone-500">OR</span>
                  <div className="flex-1 h-px bg-white/10" />
                </div>

                {/* Drag & Drop Area (secondary) */}
                <div
                  onDrop={handleDrop}
                  onDragOver={handleDragOver}
                  onDragLeave={handleDragLeave}
                  onClick={() => {
                    sound.playClick();
                    fileInputRef.current?.click();
                  }}
                  onMouseEnter={() => sound.playHover()}
                  data-cursor-text="UPLOAD"
                  className={`relative group rounded-xl border border-dashed p-8 sm:p-14 text-center transition-all cursor-pointer ${
                    isDragOver
                      ? 'border-cyan-400 bg-cyan-950/40 shadow-[0_0_30px_rgba(34,211,238,0.3)]'
                      : uploadedFile
                      ? 'border-emerald-500/60 bg-emerald-950/20 shadow-[0_0_20px_rgba(16,185,129,0.2)]'
                      : 'border-white/20 bg-black/40 hover:border-cyan-400/50 hover:bg-cyan-950/10 hover:shadow-[0_0_25px_rgba(34,211,238,0.15)]'
                  }`}
                >
                  <input
                    ref={fileInputRef}
                    type="file"
                    accept="video/*"
                    onChange={handleFileSelect}
                    className="hidden"
                  />

                  {uploadedFile ? (
                    <div className="space-y-4">
                      <div className="w-14 h-14 rounded-xl bg-emerald-500/20 border border-emerald-500/40 flex items-center justify-center mx-auto text-emerald-300 shadow-[0_0_15px_rgba(16,185,129,0.4)]">
                        <FileVideo className="w-7 h-7" />
                      </div>
                      <div>
                        <h4 className="text-base font-bold text-white font-mono break-all">
                          {uploadedFile.name}
                        </h4>
                        <p className="text-xs text-stone-400 mt-1">
                          {(uploadedFile.size / (1024 * 1024)).toFixed(2)} MB
                        </p>
                      </div>
                      <button
                        onClick={(e) => {
                          e.stopPropagation();
                          sound.playClick();
                          setUploadedFile(null);
                        }}
                        className="inline-flex items-center gap-1.5 px-3 py-1.5 rounded-lg bg-white/5 hover:bg-white/10 text-stone-300 text-xs font-mono transition-colors"
                      >
                        <X className="w-3.5 h-3.5" />
                        Remove
                      </button>
                    </div>
                  ) : (
                    <div className="space-y-4">
                      <div className="w-14 h-14 rounded-xl bg-cyan-950/40 border border-cyan-400/30 flex items-center justify-center mx-auto text-cyan-300 group-hover:scale-110 transition-transform">
                        <UploadCloud className="w-7 h-7" />
                      </div>
                      <div>
                        <h4 className="text-base font-bold text-white">
                          Drop video here
                        </h4>
                        <p className="text-xs text-stone-400 mt-1">
                          MP4, MOV, MKV — uploading on your machine (100% local)
                        </p>
                      </div>
                    </div>
                  )}
                </div>

                {/* Customization Controls */}
                <div className="grid grid-cols-1 sm:grid-cols-3 gap-4">
                  {/* Target Duration */}
                  <div className="space-y-2">
                    <label className="text-[11px] font-mono text-stone-400 uppercase tracking-wider flex items-center gap-1.5">
                      <Clock className="w-3.5 h-3.5" />
                      Duration
                    </label>
                    <select
                      value={targetDuration}
                      onChange={(e) => setTargetDuration(e.target.value as typeof targetDuration)}
                      className="w-full bg-black/60 border border-white/15 rounded-xl px-3 py-2.5 text-xs text-white focus:outline-none focus:border-cyan-400 font-mono"
                    >
                      <option value="auto">Auto (45s)</option>
                      <option value="<30s">Short (&lt;30s)</option>
                      <option value="30-60s">Medium (30-60s)</option>
                      <option value="60-90s">Long (60-90s)</option>
                    </select>
                  </div>

                  {/* Caption Theme */}
                  <div className="space-y-2">
                    <label className="text-[11px] font-mono text-stone-400 uppercase tracking-wider flex items-center gap-1.5">
                      <SlidersHorizontal className="w-3.5 h-3.5" />
                      Caption Style
                    </label>
                    <select
                      value={captionTheme}
                      onChange={(e) => setCaptionTheme(e.target.value as typeof captionTheme)}
                      className="w-full bg-black/60 border border-white/15 rounded-xl px-3 py-2.5 text-xs text-white focus:outline-none focus:border-cyan-400 font-mono"
                    >
                      <option value="cyber">Cyber (Hormozi)</option>
                      <option value="minimal">Minimal</option>
                      <option value="bold-yellow">Bold Yellow</option>
                    </select>
                  </div>

                  {/* Clip Count */}
                  <div className="space-y-2">
                    <label className="text-[11px] font-mono text-stone-400 uppercase tracking-wider flex items-center gap-1.5">
                      <Scissors className="w-3.5 h-3.5" />
                      Clip Count
                    </label>
                    <select
                      value={clipCount}
                      onChange={(e) => setClipCount(Number(e.target.value))}
                      className="w-full bg-black/60 border border-white/15 rounded-xl px-3 py-2.5 text-xs text-white focus:outline-none focus:border-cyan-400 font-mono"
                    >
                      <option value={1}>1 clip</option>
                      <option value={3}>3 clips</option>
                      <option value={5}>5 clips</option>
                      <option value={10}>10 clips</option>
                    </select>
                  </div>
                </div>

                {/* Auto-reframe Toggle */}
                <div className="flex items-center justify-between p-4 rounded-xl bg-white/5 border border-white/10">
                  <div className="flex items-center gap-3">
                    <SlidersHorizontal className="w-4 h-4 text-cyan-400" />
                    <div>
                      <p className="text-sm font-mono text-white">Auto-Reframe + Face Tracking</p>
                      <p className="text-[11px] text-stone-400 font-mono">Dynamic 9:16 crop with speaker tracking</p>
                    </div>
                  </div>
                  <button
                    onClick={() => setAutoReframe(!autoReframe)}
                    className={`relative w-12 h-6 rounded-full transition-colors ${autoReframe ? 'bg-cyan-400' : 'bg-stone-700'}`}
                  >
                    <span className={`absolute top-0.5 w-5 h-5 rounded-full bg-white transition-transform ${autoReframe ? 'translate-x-6' : 'translate-x-0.5'}`} />
                  </button>
                </div>

                {/* V8.0: Manual Time Range Selector */}
                <div className="rounded-xl bg-white/5 border border-white/10 p-4 space-y-3">
                  <div className="flex items-center justify-between">
                    <div className="flex items-center gap-3">
                      <Clock className="w-4 h-4 text-cyan-400" />
                      <div>
                        <p className="text-sm font-mono text-white">Manual Moment Selection</p>
                        <p className="text-[11px] text-stone-400 font-mono">Select specific time ranges instead of AI auto-selection</p>
                      </div>
                    </div>
                    <button
                      onClick={() => setShowManualRanges(!showManualRanges)}
                      className={`relative w-12 h-6 rounded-full transition-colors ${showManualRanges ? 'bg-cyan-400' : 'bg-stone-700'}`}
                    >
                      <span className={`absolute top-0.5 w-5 h-5 rounded-full bg-white transition-transform ${showManualRanges ? 'translate-x-6' : 'translate-x-0.5'}`} />
                    </button>
                  </div>

                  {showManualRanges && (
                    <div className="space-y-2 pt-2 border-t border-white/10">
                      <div className="flex gap-2">
                        <input
                          type="text"
                          value={rangeStart}
                          onChange={(e) => setRangeStart(e.target.value)}
                          placeholder="Start (e.g. 1:30 or 90)"
                          className="flex-1 bg-black/60 border border-white/15 rounded-lg px-3 py-2 text-xs text-white font-mono focus:outline-none focus:border-cyan-400"
                        />
                        <input
                          type="text"
                          value={rangeEnd}
                          onChange={(e) => setRangeEnd(e.target.value)}
                          placeholder="End (e.g. 2:00 or 120)"
                          className="flex-1 bg-black/60 border border-white/15 rounded-lg px-3 py-2 text-xs text-white font-mono focus:outline-none focus:border-cyan-400"
                        />
                        <button
                          onClick={handleAddRange}
                          className="px-3 py-2 rounded-lg bg-cyan-500/20 hover:bg-cyan-500/30 text-cyan-400 border border-cyan-500/30 text-xs font-mono"
                        >
                          + Add
                        </button>
                      </div>
                      {manualRanges.length > 0 && (
                        <div className="space-y-1">
                          {manualRanges.map((r, i) => (
                            <div key={i} className="flex items-center justify-between bg-black/40 rounded-lg px-3 py-1.5 text-xs font-mono">
                              <span className="text-cyan-300">
                                Clip {i+1}: {Math.floor(r.start/60)}:{String(Math.floor(r.start%60)).padStart(2,'0')} → {Math.floor(r.end/60)}:{String(Math.floor(r.end%60)).padStart(2,'0')} ({Math.round(r.end-r.start)}s)
                              </span>
                              <button onClick={() => handleRemoveRange(i)} className="text-red-400 hover:text-red-300">✕</button>
                            </div>
                          ))}
                        </div>
                      )}
                      {manualRanges.length === 0 && (
                        <p className="text-[10px] text-stone-500 font-mono">No ranges added — AI will auto-select moments</p>
                      )}
                    </div>
                  )}
                </div>

                {/* Generate Button */}
                <button
                  onClick={handleStartGeneration}
                  onMouseEnter={() => sound.playHover()}
                  disabled={!inputUrl.trim()}
                  data-cursor-text="LAUNCH"
                  className="w-full py-4 rounded-xl bg-white text-black font-mono font-bold uppercase tracking-widest text-xs hover:bg-stone-200 transition-all flex items-center justify-center gap-2 shadow-[0_0_25px_rgba(255,255,255,0.4)] disabled:opacity-30 disabled:cursor-not-allowed"
                >
                  <Sparkles className="w-4 h-4" />
                  <span>Start Autonomous Slicing</span>
                  <ArrowRight className="w-4 h-4" />
                </button>
              </motion.div>
              </>
            )}

            {/* STAGE 2: LOADING STATE — REAL PROGRESS FROM API */}
            {stage === 'loading' && (
              <motion.div
                key="loading-stage"
                initial={{ opacity: 0 }}
                animate={{ opacity: 1 }}
                exit={{ opacity: 0 }}
                transition={{ duration: 0.3 }}
              >
                <ProcessingLoadingState
                  progress={progress}
                  stageLabel={stageLabel}
                  onCancel={handleCancelJob}
                  elapsedSeconds={(job as any)?._stages?.[stageLabel]?.elapsed_seconds}
                  etaSeconds={(job as any)?._stages?.[stageLabel]?.eta_seconds}
                  fastPath={(job as any)?._stages?.transcribing?.fast_path || (job as any)?._stages?.transcribing?.source === 'youtube_auto'}
                />
              </motion.div>
            )}

            {/* STAGE 3: RESULTS — REAL CLIPS FROM API */}
            {stage === 'results' && generatedClips.length > 0 && (
              <motion.div
                key="results-stage"
                initial={{ opacity: 0 }}
                animate={{ opacity: 1 }}
                exit={{ opacity: 0 }}
                transition={{ duration: 0.3 }}
              >
                <ResultsMosaicGrid
                  clips={generatedClips}
                  onReset={handleResetToInput}
                  onPreviewClip={(clip) => setSelectedPreviewClip(clip)}
                  onPersonalize={() => { sound.playClick(); setShowEditor(true); }}
                  onOpenTimelineEditor={() => { sound.playClick(); setShowTimelineEditor(true); }}
                />
              </motion.div>
            )}

            {/* STAGE 4: ERROR STATE */}
            {stage === 'error' && (
              <motion.div
                key="error-stage"
                initial={{ opacity: 0 }}
                animate={{ opacity: 1 }}
                exit={{ opacity: 0 }}
                className="py-16 flex flex-col items-center justify-center text-center space-y-6"
              >
                <div className="w-16 h-16 rounded-2xl bg-red-500/20 border border-red-500/40 flex items-center justify-center text-red-400 shadow-[0_0_25px_rgba(239,68,68,0.3)]">
                  <AlertTriangle className="w-8 h-8" />
                </div>
                <div className="space-y-2 max-w-md">
                  <h3 className="text-xl font-display font-bold text-white">Generation Failed</h3>
                  <p className="text-sm text-stone-400 font-mono leading-relaxed">{errorMsg}</p>
                </div>
                <button
                  onClick={handleResetToInput}
                  onMouseEnter={() => sound.playHover()}
                  className="inline-flex items-center gap-2 px-6 py-3 rounded-xl bg-white/5 hover:bg-white/10 text-stone-300 hover:text-white border border-white/10 text-xs font-mono transition-colors"
                >
                  <RotateCcw className="w-4 h-4" />
                  Try Again
                </button>
              </motion.div>
            )}
          </AnimatePresence>
        </div>
      </div>

      {/* Video Preview Modal */}
      <VideoModal
        isOpen={!!selectedPreviewClip}
        onClose={() => setSelectedPreviewClip(null)}
      />

      {/* V8.5: Post-Render Personalization Editor */}
      <AnimatePresence>
        {showEditor && (
          <ClipEditorStudio
            clips={generatedClips}
            jobId={(job as any)?.job_id || ''}
            onClose={() => setShowEditor(false)}
          />
        )}
      </AnimatePresence>

      {/* V9.0: Full Timeline Editor (Opus-Clip-style + more) */}
      <AnimatePresence>
        {showTimelineEditor && (
          <TimelineEditorStudio
            clips={generatedClips}
            jobId={(job as any)?.job_id || ''}
            onClose={() => setShowTimelineEditor(false)}
            transcriptSegments={(job?.analysis_bundle as any)?.transcript_segments}
            clipCandidates={(job?.analysis_bundle as any)?.clip_candidates}
          />
        )}
      </AnimatePresence>

      {stage === 'results' && generatedClips.length > 0 && !autoEditorOpenedRef.current && !showEditor && (
        <motion.div
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
          className="fixed bottom-8 left-1/2 -translate-x-1/2 z-40 px-5 py-3 rounded-xl bg-black/80 border border-cyan-500/30 backdrop-blur-xl flex items-center gap-3"
        >
          <Loader2 className="w-4 h-4 animate-spin text-cyan-400" />
          <span className="text-sm text-cyan-300 font-mono">Opening editor...</span>
        </motion.div>
      )}
    </section>
  );
};
