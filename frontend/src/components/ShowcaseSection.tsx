import React from 'react';
import { 
  Bot, 
  Smartphone, 
  Zap, 
  Cpu,
  Radio,
  Orbit,
  Server,
  Sparkles,
  Shield,
  Gauge
} from 'lucide-react';
import { OrbitalRings } from './OrbitalRings';
import { TiltCard } from './TiltCard';
import { sound } from '../utils/soundEffects';

export const ShowcaseSection: React.FC = () => {
  return (
    <section id="capabilities" className="relative py-24 px-6 sm:px-10 max-w-6xl mx-auto z-10 space-y-20">
      {/* Section Header with Japanese Subtitle */}
      <div className="text-center max-w-2xl mx-auto space-y-3">
        <div className="inline-flex items-center gap-2 px-3.5 py-1 rounded-full border border-purple-500/30 bg-purple-950/20 text-purple-300 font-mono text-[11px] uppercase tracking-widest shadow-[0_0_15px_rgba(168,85,247,0.15)]">
          <Sparkles className="w-3.5 h-3.5 text-purple-400" />
          <span>Core Capabilities // コア機能</span>
        </div>

        <h2 className="text-3xl sm:text-5xl font-display font-bold text-white tracking-tight">
          Next-Gen AI Micro-Engine
        </h2>

        <p className="text-stone-400 text-sm sm:text-base leading-relaxed">
          Hover over each module to engage 3D telemetry tracking and inspect deep-space autonomous pipelines.
        </p>
      </div>

      {/* 3 Core Autonomous Pillars with 3D Card Tilt & Specular Light Reflection */}
      <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
        <TiltCard
          maxTilt={12}
          glareOpacity={0.3}
          data-cursor-text="HOOK AI"
          className="p-8 rounded-2xl hud-glass-panel border border-white/10 spacex-glow-border flex flex-col justify-between h-full group hover:border-cyan-400/50 hover:shadow-[0_0_30px_rgba(34,211,238,0.2)] transition-all cursor-pointer"
        >
          <div onMouseEnter={() => sound.playHover()}>
            <div className="w-12 h-12 rounded-xl bg-cyan-950/40 border border-cyan-400/30 flex items-center justify-center text-cyan-300 mb-6 shadow-[0_0_15px_rgba(34,211,238,0.2)] group-hover:scale-110 group-hover:bg-cyan-500/20 transition-all">
              <Bot className="w-6 h-6" />
            </div>
            <div className="font-jp text-[10px] font-mono text-cyan-400 mb-1">フック自動検出</div>
            <h3 className="text-xl font-display font-bold text-white mb-3 group-hover:text-glow-cyan transition-all">
              Neural Hook Detection
            </h3>
            <p className="text-stone-400 text-xs sm:text-sm leading-relaxed">
              Editorial intelligence analyzes transcript semantics, pitch cadence, and emotional spikes to isolate the clips with maximum retention potential.
            </p>
          </div>
          <div className="mt-6 pt-4 border-t border-white/5 flex items-center justify-between text-[11px] font-mono text-cyan-300">
            <span>ENGINE</span>
            <span className="font-bold">V8.0 MULTIMODAL</span>
          </div>
        </TiltCard>

        <TiltCard
          maxTilt={12}
          glareOpacity={0.3}
          data-cursor-text="REFRAME"
          className="p-8 rounded-2xl hud-glass-panel border border-white/10 spacex-glow-border flex flex-col justify-between h-full group hover:border-purple-400/50 hover:shadow-[0_0_30px_rgba(192,132,252,0.2)] transition-all cursor-pointer"
        >
          <div onMouseEnter={() => sound.playHover()}>
            <div className="w-12 h-12 rounded-xl bg-purple-950/40 border border-purple-400/30 flex items-center justify-center text-purple-300 mb-6 shadow-[0_0_15px_rgba(192,132,252,0.2)] group-hover:scale-110 group-hover:bg-purple-500/20 transition-all">
              <Smartphone className="w-6 h-6" />
            </div>
            <div className="font-jp text-[10px] font-mono text-purple-400 mb-1">話者自動トラッキング</div>
            <h3 className="text-xl font-display font-bold text-white mb-3 group-hover:text-glow-purple transition-all">
              Dynamic 9:16 Reframe
            </h3>
            <p className="text-stone-400 text-xs sm:text-sm leading-relaxed">
              Smart facial and voice tracking dynamically frames the speaker, with adaptive camera paths and auto-zoom for studio-grade composition.
            </p>
          </div>
          <div className="mt-6 pt-4 border-t border-white/5 flex items-center justify-between text-[11px] font-mono text-purple-300">
            <span>FACE TRACKING</span>
            <span className="font-bold">MEDIAPIPE + SAM</span>
          </div>
        </TiltCard>

        <TiltCard
          maxTilt={12}
          glareOpacity={0.3}
          data-cursor-text="CAPTIONS"
          className="p-8 rounded-2xl hud-glass-panel border border-white/10 spacex-glow-border flex flex-col justify-between h-full group hover:border-amber-400/50 hover:shadow-[0_0_30px_rgba(251,191,36,0.2)] transition-all cursor-pointer"
        >
          <div onMouseEnter={() => sound.playHover()}>
            <div className="w-12 h-12 rounded-xl bg-amber-950/40 border border-amber-400/30 flex items-center justify-center text-amber-300 mb-6 shadow-[0_0_15px_rgba(251,191,36,0.2)] group-hover:scale-110 group-hover:bg-amber-500/20 transition-all">
              <Zap className="w-6 h-6" />
            </div>
            <div className="font-jp text-[10px] font-mono text-amber-400 mb-1">キネティック字幕生成</div>
            <h3 className="text-xl font-display font-bold text-white mb-3 group-hover:text-glow-amber transition-all">
              Kinetic Subtitles
            </h3>
            <p className="text-stone-400 text-xs sm:text-sm leading-relaxed">
              Animated captions with keyword highlights, dynamic color pulses, and emoji placement. 18+ presets including Hormozi, MrBeast, and Cyberpunk styles.
            </p>
          </div>
          <div className="mt-6 pt-4 border-t border-white/5 flex items-center justify-between text-[11px] font-mono text-amber-300">
            <span>SUBTITLE ENGINE</span>
            <span className="font-bold">ASS + FFMPEG</span>
          </div>
        </TiltCard>
      </div>

      {/* Architecture Telemetry */}
      <TiltCard
        maxTilt={5}
        glareOpacity={0.15}
        className="relative p-8 sm:p-12 rounded-2xl hud-glass-panel border border-white/15 spacex-glow-border space-y-10 overflow-hidden"
      >
        {/* Orbital Satellite Radar Ring in background */}
        <div className="absolute -right-16 -top-16 opacity-30 pointer-events-none">
          <OrbitalRings size={340} showSatellites={true} pulseCenter={false} />
        </div>

        <div className="relative z-10 flex flex-col sm:flex-row sm:items-end justify-between gap-4 border-b border-white/10 pb-6">
          <div>
            <span className="text-[11px] font-mono text-cyan-400 uppercase tracking-widest block mb-1 text-glow-cyan">
              SYSTEM ARCHITECTURE // アーキテクチャ
            </span>
            <h3 className="text-2xl sm:text-4xl font-display font-bold text-white">
              Engineered for Local-First Production
            </h3>
          </div>
          <div className="text-xs font-mono text-stone-400 flex items-center gap-2">
            <span className="w-2 h-2 rounded-full bg-emerald-400 animate-pulse"></span>
            <span>Canonical V8.0 • No B-Roll • Zero Cloud Cost</span>
          </div>
        </div>

        <div className="relative z-10 grid grid-cols-2 md:grid-cols-4 gap-6 sm:gap-8">
          <div className="space-y-1.5 p-4 rounded-xl bg-black/40 border border-white/5 hover:border-cyan-400/40 transition-colors">
            <div className="flex items-center gap-2 text-cyan-300 mb-1">
              <Cpu className="w-4 h-4" />
              <span className="text-xs font-mono uppercase tracking-wider font-semibold">Local Whisper</span>
            </div>
            <p className="text-xs text-stone-400 leading-relaxed">
              Faster-Whisper transcription runs locally. No cloud API calls required.
            </p>
          </div>

          <div className="space-y-1.5 p-4 rounded-xl bg-black/40 border border-white/5 hover:border-purple-400/40 transition-colors">
            <div className="flex items-center gap-2 text-purple-300 mb-1">
              <Shield className="w-4 h-4" />
              <span className="text-xs font-mono uppercase tracking-wider font-semibold">Quality Gate</span>
            </div>
            <p className="text-xs text-stone-400 leading-relaxed">
              FFmpeg render QA inspects every output before marking a job complete.
            </p>
          </div>

          <div className="space-y-1.5 p-4 rounded-xl bg-black/40 border border-white/5 hover:border-amber-400/40 transition-colors">
            <div className="flex items-center gap-2 text-amber-300 mb-1">
              <Gauge className="w-4 h-4" />
              <span className="text-xs font-mono uppercase tracking-wider font-semibold">Editorial AI</span>
            </div>
            <p className="text-xs text-stone-400 leading-relaxed">
              Multimodal editorial ranking with genre intelligence and critic revision.
            </p>
          </div>

          <div className="space-y-1.5 p-4 rounded-xl bg-black/40 border border-white/5 hover:border-white/40 transition-colors">
            <div className="flex items-center gap-2 text-white mb-1">
              <Server className="w-4 h-4" />
              <span className="text-xs font-mono uppercase tracking-wider font-semibold">Targeted Retrieval</span>
            </div>
            <p className="text-xs text-stone-400 leading-relaxed">
              Downloads only the segments it needs — no full video fetch required.
            </p>
          </div>
        </div>
      </TiltCard>
    </section>
  );
};
