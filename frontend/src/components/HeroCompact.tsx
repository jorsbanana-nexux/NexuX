/**
 * NexuX V9.7 — HeroCompact
 * Opus Pro-style hero: bold statement, one value proposition, one CTA.
 * No video backgrounds, no particles — pure typography. Loads instantly.
 */
import React from 'react';
import { ArrowRight, Scissors, Sparkles } from 'lucide-react';

interface HeroCompactProps {
  onStart: () => void;
}

export function HeroCompact({ onStart }: HeroCompactProps) {
  return (
    <section className="pt-32 pb-16 sm:pt-40 sm:pb-20 px-4 sm:px-6">
      <div className="max-w-4xl mx-auto text-center">
        <div className="inline-flex items-center gap-2 px-3 py-1.5 rounded-full border border-white/10 text-xs font-medium text-zinc-400 mb-6">
          <span className="w-1.5 h-1.5 rounded-full bg-violet-500" />
          Local-first AI video repurposing — zero cloud cost
        </div>

        <h1 className="font-display text-4xl sm:text-6xl font-bold tracking-tight text-white leading-[1.05]">
          Turn long videos into
          <br />
          <span className="text-violet-500">viral clips.</span>
        </h1>

        <p className="mt-5 text-base sm:text-lg text-zinc-400 max-w-2xl mx-auto leading-relaxed">
          Podcast Mode clips your interviews automatically. AI Creative Mode
          builds compilations from a single keyword. Everything runs on your
          machine — no uploads, no subscriptions.
        </p>

        <div className="mt-8 flex flex-col sm:flex-row items-center justify-center gap-3">
          <button
            onClick={onStart}
            className="btn btn-primary w-full sm:w-auto text-base px-6 py-3"
          >
            Start clipping
            <ArrowRight className="w-4 h-4" />
          </button>
          <a
            href="#how-it-works"
            className="btn btn-secondary w-full sm:w-auto text-base px-6 py-3"
          >
            How it works
          </a>
        </div>

        {/* Dual-mode quick facts */}
        <div className="mt-14 grid sm:grid-cols-2 gap-3 max-w-2xl mx-auto text-left">
          <div className="card card-hover p-5">
            <div className="w-9 h-9 rounded-lg bg-white/[0.06] flex items-center justify-center mb-3">
              <Scissors className="w-4 h-4 text-violet-400" />
            </div>
            <h3 className="font-semibold text-white text-sm">Podcast Mode</h3>
            <p className="mt-1 text-sm text-zinc-400 leading-relaxed">
              Paste a YouTube link. Get ready-to-post 9:16 clips with karaoke
              subtitles and viral titles.
            </p>
          </div>
          <div className="card card-hover p-5">
            <div className="w-9 h-9 rounded-lg bg-white/[0.06] flex items-center justify-center mb-3">
              <Sparkles className="w-4 h-4 text-violet-400" />
            </div>
            <h3 className="font-semibold text-white text-sm">AI Creative Mode</h3>
            <p className="mt-1 text-sm text-zinc-400 leading-relaxed">
              Type one keyword. NexuX finds the best moments across videos and
              compiles them into a narrated short.
            </p>
          </div>
        </div>
      </div>
    </section>
  );
}

export default HeroCompact;
