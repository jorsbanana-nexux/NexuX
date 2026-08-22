/**
 * NexuX V9.7 — SettingsPage
 * Full settings surface: transcription (WhisperX model manager), network,
 * and system preferences. Clean two-column layout, auto-save on change,
 * model download with live progress polling.
 */
import React, { useEffect, useState, useCallback, useRef } from 'react';
import {
  CheckCircle2, Download, Loader2, RefreshCw, RotateCcw,
  AlertTriangle, Mic2, Network, Cpu,
} from 'lucide-react';
import {
  settingsApi, NexuxSettings, ModelInfo, PreloadStatus,
} from '../api/settingsApi';

interface SettingsPageProps {
  showToast: (kind: 'success' | 'error' | 'info', msg: string) => void;
}

export function SettingsPage({ showToast }: SettingsPageProps) {
  const [settings, setSettings] = useState<NexuxSettings | null>(null);
  const [variants, setVariants] = useState<Record<string, { label: string; size_approx: string; description: string }>>({});
  const [models, setModels] = useState<ModelInfo[]>([]);
  const [whisperxInstalled, setWhisperxInstalled] = useState(false);
  const [hfTokenSet, setHfTokenSet] = useState(false);
  const [loading, setLoading] = useState(true);
  const [saving, setSaving] = useState(false);
  const [preloadJobs, setPreloadJobs] = useState<Record<string, PreloadStatus>>({});
  const pollRef = useRef<Record<string, ReturnType<typeof setInterval>>>({});

  const loadAll = useCallback(async () => {
    try {
      const [s, m] = await Promise.all([settingsApi.get(), settingsApi.models()]);
      setSettings(s.settings);
      setVariants(s.variants);
      setHfTokenSet(s.env.HF_TOKEN_set);
      setModels(m.models);
      setWhisperxInstalled(m.whisperx_installed);
      setPreloadJobs(m.preload);
    } catch (e) {
      showToast('error', `Failed to load settings: ${(e as Error).message}`);
    } finally {
      setLoading(false);
    }
  }, [showToast]);

  useEffect(() => {
    loadAll();
    const polls = pollRef.current;
    return () => Object.values(polls).forEach(clearInterval);
  }, [loadAll]);

  const save = useCallback(async (patch: Partial<NexuxSettings>) => {
    setSaving(true);
    try {
      const r = await settingsApi.patch(patch);
      setSettings(r.settings);
      showToast('success', 'Settings saved');
      // Refresh model "active" flags after model change
      const m = await settingsApi.models();
      setModels(m.models);
    } catch (e) {
      showToast('error', `Save failed: ${(e as Error).message}`);
    } finally {
      setSaving(false);
    }
  }, [showToast]);

  const startPreload = useCallback(async (variant: string) => {
    const jobId = `preload_${variant}`;
    try {
      const r = await settingsApi.preload(variant, !whisperxInstalled);
      showToast('info', `Downloading ${variant} — you can keep working.`);
      setPreloadJobs((p) => ({ ...p, [r.job]: { status: 'downloading', variant, message: 'Starting...' } }));
      pollRef.current[jobId] = setInterval(async () => {
        try {
          const st = await settingsApi.preloadStatus(jobId);
          setPreloadJobs((p) => ({ ...p, [jobId]: st }));
          if (st.status === 'done' || st.status === 'error') {
            clearInterval(pollRef.current[jobId]);
            delete pollRef.current[jobId];
            if (st.status === 'done') {
              showToast('success', `${variant} downloaded — ready to use`);
              const m = await settingsApi.models();
              setModels(m.models);
              setWhisperxInstalled(m.whisperx_installed);
            } else {
              showToast('error', `Download failed: ${st.message}`);
            }
          }
        } catch {
          clearInterval(pollRef.current[jobId]);
          delete pollRef.current[jobId];
        }
      }, 2000);
    } catch (e) {
      showToast('error', `Preload failed: ${(e as Error).message}`);
    }
  }, [whisperxInstalled, showToast]);

  const resetAll = useCallback(async () => {
    try {
      const r = await settingsApi.reset();
      setSettings(r.settings);
      showToast('success', 'Settings reset to defaults');
      const m = await settingsApi.models();
      setModels(m.models);
    } catch (e) {
      showToast('error', `Reset failed: ${(e as Error).message}`);
    }
  }, [showToast]);

  if (loading || !settings) {
    return (
      <div className="pt-32 pb-20 px-4 max-w-5xl mx-auto flex items-center justify-center min-h-[50vh]">
        <Loader2 className="w-6 h-6 animate-spin text-zinc-500" />
      </div>
    );
  }

  const isPreloading = (id: string) =>
    preloadJobs[`preload_${id}`]?.status === 'downloading';

  return (
    <div className="pt-24 pb-20 px-4 sm:px-6 max-w-5xl mx-auto">
      {/* Header */}
      <div className="flex items-center justify-between mb-8">
        <div>
          <h1 className="font-display text-2xl sm:text-3xl font-bold text-white">Settings</h1>
          <p className="mt-1 text-sm text-zinc-400">
            Changes save automatically and take effect on the next job.
          </p>
        </div>
        <div className="flex items-center gap-2">
          {saving && <Loader2 className="w-4 h-4 animate-spin text-zinc-500" />}
          <button onClick={loadAll} className="btn btn-ghost p-2" title="Reload">
            <RefreshCw className="w-4 h-4" />
          </button>
          <button onClick={resetAll} className="btn btn-ghost text-sm" title="Reset to defaults">
            <RotateCcw className="w-4 h-4" />
            <span className="hidden sm:inline">Reset</span>
          </button>
        </div>
      </div>

      <div className="space-y-6">
        {/* ── Transcription ── */}
        <section className="card p-6">
          <div className="flex items-center gap-3 mb-5">
            <div className="w-9 h-9 rounded-lg bg-violet-500/10 flex items-center justify-center">
              <Mic2 className="w-4 h-4 text-violet-400" />
            </div>
            <div>
              <h2 className="font-semibold text-white">Transcription</h2>
              <p className="text-xs text-zinc-500">WhisperX engine — used when YouTube auto-captions are unavailable</p>
            </div>
          </div>

          {!whisperxInstalled && (
            <div className="mb-5 flex items-start gap-3 rounded-lg border border-amber-500/20 bg-amber-500/5 p-4">
              <AlertTriangle className="w-4 h-4 text-amber-400 mt-0.5 shrink-0" />
              <div className="text-sm">
                <p className="text-amber-200 font-medium">WhisperX not installed</p>
                <p className="text-zinc-400 mt-0.5">
                  Transcription falls back to YouTube auto-captions only. Downloading a
                  model below will install WhisperX automatically.
                </p>
              </div>
            </div>
          )}

          {/* Model variants — 3 curated options */}
          <p className="section-label mb-3">WhisperX model</p>
          <div className="grid sm:grid-cols-3 gap-3 mb-6">
            {models.map((m) => {
              const preloading = isPreloading(m.id);
              const status = preloadJobs[`preload_${m.id}`];
              return (
                <div
                  key={m.id}
                  className={`rounded-xl border p-4 transition-colors ${
                    m.active
                      ? 'border-violet-500/50 bg-violet-500/[0.06]'
                      : 'border-white/[0.08] bg-white/[0.02]'
                  }`}
                >
                  <div className="flex items-center justify-between">
                    <span className="font-semibold text-white text-sm">{variants[m.id]?.label ?? m.id}</span>
                    <span className="text-[10px] text-zinc-500 font-mono">{m.size_approx}</span>
                  </div>
                  <p className="mt-1 text-xs text-zinc-400 leading-relaxed min-h-[2.5rem]">
                    {variants[m.id]?.description}
                  </p>

                  <div className="mt-3 flex items-center gap-2">
                    {m.active ? (
                      <span className="inline-flex items-center gap-1 text-xs font-medium text-violet-400">
                        <CheckCircle2 className="w-3.5 h-3.5" /> Active
                      </span>
                    ) : m.downloaded ? (
                      <button
                        onClick={() => save({ transcription_model: m.id })}
                        className="btn btn-secondary text-xs px-3 py-1.5"
                      >
                        Apply
                      </button>
                    ) : (
                      <span className="text-xs text-zinc-500">Not downloaded</span>
                    )}

                    {!m.downloaded && (
                      <button
                        onClick={() => startPreload(m.id)}
                        disabled={preloading}
                        className="btn btn-primary text-xs px-3 py-1.5 ml-auto"
                      >
                        {preloading ? (
                          <>
                            <Loader2 className="w-3.5 h-3.5 animate-spin" />
                            {status?.message ?? 'Downloading'}
                          </>
                        ) : (
                          <>
                            <Download className="w-3.5 h-3.5" />
                            Download
                          </>
                        )}
                      </button>
                    )}
                  </div>

                  {status?.status === 'error' && (
                    <p className="mt-2 text-xs text-red-400 break-words">{status.message}</p>
                  )}
                </div>
              );
            })}
          </div>

          {/* Language + advanced */}
          <div className="grid sm:grid-cols-2 gap-4">
            <div>
              <label className="section-label block mb-2" htmlFor="set-language">Language</label>
              <select
                id="set-language"
                className="input"
                value={settings.language ?? ''}
                onChange={(e) => save({ language: e.target.value || null })}
              >
                <option value="">Auto-detect</option>
                <option value="en">English</option>
                <option value="id">Indonesian</option>
                <option value="es">Spanish</option>
                <option value="ja">Japanese</option>
              </select>
            </div>
            <div>
              <label className="section-label block mb-2" htmlFor="set-batch">Batch size</label>
              <select
                id="set-batch"
                className="input"
                value={settings.batch_size}
                onChange={(e) => save({ batch_size: Number(e.target.value) })}
              >
                {[4, 8, 16, 32].map((n) => (
                  <option key={n} value={n}>{n}{n === 16 ? ' (default)' : ''}</option>
                ))}
              </select>
              <p className="mt-1.5 text-xs text-zinc-500">Higher = faster on GPU. Lower if you run out of memory.</p>
            </div>
          </div>

          <div className="mt-4 flex flex-col gap-3">
            <Toggle
              checked={settings.word_timestamps}
              onChange={(v) => save({ word_timestamps: v })}
              label="Word-level timestamps"
              hint="Karaoke-precise subtitle alignment (recommended)."
            />
            <Toggle
              checked={settings.diarization}
              onChange={(v) => save({ diarization: v })}
              label="Speaker diarization"
              hint={hfTokenSet
                ? 'Identifies who speaks when (pyannote via HF_TOKEN).'
                : 'Requires HF_TOKEN env var — currently not set.'}
              disabled={!hfTokenSet}
            />
          </div>
        </section>

        {/* ── Network ── */}
        <section className="card p-6">
          <div className="flex items-center gap-3 mb-5">
            <div className="w-9 h-9 rounded-lg bg-violet-500/10 flex items-center justify-center">
              <Network className="w-4 h-4 text-violet-400" />
            </div>
            <div>
              <h2 className="font-semibold text-white">Network</h2>
              <p className="text-xs text-zinc-500">Anti-block settings for YouTube downloads</p>
            </div>
          </div>

          <div className="grid sm:grid-cols-2 gap-4">
            <div>
              <label className="section-label block mb-2" htmlFor="set-proxy">Proxy URL</label>
              <input
                id="set-proxy"
                className="input font-mono2 text-xs"
                placeholder="socks5://127.0.0.1:1080"
                value={settings.proxy_url}
                onChange={(e) => setSettings({ ...settings, proxy_url: e.target.value })}
                onBlur={(e) => save({ proxy_url: e.target.value.trim() })}
              />
              <p className="mt-1.5 text-xs text-zinc-500">
                Routes all yt-dlp traffic. Use when your network blocks googlevideo.com.
              </p>
            </div>
            <div>
              <label className="section-label block mb-2" htmlFor="set-clients">Player clients</label>
              <input
                id="set-clients"
                className="input font-mono2 text-xs"
                placeholder="android,ios,web_embedded"
                value={settings.player_clients}
                onChange={(e) => setSettings({ ...settings, player_clients: e.target.value })}
                onBlur={(e) => save({ player_clients: e.target.value.trim() })}
              />
              <p className="mt-1.5 text-xs text-zinc-500">
                YouTube client emulation for HTTP 403 blocks. Empty = yt-dlp default.
              </p>
            </div>
          </div>
        </section>

        {/* ── System ── */}
        <section className="card p-6">
          <div className="flex items-center gap-3 mb-5">
            <div className="w-9 h-9 rounded-lg bg-violet-500/10 flex items-center justify-center">
              <Cpu className="w-4 h-4 text-violet-400" />
            </div>
            <div>
              <h2 className="font-semibold text-white">System</h2>
              <p className="text-xs text-zinc-500">Self-maintenance behavior</p>
            </div>
          </div>

          <Toggle
            checked={settings.auto_update_ytdlp}
            onChange={(v) => save({ auto_update_ytdlp: v })}
            label="Auto-update yt-dlp"
            hint="Background self-update at startup + on HTTP 403. Disable for air-gapped setups."
          />
        </section>
      </div>
    </div>
  );
}

/** Accessible toggle switch — used across all boolean settings. */
function Toggle({
  checked, onChange, label, hint, disabled,
}: {
  checked: boolean;
  onChange: (v: boolean) => void;
  label: string;
  hint?: string;
  disabled?: boolean;
}) {
  return (
    <div className={`flex items-start justify-between gap-4 ${disabled ? 'opacity-50' : ''}`}>
      <div>
        <p className="text-sm font-medium text-white">{label}</p>
        {hint && <p className="text-xs text-zinc-500 mt-0.5">{hint}</p>}
      </div>
      <button
        role="switch"
        aria-checked={checked}
        aria-label={label}
        disabled={disabled}
        onClick={() => onChange(!checked)}
        className={`relative inline-flex h-6 w-11 shrink-0 rounded-full transition-colors ${
          checked ? 'bg-violet-600' : 'bg-white/[0.12]'
        }`}
      >
        <span
          className={`inline-block h-5 w-5 transform rounded-full bg-white transition-transform mt-0.5 ${
            checked ? 'translate-x-[22px]' : 'translate-x-0.5'
          }`}
        />
      </button>
    </div>
  );
}

export default SettingsPage;
