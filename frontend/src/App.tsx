/**
 * NexuX V9.7 — App shell.
 * Clean view-based architecture (no modals-as-pages), SpaceX-style restraint:
 * Studio (create flows), Compare (multi-job), Settings.
 * All heavy sections render inside a single scroll container — no custom
 * scroll hijacking, no global cursor overrides, no particle systems.
 */
import React, { useState, useEffect, useCallback, Suspense, lazy, useRef } from 'react';
import { AppHeader } from './components/AppHeader';

const HeroCompact = lazy(() => import('./components/HeroCompact'));
const JobCompareView = lazy(() => import('./components/JobCompareView'));
const SubtitleEngineStudio = lazy(() => import('./components/SubtitleEngineStudio').then(m => ({ default: m.SubtitleEngineStudio })));
const StudioGenerate = lazy(() => import('./components/StudioGenerate'));
const SettingsPage = lazy(() => import('./components/SettingsPage'));
const nexuxApiHealth = () => import('./api/nexuxApi').then(m => m.nexuxApi.health());

type View = 'studio' | 'compare' | 'settings';

interface Toast {
  id: number;
  kind: 'success' | 'error' | 'info';
  message: string;
}

const LazyFallback = () => (
  <div className="min-h-[180px] flex items-center justify-center">
    <div className="w-6 h-6 border-2 border-white/20 border-t-violet-500 rounded-full animate-spin" />
  </div>
);

export default function App() {
  const [view, setView] = useState<View>('studio');
  const [healthOk, setHealthOk] = useState<boolean | null>(null);
  const [toasts, setToasts] = useState<Toast[]>([]);
  const toastId = useRef(0);

  useEffect(() => {
    let alive = true;
    nexuxApiHealth()
      .then(() => alive && setHealthOk(true))
      .catch(() => alive && setHealthOk(false));
    return () => { alive = false; };
  }, []);

  const showToast = useCallback((kind: Toast['kind'], message: string) => {
    const id = ++toastId.current;
    setToasts((t) => [...t, { id, kind, message }]);
    setTimeout(() => setToasts((t) => t.filter((x) => x.id !== id)), 4000);
  }, []);

  const goToStudioFlow = useCallback(() => {
    setView('studio');
    requestAnimationFrame(() => {
      document.getElementById('studio-generate')?.scrollIntoView({ behavior: 'smooth' });
    });
  }, []);

  return (
    <div className="min-h-screen bg-[#0a0a0b] text-white">
      <AppHeader
        currentView={view}
        onNavigate={(v) => {
          setView(v);
        }}
        healthOk={healthOk}
      />

      {/* Toast stack — top-right under header */}
      <div className="fixed top-20 right-4 z-[60] flex flex-col gap-2 max-w-sm" role="status">
        {toasts.map((t) => (
          <div
            key={t.id}
            className={`rounded-lg border px-4 py-2.5 text-sm font-medium shadow-lg ${
              t.kind === 'success'
                ? 'border-emerald-500/30 bg-emerald-950/90 text-emerald-200'
                : t.kind === 'error'
                ? 'border-red-500/30 bg-red-950/90 text-red-200'
                : 'border-white/15 bg-neutral-900/95 text-zinc-200'
            }`}
          >
            {t.message}
          </div>
        ))}
      </div>

      {view === 'studio' && (
        <>
          <Suspense fallback={<LazyFallback />}>
            <HeroCompact onStart={goToStudioFlow} />
          </Suspense>

          <Suspense fallback={<LazyFallback />}>
            <StudioGenerate />
          </Suspense>

          <section id="how-it-works" className="py-16 px-4 sm:px-6 border-t border-white/[0.06]">
            <div className="max-w-5xl mx-auto">
              <p className="section-label mb-3">How it works</p>
              <h2 className="font-display text-2xl sm:text-3xl font-bold mb-8">
                Three steps. Zero cloud.
              </h2>
              <div className="grid sm:grid-cols-3 gap-4">
                {[
                  { n: '01', t: 'Paste link or keyword', d: 'YouTube URL for Podcast Mode, or a single keyword for AI Creative Mode.' },
                  { n: '02', t: 'AI finds the moments', d: '8-dimension scoring, hook detection, and critic review pick the strongest segments.' },
                  { n: '03', t: 'Export & post', d: '9:16 clips with karaoke subtitles, viral titles, and hashtags — rendered locally with FFmpeg.' },
                ].map((s) => (
                  <div key={s.n} className="card p-5">
                    <span className="text-xs font-mono2 text-violet-400">{s.n}</span>
                    <h3 className="mt-2 font-semibold text-white text-sm">{s.t}</h3>
                    <p className="mt-1 text-sm text-zinc-400 leading-relaxed">{s.d}</p>
                  </div>
                ))}
              </div>
            </div>
          </section>

          <Suspense fallback={<LazyFallback />}>
            <SubtitleEngineStudio />
          </Suspense>

          <footer className="border-t border-white/[0.06] py-10 px-4 sm:px-6">
            <div className="max-w-7xl mx-auto flex flex-col sm:flex-row items-center justify-between gap-4">
              <span className="text-sm text-zinc-500">
                NexuX v9.7 — local-first AI video repurposing
              </span>
              <div className="flex items-center gap-5 text-sm text-zinc-500">
                <button onClick={() => setView('settings')} className="hover:text-white transition-colors">
                  Settings
                </button>
                <a
                  href="https://github.com/jorsbanana-nexux/NexuX"
                  target="_blank"
                  rel="noreferrer"
                  className="hover:text-white transition-colors"
                >
                  GitHub
                </a>
              </div>
            </div>
          </footer>
        </>
      )}

      {view === 'compare' && (
        <div className="pt-16">
          <Suspense fallback={<LazyFallback />}>
            <JobCompareView />
          </Suspense>
        </div>
      )}

      {view === 'settings' && (
        <Suspense fallback={<LazyFallback />}>
          <SettingsPage showToast={showToast} />
        </Suspense>
      )}

    </div>
  );
}
