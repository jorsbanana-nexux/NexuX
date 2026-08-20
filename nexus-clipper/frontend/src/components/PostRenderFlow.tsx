/**
 * NexuX V9.5 — Post-Render Flow Orchestrator
 * ============================================
 * 
 * Manages the full flow:
 * 1. Input (Mode 1 URL or Mode 2 keyword)
 * 2. Processing (real-time progress via WebSocket/polling)
 * 3. Results Grid (shows all rendered clips)
 * 4. Auto-navigate to Editor (ClipEditorStudio) when user clicks "Personalize"
 *    OR auto-navigate after all clips are ready (configurable)
 * 
 * This is the component that ties everything together:
 * SpaceshipConsole/Mode2Console → PostRenderFlow → Results → Editor
 */

import React, { useState, useEffect, useCallback, useRef } from 'react';
import { motion, AnimatePresence } from 'motion/react';
import {
  Loader2, CheckCircle2, AlertCircle, Download, Edit3,
  Sparkles, Mic, ArrowRight, RefreshCw, Clock, Film,
  ChevronRight, Zap,
} from 'lucide-react';
import { sound } from '../utils/soundEffects';
import {
  nexuxApi, startJobPolling, buildOutputUrl,
  type NexuXJob, type NexuXStatus,
} from '../api/nexuxApi';
import { v2Api, type NexuXMode } from '../api/v2Api';
import { GeneratedClip } from './VideoResultCard';
import { ClipEditorStudio } from './ClipEditorStudio';

// ── Flow States ──
type FlowState =
  | 'input'       // Waiting for user input
  | 'processing'  // Job is running
  | 'results'     // Clips are ready, showing grid
  | 'editor';     // Full-screen editor open

interface PostRenderFlowProps {
  mode: NexuXMode;
  // Mode 1
  youtubeUrl?: string;
  // Mode 2
  keyword?: string;
  // Settings
  targetDuration?: number;
  clipCount?: number;
  subtitleStyle?: string;
  aspectRatio?: string;
  voiceEnabled?: boolean;
  voiceName?: string;
  sfxEnabled?: boolean;
  bgmEnabled?: boolean;
  maxSources?: number;
  // Auto-open editor after render (default: false, user clicks "Personalize")
  autoOpenEditor?: boolean;
  // Callbacks
  onBack?: () => void;
  onComplete?: (clips: GeneratedClip[]) => void;
}

export const PostRenderFlow: React.FC<PostRenderFlowProps> = ({
  mode,
  youtubeUrl,
  keyword,
  targetDuration = 45,
  clipCount = 5,
  subtitleStyle = 'hormozi',
  aspectRatio = '9:16',
  voiceEnabled = true,
  voiceName = 'id-ID-ArdiNeural',
  sfxEnabled = true,
  bgmEnabled = true,
  maxSources = 10,
  autoOpenEditor = false,
  onBack,
  onComplete,
}) => {
  const [flowState, setFlowState] = useState<FlowState>('input');
  const [jobId, setJobId] = useState<string | null>(null);
  const [job, setJob] = useState<NexuXJob | null>(null);
  const [clips, setClips] = useState<GeneratedClip[]>([]);
  const [error, setError] = useState<string | null>(null);
  const [autoEditorTriggered, setAutoEditorTriggered] = useState(false);
  const stopPollingRef = useRef<(() => void) | null>(null);

  // ── Start Generation ──
  const startGeneration = useCallback(async () => {
    setFlowState('processing');
    setError(null);
    setClips([]);
    setAutoEditorTriggered(false);

    try {
      const payload: Record<string, unknown> = {
        mode,
        target_duration: targetDuration,
        aspect_ratio: aspectRatio,
        subtitle_style: subtitleStyle,
      };

      if (mode === 'podcast' && youtubeUrl) {
        payload.youtube_url = youtubeUrl;
        payload.clip_count = clipCount;
      } else if (mode === 'creative' && keyword) {
        payload.keyword = keyword;
        payload.voice_enabled = voiceEnabled;
        payload.voice_name = voiceName;
        payload.sfx_enabled = sfxEnabled;
        payload.bgm_enabled = bgmEnabled;
        payload.max_sources = maxSources;
      }

      const res = await v2Api.generate(payload as Parameters<typeof v2Api.generate>[0]);
      setJobId(res.job_id);

      // Start polling for job status
      stopPollingRef.current = startJobPolling(
        res.job_id,
        (updatedJob) => {
          setJob(updatedJob);
        },
        (finalJob) => {
          setJob(finalJob);
          if (finalJob.status === 'completed' && finalJob.clips?.length > 0) {
            // Convert clips to GeneratedClip format
            const generatedClips = finalJob.clips.map((url, idx) => ({
              id: `${finalJob.job_id}-${idx}`,
              url: buildOutputUrl(url) || url,
              thumbnail: '',
              title: `Clip ${idx + 1}`,
              duration: targetDuration,
              score: finalJob.render_meta?.[idx]?.virality || 0,
            }));
            setClips(generatedClips);
            setFlowState('results');

            if (autoOpenEditor) {
              // Auto-navigate to editor after a brief delay
              setTimeout(() => {
                setFlowState('editor');
                setAutoEditorTriggered(true);
              }, 1500);
            }
          } else if (finalJob.status === 'failed') {
            setError(finalJob.error || 'Generation failed');
            setFlowState('input');
          }
        },
        1500,
      );
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to start generation');
      setFlowState('input');
    }
  }, [mode, youtubeUrl, keyword, targetDuration, clipCount, subtitleStyle,
      aspectRatio, voiceEnabled, voiceName, sfxEnabled, bgmEnabled, maxSources,
      autoOpenEditor]);

  // ── Auto-start when URL or keyword is provided ──
  useEffect(() => {
    if (flowState === 'input' && ((mode === 'podcast' && youtubeUrl) || (mode === 'creative' && keyword))) {
      startGeneration();
    }
    // Cleanup polling on unmount
    return () => {
      stopPollingRef.current?.();
    };
  }, [flowState, mode, youtubeUrl, keyword]);

  // ── Editor handlers ──
  const handleOpenEditor = () => {
    sound.playClick();
    setFlowState('editor');
  };

  const handleCloseEditor = () => {
    sound.playClick();
    setFlowState('results');
  };

  const handleReRender = () => {
    // Re-run the pipeline with new settings
    startGeneration();
  };

  // ── Render ──

  // INPUT STATE
  if (flowState === 'input' && !jobId) {
    return (
      <div className="flex flex-col items-center justify-center min-h-[400px] gap-4">
        {error && (
          <div className="flex items-center gap-2 text-red-400 text-sm">
            <AlertCircle className="w-5 h-5" />
            {error}
          </div>
        )}
        {onBack && (
          <button
            onClick={() => { sound.playClick(); onBack(); }}
            className="text-gray-400 hover:text-white text-sm flex items-center gap-2"
          >
            ← Kembali
          </button>
        )}
      </div>
    );
  }

  // PROCESSING STATE
  if (flowState === 'processing') {
    return (
      <ProcessingView job={job} mode={mode} />
    );
  }

  // RESULTS STATE
  if (flowState === 'results') {
    return (
      <ResultsView
        clips={clips}
        jobId={jobId || ''}
        mode={mode}
        autoEditorTriggered={autoEditorTriggered}
        onOpenEditor={handleOpenEditor}
        onRegenerate={handleReRender}
        onBack={onBack}
        onComplete={onComplete}
      />
    );
  }

  // EDITOR STATE — Full-screen ClipEditorStudio
  if (flowState === 'editor' && clips.length > 0) {
    return (
      <ClipEditorStudio
        clips={clips}
        jobId={jobId || ''}
        onClose={handleCloseEditor}
        onReRender={() => {
          // After re-render, go back to results
          handleCloseEditor();
          handleReRender();
        }}
      />
    );
  }

  return null;
};

// ═══════════════════════════════════════════════════
// Processing View — Real-time progress
// ═══════════════════════════════════════════════════

const ProcessingView: React.FC<{ job: NexuXJob | null; mode: NexuXMode }> = ({ job, mode }) => {
  const progress = job?.progress || 0;
  const stage = job?.stage || 'queued';
  const modeLabel = mode === 'podcast' ? '🎙️ Podcast Mode' : '✨ AI Creative Mode';

  const stageLabels: Record<string, string> = {
    queued: 'Menunggu...',
    metadata: 'Mengambil info video...',
    transcribing: 'Transkripsi audio...',
    analyzing: 'AI menganalisis konten...',
    downloading: 'Mengunduh bagian video...',
    rendering: 'Rendering klip dengan efek...',
    critic: 'Kritik editorial & revisi...',
    assembly: 'Perakitan final...',
    searching: 'Mencari video YouTube...',
    narrating: 'Generate narasi AI...',
    compiling: 'Kompilasi video...',
  };

  return (
    <div className="flex flex-col items-center justify-center min-h-[500px] gap-6">
      {/* Spinner */}
      <div className="relative">
        <motion.div
          animate={{ rotate: 360 }}
          transition={{ duration: 2, repeat: Infinity, ease: 'linear' }}
          className="w-20 h-20 rounded-full border-2 border-cyan-500/20 border-t-cyan-400"
        />
        <div className="absolute inset-0 flex items-center justify-center">
          <span className="text-2xl">{mode === 'podcast' ? '🎙️' : '✨'}</span>
        </div>
      </div>

      {/* Mode label */}
      <div className="text-sm text-gray-400 font-mono">{modeLabel}</div>

      {/* Stage */}
      <div className="text-lg text-white font-medium">
        {stageLabels[stage] || stage}
      </div>

      {/* Progress bar */}
      <div className="w-full max-w-md">
        <div className="flex items-center justify-between mb-2">
          <span className="text-xs text-gray-500">Progress</span>
          <span className="text-xs text-cyan-400 font-mono">{progress.toFixed(0)}%</span>
        </div>
        <div className="h-2 bg-white/5 rounded-full overflow-hidden">
          <motion.div
            animate={{ width: `${progress}%` }}
            transition={{ duration: 0.5 }}
            className="h-full bg-gradient-to-r from-cyan-500 to-blue-500 rounded-full"
          />
        </div>
      </div>

      {/* ETA */}
      {job && (job as Record<string, unknown>)._stages && (
        <div className="text-xs text-gray-500 flex items-center gap-2">
          <Clock className="w-3 h-3" />
          ETA: {((job as Record<string, unknown>)._eta_seconds as number || 0).toFixed(0)}s
        </div>
      )}
    </div>
  );
};

// ═══════════════════════════════════════════════════
// Results View — Clip grid with "Personalize" button
// ═══════════════════════════════════════════════════

interface ResultsViewProps {
  clips: GeneratedClip[];
  jobId: string;
  mode: NexuXMode;
  autoEditorTriggered: boolean;
  onOpenEditor: () => void;
  onRegenerate: () => void;
  onBack?: () => void;
  onComplete?: (clips: GeneratedClip[]) => void;
}

const ResultsView: React.FC<ResultsViewProps> = ({
  clips, jobId, mode, autoEditorTriggered,
  onOpenEditor, onRegenerate, onBack, onComplete,
}) => {
  return (
    <motion.div
      initial={{ opacity: 0, y: 20 }}
      animate={{ opacity: 1, y: 0 }}
      className="w-full max-w-5xl mx-auto"
    >
      {/* Success header */}
      <div className="text-center mb-8">
        <motion.div
          initial={{ scale: 0 }}
          animate={{ scale: 1 }}
          transition={{ type: 'spring', delay: 0.2 }}
          className="inline-flex items-center justify-center w-16 h-16 rounded-full bg-emerald-500/10 border border-emerald-500/30 mb-4"
        >
          <CheckCircle2 className="w-8 h-8 text-emerald-400" />
        </motion.div>
        <h2 className="text-2xl font-bold text-white mb-2">
          {clips.length} Klip Siap! 🎉
        </h2>
        <p className="text-gray-400 text-sm">
          Klik "Personalisasi" untuk edit effect, subtitle, template, dan lainnya
        </p>
      </div>

      {/* Clips grid */}
      <div className="grid grid-cols-2 md:grid-cols-3 gap-4 mb-8">
        {clips.map((clip, idx) => (
          <motion.div
            key={clip.id}
            initial={{ opacity: 0, scale: 0.9 }}
            animate={{ opacity: 1, scale: 1 }}
            transition={{ delay: idx * 0.1 }}
            className="relative rounded-xl overflow-hidden border border-white/10 bg-black/40 group"
          >
            {/* Video thumbnail/preview */}
            <div className="aspect-[9/16] relative">
              {clip.url && (
                <video
                  src={clip.url}
                  className="w-full h-full object-cover"
                  muted
                  onMouseEnter={(e) => e.currentTarget.play()}
                  onMouseLeave={(e) => { e.currentTarget.pause(); e.currentTime = 0; }}
                />
              )}
              {/* Score badge */}
              {clip.score > 0 && (
                <div className="absolute top-2 right-2 px-2 py-0.5 rounded-md bg-black/60 backdrop-blur text-xs font-mono text-cyan-400">
                  {clip.score.toFixed(0)}
                </div>
              )}
              {/* Clip number */}
              <div className="absolute top-2 left-2 px-2 py-0.5 rounded-md bg-black/60 backdrop-blur text-xs text-white font-mono">
                #{idx + 1}
              </div>
            </div>
            {/* Clip info */}
            <div className="p-3">
              <div className="text-sm text-white font-medium truncate">{clip.title}</div>
              <div className="text-xs text-gray-500 mt-1 flex items-center gap-2">
                <Clock className="w-3 h-3" /> {clip.duration}s
              </div>
            </div>
          </motion.div>
        ))}
      </div>

      {/* Action buttons */}
      <div className="flex flex-col sm:flex-row items-center justify-center gap-3">
        {/* Primary: Personalize */}
        <motion.button
          whileHover={{ scale: 1.02 }}
          whileTap={{ scale: 0.98 }}
          onClick={onOpenEditor}
          className="px-8 py-4 rounded-xl bg-gradient-to-r from-cyan-500 to-blue-500 text-white font-medium flex items-center gap-3 shadow-lg shadow-cyan-500/20"
        >
          <Edit3 className="w-5 h-5" />
          Personalisasi Klip
          <ArrowRight className="w-4 h-4" />
        </motion.button>

        {/* Secondary: Download all */}
        <a
          href={jobId ? nexuxApi.downloadUrl(jobId) : '#'}
          className="px-6 py-4 rounded-xl bg-white/5 border border-white/10 text-white font-medium flex items-center gap-2 hover:bg-white/10 transition-colors"
        >
          <Download className="w-5 h-5" />
          Download Semua
        </a>

        {/* Tertiary: Regenerate */}
        <button
          onClick={onRegenerate}
          className="px-6 py-4 rounded-xl bg-white/5 border border-white/10 text-white font-medium flex items-center gap-2 hover:bg-white/10 transition-colors"
        >
          <RefreshCw className="w-5 h-5" />
          Generate Ulang
        </button>
      </div>

      {/* Auto-editor indicator */}
      {autoEditorTriggered && (
        <div className="mt-4 text-center text-xs text-cyan-400 flex items-center justify-center gap-2">
          <Sparkles className="w-3 h-3" />
          Membuka editor otomatis...
        </div>
      )}

      {/* Feature hints */}
      <div className="mt-8 grid grid-cols-2 md:grid-cols-4 gap-3">
        {[
          { icon: Edit3, label: '10 Creator Templates', desc: 'Hormozi, MrBeast, dll' },
          { icon: Sparkles, label: 'Effect Personalisasi', desc: 'Zoom, color grade, speed' },
          { icon: Film, label: 'Subtitle Studio', desc: 'Font, warna, animasi' },
          { icon: Zap, label: 'Re-render Cepat', desc: 'Preview real-time' },
        ].map((f, i) => {
          const Icon = f.icon;
          return (
            <div key={i} className="flex items-center gap-2 p-3 rounded-lg bg-white/5 border border-white/5">
              <Icon className="w-4 h-4 text-cyan-400" />
              <div>
                <div className="text-xs text-white font-medium">{f.label}</div>
                <div className="text-[10px] text-gray-500">{f.desc}</div>
              </div>
            </div>
          );
        })}
      </div>

      {/* Back button */}
      {onBack && (
        <div className="mt-6 text-center">
          <button
            onClick={onBack}
            className="text-gray-400 hover:text-white text-sm flex items-center gap-2 mx-auto"
          >
            ← Kembali ke Mode Selector
          </button>
        </div>
      )}
    </motion.div>
  );
};
