import React, { useEffect, useRef, useState } from 'react';
import { motion, AnimatePresence } from 'motion/react';
import {
  X,
  Sparkles,
  Video,
  ArrowRight,
  CheckCircle2,
  Cpu,
  AlertTriangle,
  Download,
  Square,
  ExternalLink,
} from 'lucide-react';
import {
  buildOutputUrl,
  nexuxApi,
  type NexuXJob,
  type NexuXStatus,
} from '../api/nexuxApi';

interface TryModalProps {
  isOpen: boolean;
  onClose: () => void;
}

type Stage = 'input' | 'processing' | 'done' | 'error';

const TERMINAL: NexuXStatus[] = ['completed', 'failed', 'cancelled', 'interrupted'];

const stageLabel = (stage: string, status: NexuXStatus) => {
  if (status === 'queued') return 'Job queued • waiting for engine';
  if (status === 'completed') return 'Render complete • quality gate passed';
  if (status === 'failed') return 'Engine reported a failure';
  if (status === 'cancelled') return 'Job cancelled';
  if (status === 'interrupted') return 'Job interrupted';
  return stage.replace(/_/g, ' ');
};

export const TryModal: React.FC<TryModalProps> = ({ isOpen, onClose }) => {
  const [stage, setStage] = useState<Stage>('input');
  const [url, setUrl] = useState('');
  const [clipCount, setClipCount] = useState(5);
  const [job, setJob] = useState<NexuXJob | null>(null);
  const [error, setError] = useState('');
  const [cancelling, setCancelling] = useState(false);
  const pollTimer = useRef<ReturnType<typeof setTimeout> | null>(null);

  const stopPolling = () => {
    if (pollTimer.current) {
      clearTimeout(pollTimer.current);
      pollTimer.current = null;
    }
  };

  const pollJob = async (jobId: string) => {
    try {
      const next = await nexuxApi.job(jobId);
      setJob(next);

      if (next.status === 'completed') {
        setStage('done');
        return;
      }
      if (TERMINAL.includes(next.status)) {
        setError(next.error || `Job ${next.status}.`);
        setStage('error');
        return;
      }

      pollTimer.current = setTimeout(() => {
        void pollJob(jobId);
      }, 1500);
    } catch (pollError) {
      setError(pollError instanceof Error ? pollError.message : 'Unable to read job status.');
      setStage('error');
    }
  };

  useEffect(() => () => stopPolling(), []);

  const handleStartAnalysis = async (e: React.FormEvent) => {
    e.preventDefault();
    stopPolling();
    setError('');
    setJob(null);
    setStage('processing');

    try {
      const created = await nexuxApi.generate({
        youtube_url: url.trim(),
        target_duration: 45,
        aspect_ratio: '9:16',
        subtitle_style: 'hormozi',
        font: 'Arial',
        font_size: 48,
        primary_color: '#FFFFFF',
        highlight_color: '#FFD700',
        stroke_color: '#000000',
        stroke_width: 3,
        position: 'center',
        animation: 'pop',
        auto_zoom: true,
        face_tracking: true,
        clip_count: clipCount,
        language: null,
        normalize_audio: true,
        emoji_enabled: false,
      });
      setJob(created);
      await pollJob(created.job_id);
    } catch (submitError) {
      setError(submitError instanceof Error ? submitError.message : 'Unable to start NexuX.');
      setStage('error');
    }
  };

  const handleCancel = async () => {
    if (!job?.job_id || cancelling) return;
    setCancelling(true);
    try {
      await nexuxApi.cancel(job.job_id);
      stopPolling();
      setJob((current) => current ? { ...current, status: 'cancelled', stage: 'cancelled' } : current);
      setError('Job cancelled by user.');
      setStage('error');
    } catch (cancelError) {
      setError(cancelError instanceof Error ? cancelError.message : 'Unable to cancel the job.');
    } finally {
      setCancelling(false);
    }
  };

  const handleReset = () => {
    stopPolling();
    setStage('input');
    setUrl('');
    setClipCount(5);
    setJob(null);
    setError('');
    onClose();
  };

  const firstClip = buildOutputUrl(job?.clips?.[0] ?? job?.output_path ?? null);
  const progress = Math.max(0, Math.min(100, Number(job?.progress ?? 0)));

  if (!isOpen) return null;

  return (
    <AnimatePresence>
      <div className="fixed inset-0 z-50 flex items-center justify-center p-4 sm:p-6">
        <motion.div
          initial={{ opacity: 0 }}
          animate={{ opacity: 1 }}
          exit={{ opacity: 0 }}
          onClick={stage === 'processing' ? undefined : onClose}
          className="absolute inset-0 bg-black/85 backdrop-blur-xl"
        />

        <motion.div
          initial={{ opacity: 0, scale: 0.95, y: 15 }}
          animate={{ opacity: 1, scale: 1, y: 0 }}
          exit={{ opacity: 0, scale: 0.95, y: 15 }}
          className="relative w-full max-w-xl bg-stone-950 border border-white/15 rounded-2xl p-6 sm:p-8 shadow-[0_25px_80px_rgba(0,0,0,0.9)] overflow-hidden z-10"
        >
          <div className="absolute top-0 right-0 w-64 h-64 bg-cyan-500/10 rounded-full blur-3xl pointer-events-none" />

          <button
            onClick={stage === 'processing' ? undefined : onClose}
            disabled={stage === 'processing'}
            aria-label="Close"
            className="absolute top-5 right-5 p-2 rounded-lg bg-white/5 hover:bg-white/10 text-stone-400 hover:text-white transition-colors disabled:opacity-30 disabled:cursor-not-allowed"
          >
            <X className="w-5 h-5" />
          </button>

          {stage === 'input' && (
            <div className="space-y-6">
              <div className="flex items-center gap-3">
                <div className="w-10 h-10 rounded-xl bg-cyan-950 border border-cyan-500/40 flex items-center justify-center text-cyan-400">
                  <Cpu className="w-5 h-5" />
                </div>
                <div>
                  <h3 className="text-xl font-display font-bold text-white">Launch NexuX Repurposer</h3>
                  <p className="text-xs text-stone-400 font-mono">CANONICAL LOCAL-FIRST PIPELINE</p>
                </div>
              </div>

              <form onSubmit={handleStartAnalysis} className="space-y-5">
                <div className="space-y-2">
                  <label className="text-xs font-mono text-stone-300 uppercase tracking-wider block">
                    YouTube Source URL
                  </label>
                  <input
                    type="url"
                    required
                    value={url}
                    onChange={(e) => setUrl(e.target.value)}
                    placeholder="https://youtube.com/watch?v=..."
                    className="w-full bg-black/60 border border-white/15 rounded-xl px-4 py-3 text-sm text-white placeholder-stone-600 focus:outline-none focus:border-cyan-400 transition-colors font-mono"
                  />
                </div>

                <div className="grid grid-cols-2 gap-4">
                  <div className="space-y-2">
                    <label className="text-xs font-mono text-stone-300 uppercase tracking-wider block">Target Clips</label>
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

                  <div className="space-y-2">
                    <label className="text-xs font-mono text-stone-300 uppercase tracking-wider block">Aspect Output</label>
                    <div className="px-3 py-2.5 bg-black/60 border border-white/15 rounded-xl text-xs font-mono text-cyan-300 flex items-center gap-2">
                      <Video className="w-3.5 h-3.5" />
                      <span>9:16 Vertical</span>
                    </div>
                  </div>
                </div>

                <div className="p-4 rounded-xl bg-white/5 border border-white/10 text-xs text-stone-300 space-y-2">
                  <div className="flex items-center justify-between">
                    <span className="font-mono flex items-center gap-2"><Sparkles className="w-3.5 h-3.5 text-cyan-400" />AI editorial ranking</span>
                    <span className="text-emerald-400 font-mono font-bold">LIVE</span>
                  </div>
                  <div className="flex items-center justify-between">
                    <span className="font-mono">Face tracking + auto zoom</span>
                    <span className="text-emerald-400 font-mono font-bold">ON</span>
                  </div>
                  <div className="flex items-center justify-between">
                    <span className="font-mono">Render QA gate</span>
                    <span className="text-emerald-400 font-mono font-bold">ON</span>
                  </div>
                </div>

                <button
                  type="submit"
                  data-cursor-text="GO"
                  className="w-full py-4 rounded-xl bg-white text-black font-mono font-bold uppercase tracking-widest text-xs hover:bg-stone-200 transition-all flex items-center justify-center gap-2 shadow-[0_0_25px_rgba(255,255,255,0.4)]"
                >
                  <span>Start Autonomous Slicing</span>
                  <ArrowRight className="w-4 h-4" />
                </button>
              </form>
            </div>
          )}

          {stage === 'processing' && (
            <div className="py-10 space-y-7">
              <div className="relative w-20 h-20 mx-auto">
                <div className="absolute inset-0 rounded-full border-2 border-cyan-400/20 border-t-cyan-400 animate-spin" />
                <div className="absolute inset-2 rounded-full border-2 border-white/20 border-b-white animate-spin" style={{ animationDirection: 'reverse', animationDuration: '1.5s' }} />
                <div className="absolute inset-0 flex items-center justify-center">
                  <Sparkles className="w-6 h-6 text-cyan-400 animate-pulse" />
                </div>
              </div>

              <div className="text-center space-y-2">
                <h4 className="text-lg font-display font-bold text-white">NexuX Engine Processing</h4>
                <p className="text-xs font-mono text-cyan-300 uppercase tracking-wider">
                  {stageLabel(job?.stage ?? 'starting', job?.status ?? 'queued')}
                </p>
                <p className="text-xs font-mono text-stone-400 max-w-sm mx-auto">
                  Job ID: {job?.job_id ?? 'submitting...'}
                </p>
              </div>

              <div className="space-y-2">
                <div className="flex items-center justify-between text-[11px] font-mono text-stone-400">
                  <span>{Math.round(progress)}%</span>
                  <span>canonical backend</span>
                </div>
                <div className="w-full bg-white/10 rounded-full h-2 overflow-hidden">
                  <div className="bg-gradient-to-r from-cyan-400 to-blue-500 h-full transition-[width] duration-500" style={{ width: `${progress}%` }} />
                </div>
              </div>

              <button
                onClick={handleCancel}
                disabled={!job?.job_id || cancelling}
                className="mx-auto flex items-center justify-center gap-2 px-4 py-2.5 rounded-lg border border-red-400/30 text-red-300 hover:bg-red-500/10 disabled:opacity-40 text-xs font-mono uppercase tracking-wider"
              >
                <Square className="w-3.5 h-3.5" />
                {cancelling ? 'Cancelling…' : 'Cancel job'}
              </button>
            </div>
          )}

          {stage === 'done' && job && (
            <div className="space-y-6">
              <div className="text-center space-y-2">
                <div className="w-16 h-16 rounded-full bg-emerald-500/20 border border-emerald-500/50 flex items-center justify-center mx-auto text-emerald-400 shadow-[0_0_30px_rgba(16,185,129,0.3)]">
                  <CheckCircle2 className="w-8 h-8" />
                </div>
                <h4 className="text-2xl font-display font-bold text-white">{job.clips.length} Clips Ready</h4>
                <p className="text-xs font-mono text-stone-400">Backend render + QA completed for job {job.job_id}</p>
              </div>

              {firstClip && (
                <video
                  src={firstClip}
                  controls
                  playsInline
                  className="w-full max-h-[55vh] object-contain rounded-xl bg-black border border-white/10"
                />
              )}

              <div className="grid grid-cols-1 sm:grid-cols-2 gap-3">
                <a
                  href={nexuxApi.downloadUrl(job.job_id)}
                  className="py-3 rounded-xl bg-cyan-400 text-black font-mono font-bold uppercase tracking-widest text-xs hover:bg-cyan-300 transition-all flex items-center justify-center gap-2"
                >
                  <Download className="w-4 h-4" />
                  Download MP4
                </a>
                {firstClip ? (
                  <a
                    href={firstClip}
                    target="_blank"
                    rel="noreferrer"
                    className="py-3 rounded-xl border border-white/15 text-white font-mono font-bold uppercase tracking-widest text-xs hover:bg-white/5 transition-all flex items-center justify-center gap-2"
                  >
                    <ExternalLink className="w-4 h-4" />
                    Open output
                  </a>
                ) : null}
              </div>

              <button
                onClick={handleReset}
                className="w-full py-3 rounded-xl border border-white/10 text-stone-300 hover:text-white hover:bg-white/5 transition-all flex items-center justify-center gap-2 text-xs font-mono uppercase tracking-wider"
              >
                Run another source
                <ArrowRight className="w-4 h-4" />
              </button>
            </div>
          )}

          {stage === 'error' && (
            <div className="py-6 space-y-6 text-center">
              <div className="w-16 h-16 rounded-full bg-red-500/15 border border-red-500/30 flex items-center justify-center mx-auto text-red-300">
                <AlertTriangle className="w-8 h-8" />
              </div>
              <div className="space-y-2">
                <h4 className="text-xl font-display font-bold text-white">NexuX could not complete the job</h4>
                <p className="text-xs font-mono text-stone-400 break-words">{error || 'Unknown engine error.'}</p>
              </div>
              {job?.job_id && <p className="text-[11px] font-mono text-stone-600">Job: {job.job_id}</p>}
              <button
                onClick={() => { stopPolling(); setStage('input'); setError(''); }}
                className="w-full py-3 rounded-xl bg-white text-black font-mono font-bold uppercase tracking-widest text-xs hover:bg-stone-200 transition-all"
              >
                Try again
              </button>
            </div>
          )}
        </motion.div>
      </div>
    </AnimatePresence>
  );
};
