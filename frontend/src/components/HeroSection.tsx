import React from 'react';
import { motion } from 'motion/react';
import { Play, ArrowRight, ChevronDown, Sparkles, Rocket } from 'lucide-react';
import { sound } from '../utils/soundEffects';
import { MagneticElement } from './MagneticElement';
import { OrbitalRings } from './OrbitalRings';
import { HoloCyberGlitchText } from './HoloCyberGlitchText';
import { LiquidMagneticButton } from './LiquidMagneticButton';

interface HeroSectionProps {
  onOpenTryModal?: () => void;
  onOpenDemoVideo?: () => void;
}

export const HeroSection: React.FC<HeroSectionProps> = ({ 
  onOpenTryModal, 
  onOpenDemoVideo 
}) => {
  const scrollToConsole = () => {
    sound.playClick();
    const target = document.getElementById('workspace-console') || document.getElementById('engine');
    if (target) {
      target.scrollIntoView({ behavior: 'smooth' });
    }
  };

  return (
    <section 
      id="hero" 
      className="relative min-h-screen w-full flex flex-col justify-between items-center overflow-hidden pt-32 pb-12 select-none bg-transparent"
    >
      {/* 1. Planetary Orbital Rings Animation in Hero Center-Background */}
      <div className="absolute top-1/2 left-1/2 -translate-x-1/2 -translate-y-1/2 pointer-events-none z-0 opacity-60">
        <OrbitalRings size={560} showSatellites={true} pulseCenter={false} />
      </div>

      {/* 2. Top SpaceX & Rocket Flight Identifier Badge */}
      <motion.div
        initial={{ opacity: 0, y: -12 }}
        animate={{ opacity: 1, y: 0 }}
        transition={{ duration: 0.5 }}
        className="relative z-10 px-4 flex items-center gap-3"
      >
        <MagneticElement strength={0.2} radius={50}>
          <div className="inline-flex items-center gap-2 px-4 py-1.5 rounded-full border border-cyan-500/30 bg-cyan-950/30 backdrop-blur-md text-[11px] font-mono tracking-widest text-cyan-200 shadow-[0_0_20px_rgba(34,211,238,0.2)]">
            <Rocket className="w-3.5 h-3.5 text-cyan-400 animate-pulse" />
            <span className="text-white font-bold tracking-wider">SPACEX STARSHIP FLIGHT-V</span>
            <span className="text-cyan-400/80 font-jp text-[10px]">次世代宇宙軌道AIエンジン</span>
          </div>
        </MagneticElement>
      </motion.div>

      {/* 4. Centered SpaceX-Grade Typography & Direct Magnetic CTA */}
      <div className="relative z-10 max-w-5xl mx-auto px-6 text-center my-auto flex flex-col items-center">
        <motion.div
          initial={{ opacity: 0, y: 16 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ duration: 0.6, ease: [0.16, 1, 0.3, 1] }}
          className="space-y-4"
        >
          <span className="font-mono text-xs sm:text-sm uppercase tracking-[0.35em] text-cyan-400 font-semibold block text-glow-cyan">
            Space-Grade Autonomous Video Repurposing
          </span>

          <h1 
            id="brand-hero-title"
            className="font-display font-extrabold text-4xl sm:text-6xl md:text-8xl lg:text-[6.5rem] tracking-[-0.03em] text-white leading-[1.05] uppercase"
          >
            <HoloCyberGlitchText text="TURN RAW STREAMS" as="span" /> <br className="hidden sm:inline" />
            <span className="text-transparent bg-clip-text bg-gradient-to-r from-white via-cyan-200 to-stone-400">
              INTO VIRAL GOLD.
            </span>
          </h1>

          <p className="text-stone-300 text-sm sm:text-base md:text-lg font-normal leading-relaxed max-w-2xl mx-auto pt-2">
            Powered by multi-stage neural hook analysis, kinetic captions, and orbital 9:16 re-framing. Accelerate your content velocity at SpaceX speed.
          </p>
        </motion.div>

        {/* Action Controls with Organic Liquid Magnetic Buttons */}
        <motion.div
          initial={{ opacity: 0, y: 16 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ duration: 0.6, delay: 0.15 }}
          className="flex flex-wrap items-center justify-center gap-4 sm:gap-6 mt-10"
        >
          <LiquidMagneticButton
            id="hero-start-ingest-btn"
            onClick={scrollToConsole}
            dataCursorText="INGEST"
            variant="primary"
          >
            <Sparkles className="w-4 h-4 text-cyan-600" />
            <span>Open Ingest Cockpit</span>
            <ArrowRight className="w-4 h-4 text-black" />
          </LiquidMagneticButton>

          <LiquidMagneticButton
            id="hero-watch-reel-btn"
            onClick={() => {
              if (onOpenDemoVideo) onOpenDemoVideo();
            }}
            dataCursorText="PREVIEW"
            variant="glass"
          >
            <Play className="w-3.5 h-3.5 fill-current text-cyan-400" />
            <span>Watch Starship Reel</span>
          </LiquidMagneticButton>
        </motion.div>
      </div>

      {/* 5. Minimalist Smooth Scroll Indicator with Magnetic Snapping */}
      <motion.div
        initial={{ opacity: 0 }}
        animate={{ opacity: 1 }}
        transition={{ duration: 0.5, delay: 0.3 }}
        onClick={scrollToConsole}
        onMouseEnter={() => sound.playHover()}
        data-cursor-text="SCROLL"
        className="relative z-10 flex flex-col items-center gap-2 cursor-pointer text-stone-500 hover:text-cyan-300 transition-colors mt-20 sm:mt-28 mb-4 sm:mb-6"
      >
        <MagneticElement strength={0.3} radius={50}>
          <div className="flex flex-col items-center gap-2 px-4 py-2">
            <span className="font-mono text-[11px] uppercase tracking-[0.35em] text-stone-400">
              Scroll to Cockpit
            </span>
            <motion.div
              animate={{ y: [0, 6, 0] }}
              transition={{ duration: 1.5, repeat: Infinity, ease: 'easeInOut' }}
            >
              <ChevronDown className="w-4 h-4 text-cyan-400" />
            </motion.div>
          </div>
        </MagneticElement>
      </motion.div>
    </section>
  );
};
