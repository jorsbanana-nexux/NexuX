/**
 * @license
 * SPDX-License-Identifier: Apache-2.0
 */

import React, { useState, useEffect, Suspense, lazy } from 'react';
import { CustomCursor } from './components/CustomCursor';
import { CosmicAtmosphere } from './components/CosmicAtmosphere';
import { Rocket4KVideoBackground, SPACE_4K_VARIANTS } from './components/Rocket4KVideoBackground';
import { Navbar } from './components/Navbar';
import { HeroSection } from './components/HeroSection';
import { MagneticElement } from './components/MagneticElement';
import { CosmicThemeMode } from './components/AudioCosmicControls';
import { WarpSpeedTransition } from './components/WarpSpeedTransition';
import { Cpu } from 'lucide-react';
import { sound } from './utils/soundEffects';
import { initLenis, destroyLenis } from './utils/lenis';

// Lazy-loaded below-the-fold components (reduces initial bundle)
const PostRenderFlow = lazy(() => import('./components/PostRenderFlow').then(m => ({ default: m.PostRenderFlow })));
const JobCompareView = lazy(() => import('./components/JobCompareView'));
const SubtitleEngineStudio = lazy(() => import('./components/SubtitleEngineStudio').then(m => ({ default: m.SubtitleEngineStudio })));
const ShowcaseSection = lazy(() => import('./components/ShowcaseSection').then(m => ({ default: m.ShowcaseSection })));
const TryModal = lazy(() => import('./components/TryModal').then(m => ({ default: m.TryModal })));
const VideoModal = lazy(() => import('./components/VideoModal').then(m => ({ default: m.VideoModal })));
const CosmicSpaceDock = lazy(() => import('./components/CosmicSpaceDock').then(m => ({ default: m.CosmicSpaceDock })));

// Lightweight fallback for lazy components
const LazyFallback = () => (
  <div className="min-h-[200px] flex items-center justify-center">
    <div className="w-8 h-8 border-2 border-cyan-400/30 border-t-cyan-400 rounded-full animate-spin" />
  </div>
);

export default function App() {
  const [isTryModalOpen, setIsTryModalOpen] = useState(false);
  const [isVideoModalOpen, setIsVideoModalOpen] = useState(false);
  
  // Cosmic Theme Mode: 'nebula' (vibrant aura) vs 'deep-space' (pure OLED void)
  const [cosmicTheme, setCosmicTheme] = useState<CosmicThemeMode>('nebula');
  
  // 10 4K Space Background Controller State (5s interval as requested)
  const [spaceTrackIndex, setSpaceTrackIndex] = useState(0);
  const [isAutoCycle, setIsAutoCycle] = useState(true);

  // Warp Speed Transition State
  const [warpActive, setWarpActive] = useState(false);
  const [warpLabel, setWarpLabel] = useState('WARP DRIVE ENGAGED');

  // Initialize Lenis Momentum Smooth Scrolling & GSAP integration
  useEffect(() => {
    const lenis = initLenis();
    return () => {
      destroyLenis();
    };
  }, []);

  // 5-Second Rapid Space Cycle Timer (Requested by User)
  useEffect(() => {
    if (!isAutoCycle) return;
    const timer = setInterval(() => {
      setSpaceTrackIndex((prev) => (prev + 1) % SPACE_4K_VARIANTS.length);
    }, 5000);

    return () => clearInterval(timer);
  }, [isAutoCycle]);

  const triggerWarp = (label: string = 'LIGHTSPEED ENGAGED // 躍進モード') => {
    setWarpLabel(label);
    setWarpActive(true);
  };

  return (
    <div className="relative min-h-screen bg-transparent text-white selection:bg-cyan-500/30 selection:text-cyan-200">
      {/* 1. Dynamic 4K SpaceX / Elon Musk Rocket Rotating Video Background with 10 Space Variants & 5s Fast Auto-Cycle */}
      <Rocket4KVideoBackground 
        opacity={cosmicTheme === 'deep-space' ? 0.7 : 0.85} 
        currentIndex={spaceTrackIndex}
        onIndexChange={(idx) => setSpaceTrackIndex(idx)}
      />

      {/* 2. Interactive Cosmic Atmosphere: Parallax Starfield & Aurora Stardust Overlays */}
      <CosmicAtmosphere theme={cosmicTheme} enableParticles={true} />

      {/* 3. Custom Glowing Star-Trail Cursor with Magnetic Trailing Effect */}
      <CustomCursor />

      {/* 4. Transparent Astronaut Glassmorphism Navbar with Magnetic Links */}
      <Navbar
        onOpenTryModal={() => {
          sound.playClick();
          setIsTryModalOpen(true);
        }}
      />

      {/* 5. Hero Section with Orbital Rotations & SpaceX Parallax Video Background */}
      <HeroSection
        onOpenTryModal={() => setIsTryModalOpen(true)}
        onOpenDemoVideo={() => setIsVideoModalOpen(true)}
      />

      {/* 6. Dual-Mode Flow: Mode Selector → Podcast Console (Spaceship) or AI Creative Console (Mode 2) */}
      <Suspense fallback={<LazyFallback />}>
        <PostRenderFlow />
      </Suspense>

      {/* 6.5 Multi-Job Compare Dashboard — cross-job quality matrix (beyond Opus Clip) */}
      <Suspense fallback={<LazyFallback />}>
        <JobCompareView />
      </Suspense>

      {/* 7. Subtitle Engine Studio with Word-by-Word, Line-by-Line, Bounce-Zoom & Hormozi, Minimal, Gamer Presets */}
      <Suspense fallback={<LazyFallback />}>
        <SubtitleEngineStudio />
      </Suspense>

      {/* 8. High-Performance Architecture Telemetry with 3D Tilt & Orbital Radar Diagnostics */}
      <Suspense fallback={<LazyFallback />}>
        <ShowcaseSection />
      </Suspense>

      {/* 9. Minimalist, Zero-Clutter Unified Floating Space Dock at Bottom Right */}
      <Suspense fallback={<LazyFallback />}>
        <CosmicSpaceDock
          currentTrackIndex={spaceTrackIndex}
          onTrackSelect={(idx) => setSpaceTrackIndex(idx)}
          isAutoCycle={isAutoCycle}
          onToggleAutoCycle={() => setIsAutoCycle(!isAutoCycle)}
          currentTheme={cosmicTheme}
          onThemeChange={(newTheme) => setCosmicTheme(newTheme)}
          onTriggerWarp={(label) => triggerWarp(label)}
        />
      </Suspense>

      {/* 10. Warp Speed Hyperspace Tunnel Transition */}
      <WarpSpeedTransition
        isActive={warpActive}
        label={warpLabel}
        durationMs={1100}
        onComplete={() => setWarpActive(false)}
      />

      {/* 11. Modern Astronaut Visor Glassmorphism Footer with Magnetic Anchors */}
      <footer className="relative border-t border-white/10 bg-black/80 backdrop-blur-xl py-12 px-6 sm:px-10 z-10 select-none">
        <div className="max-w-6xl mx-auto flex flex-col md:flex-row items-center justify-between gap-6">
          <MagneticElement strength={0.25} radius={60}>
            <div className="flex items-center gap-3">
              <div className="w-8 h-8 rounded-lg bg-white/10 border border-cyan-400/40 text-cyan-300 flex items-center justify-center font-black text-sm shadow-[0_0_15px_rgba(34,211,238,0.25)]">
                <Cpu className="w-4 h-4 text-cyan-300" />
              </div>
              <div className="flex items-baseline gap-2">
                <span className="font-display tracking-[0.25em] font-extrabold text-base text-white">
                  NEXU<span className="text-cyan-400 text-glow-cyan">X</span>
                </span>
                <span className="font-jp text-[10px] font-medium tracking-widest text-stone-500">
                  ネクサス
                </span>
              </div>
            </div>
          </MagneticElement>

          <div className="flex items-center gap-6 text-xs font-mono text-stone-400">
            <MagneticElement strength={0.3} radius={50}>
              <a 
                href="#hero" 
                onClick={() => sound.playClick()}
                className="hover:text-cyan-300 transition-colors py-1 block"
              >
                Overview
              </a>
            </MagneticElement>
            <MagneticElement strength={0.3} radius={50}>
              <a 
                href="#workspace-console" 
                onClick={() => sound.playClick()}
                className="hover:text-cyan-300 transition-colors py-1 block"
              >
                Cockpit
              </a>
            </MagneticElement>
            <MagneticElement strength={0.3} radius={50}>
              <a 
                href="#subtitle-engine" 
                onClick={() => sound.playClick()}
                className="hover:text-cyan-300 transition-colors py-1 block"
              >
                Subtitles
              </a>
            </MagneticElement>
            <MagneticElement strength={0.3} radius={50}>
              <a 
                href="#capabilities" 
                onClick={() => sound.playClick()}
                className="hover:text-cyan-300 transition-colors py-1 block"
              >
                Architecture
              </a>
            </MagneticElement>
          </div>

          <div className="text-[11px] font-mono text-stone-500 flex items-center gap-2">
            <span className="w-1.5 h-1.5 rounded-full bg-emerald-400 animate-pulse" />
            <span>© 2026 NEXUX • Autonomous AI Space Infrastructure</span>
          </div>
        </div>
      </footer>

      {/* Interactive Modals */}
      <Suspense fallback={null}>
        <TryModal
          isOpen={isTryModalOpen}
          onClose={() => setIsTryModalOpen(false)}
        />
      </Suspense>

      <Suspense fallback={null}>
        <VideoModal
          isOpen={isVideoModalOpen}
          onClose={() => setIsVideoModalOpen(false)}
        />
      </Suspense>
    </div>
  );
}
