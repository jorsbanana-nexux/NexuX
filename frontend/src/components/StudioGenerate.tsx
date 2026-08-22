/**
 * NexuX V9.7 — StudioGenerate
 * Unified generation surface (replaces the SpaceshipConsole flow).
 * Podcast Mode inline + AI Creative Mode embedded — one clean panel.
 */
import React, { useEffect, useRef, useState } from 'react';
import {
  Link2, Sparkles, Loader2, CheckCircle2, AlertTriangle,
  Download, Square, Scissors, Upload as UploadIcon,
} from 'lucide-react';
import { nexuxApi, type NexuXJob, type NexuXStatus } from '../api/nexuxApi';
import { Mode2Console } from './Mode2Console';

const TERMINAL: NexuXStatus[] = ['completed', 'failed', 'cancelled', 'interrupted'];
type Mode = 'podcast' | 'creative';

export function StudioGenerate() {
  const [mode, setMode] = useState<Mode>('podcast');
  return (
    <section id="studio-generate" className="py-16 px-4 sm:px-6 border-t border-white/[0.06]">
      <div className="max-w-3xl mx-auto">
        <p className="section-label mb-3 text-center">Create</p>
        <div className="card p-6 sm:p-8">
          {/* Mode tabs */}
          <div className="flex rounded-lg bg-white/[0.04] p-1 mb-6" role="tablist">
            {(
              [
                { id: 'podcast', label: 'Podcast Mode', icon: Scissors },
                { id: 'creative', label: 'AI Creative', icon: Sparkles },
              ] as const
            ).map(({ id, label, icon: Icon }) => (
              <button
                key={id}
                role="tab"
                aria-selected={mode === id}
                onClick={() => setMode(id)}
                className={`flex-1 flex items-center justify-center gap-2 rounded-md px-4 py-2.5 text-sm font-medium transition-colors ${
                  mode === id
                    ? 'bg-white/[0.08] text-white'
                    : 'text-zinc-400 hover:text-white'
                }`}
              >
                <Icon className="w-4 h-4" />
                {label}
              </button>
            ))}
          </div>

          {mode === 'podcast' ? <PodcastPanel /> : (
            <div className="mode2-embedded">
              <Mode2Console />
            </div>
          )}
        </div>
      </div>
    </section>
  );
}

function PodcastPanel() {
  const [url, setUrl] = useState('');
  const [clipCount, setClipCount] = useState(5);
  const [uploading, setUploading] = useState(false);
  const [job, setJob] = useState<NexuXJob | null>(null);
  const [error, setError] = useState('');
  const pollTimer = useRef<ReturnType<typeof setTimeout> | null>(null);
  const fileRef = useRef<HTMLInputElement>(null);

  const stopPolling = () => {
    if (pollTimer.current) {
      clearTimeout(pollTimer.current);
      pollTimer.current = null;
    }
  };
  useEffect(stopPolling, []);

  const pollJob = async (jobId: string) => {
    try {
      const next = await nexuxApi.job(jobId);
      setJob(next);
      if (TERMINAL.includes(next.status)) return stopPolling();
      pollTimer.current = setTimeout(() => pollJob(jobId), 1500);
    } catch {
      pollTimer.current = setTimeout(() => pollJob(jobId), 3000);
    }
  };

  const submit = async () => {
    const trimmed = url.trim();
    if (!trimmed) {
      setError('Paste a YouTube URL or upload a local video first.');
      return;
    }
    setError('');
    stopPolling();
    try {
      const created = await nexuxApi.generate({
        youtube_url: trimmed,
        target_duration: 60,
        aspect_ratio: '9:16',
        subtitle_style: 'karaoke',
        font: 'Arial',
        font_size: 48,
        primary_color: '#FFFFFF',
        highlight_color: '#FFD700',
        stroke_color: '#000000',
        stroke_width: 2,
        position: 'bottom',
        animation: 'fade',
        auto_zoom: true,
        face_tracking: true,
        clip_count: clipCount,
        language: null,
        normalize_audio: true,
        emoji_enabled: false,
      });
      setJob(created);
      pollJob(created.job_id);
    } catch (e) {
      setJob(null);
      setError((e as Error).message);
    }
  };

  const uploadLocal = async (file: File) => {
    setUploading(true);
    setError('');
    try {
      const uploaded = await nexuxApi.upload(file);
      setUrl(uploaded.local_url);
    } catch (e) {
      setError((e as Error).message);
    } finally {
      setUploading(false);
    }
  };

  const cancel = async () => {
    if (!job) return;
    try {
      await nexuxApi.cancel(job.job_id);
    } catch {
      // already terminal — fine
    }
  };

  const progress = job?.progress ?? 0;
  const running = job && !TERMINAL.includes(job.status);

  return (
    <div>
      {/* URL input + upload */}
      <div className="flex flex-col sm:flex-row gap-3">
        <div className="relative flex-1">
          <Link2 className="absolute left-3 top-1/2 -translate-y-1/2 w-4 h-4 text-zinc-500" />
          <input
            className="input pl-9"
            placeholder="Paste a YouTube URL…"
            value={url}
            onChange={(e) => setUrl(e.target.value)}
            disabled={!!running}
          />
        </div>
        <input
          ref={fileRef}
          type="file"
          accept="video/*"
          className="hidden"
          onChange={(e) => e.target.files?.[0] && uploadLocal(e.target.files[0])}
        />
        <button
          onClick={() => fileRef.current?.click()}
          className="btn btn-secondary"
          disabled={uploading || !!running}
        >
          {uploading ? <Loader2 className="w-4 h-4 animate-spin" /> : <UploadIcon className="w-4 h-4" />}
          Upload local
        </button>
      </div>

      <div className="mt-4 flex flex-col sm:flex-row sm:items-center gap-3">
        <label className="text-xs text-zinc-500" htmlFor="clip-count">Clips</label>
        <select
          id="clip-count"
          className="input sm:w-28"
          value={clipCount}
          onChange={(e) => setClipCount(Number(e.target.value))}
          disabled={!!running}
        >
          {[3, 5, 8, 10].map((n) => <option key={n} value={n}>{n}</option>)}
        </select>
        {running ? (
          <button onClick={cancel} className="btn btn-secondary sm:ml-auto">
            <Square className="w-3.5 h-3.5" /> Cancel
          </button>
        ) : (
          <button onClick={submit} className="btn btn-primary sm:ml-auto">
            Generate clips
          </button>
        )}
      </div>

      {error && (
        <div className="mt-4 flex items-start gap-2 rounded-lg border border-red-500/20 bg-red-500/5 p-3 text-sm text-red-300">
          <AlertTriangle className="w-4 h-4 mt-0.5 shrink-0" />
          <span>{error}</span>
        </div>
      )}

      {job && (
        <div className="mt-6">
          {running ? (
            <div>
              <div className="flex items-center justify-between text-xs text-zinc-500 mb-2">
                <span>{job.stage?.replace(/_/g, ' ') ?? 'processing'}</span>
                <span className="font-mono2">{progress.toFixed(0)}%</span>
              </div>
              <div className="h-1.5 rounded-full bg-white/[0.08] overflow-hidden">
                <div
                  className="h-full bg-violet-500 transition-[width] duration-500"
                  style={{ width: `${progress}%` }}
                />
              </div>
            </div>
          ) : job.status === 'completed' ? (
            <div className="rounded-lg border border-emerald-500/20 bg-emerald-500/5 p-4">
              <div className="flex items-center gap-2 text-emerald-300 font-medium text-sm">
                <CheckCircle2 className="w-4 h-4" />
                Render complete
              </div>
              <div className="mt-3 flex flex-wrap gap-2">
                <a
                  href={nexuxApi.downloadUrl(job.job_id)}
                  className="btn btn-primary text-xs"
                  download
                >
                  <Download className="w-3.5 h-3.5" /> Download all
                </a>
              </div>
            </div>
          ) : (
            <div className="rounded-lg border border-red-500/20 bg-red-500/5 p-4 text-sm text-red-300">
              {job.error || `Job ${job.status}`}
            </div>
          )}
        </div>
      )}
    </div>
  );
}

export default StudioGenerate;
