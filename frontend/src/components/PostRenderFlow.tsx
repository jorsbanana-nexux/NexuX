import React, { useState } from 'react';
import { motion, AnimatePresence } from 'motion/react';
import { ArrowLeft, Rocket } from 'lucide-react';
import { ModeSelector } from './ModeSelector';
import { SpaceshipConsole } from './SpaceshipConsole';
import { Mode2Console } from './Mode2Console';
import { sound } from '../utils/soundEffects';
import type { NexuXMode } from '../api/v2Api';

type FlowStage = 'select' | NexuXMode;

/**
 * PostRenderFlow — Dual-mode orchestrator (V9.5)
 * ===============================================
 * Flow: mode selection → mode console (input → processing → results).
 * Podcast Mode renders the SpaceshipConsole, which auto-opens the
 * ClipEditorStudio when rendering completes (results → editor handoff).
 */
export const PostRenderFlow: React.FC = () => {
  const [stage, setStage] = useState<FlowStage>('select');

  const goBack = () => {
    sound.playClick();
    setStage('select');
  };

  if (stage === 'podcast') {
    return (
      <div className="relative">
        <FlowBackButton onBack={goBack} label="Ganti Mode" />
        <SpaceshipConsole />
      </div>
    );
  }

  if (stage === 'creative') {
    return (
      <div className="relative">
        <Mode2Console onBack={goBack} />
      </div>
    );
  }

  return (
    <section id="mode-select" className="relative py-24 px-6 sm:px-10 z-10">
      <div className="max-w-5xl mx-auto">
        <motion.div
          initial={{ opacity: 0, y: 16 }}
          whileInView={{ opacity: 1, y: 0 }}
          viewport={{ once: true, margin: '-80px' }}
          transition={{ duration: 0.6 }}
          className="text-center mb-12"
        >
          <div className="inline-flex items-center gap-2 rounded-full border border-cyan-400/30 bg-cyan-400/5 px-4 py-1.5 mb-5">
            <Rocket className="w-3.5 h-3.5 text-cyan-300" />
            <span className="text-[11px] font-mono tracking-[0.2em] text-cyan-300 uppercase">
              Dual-Mode Engine
            </span>
          </div>
          <h2 className="text-3xl sm:text-4xl font-extrabold text-white mb-3">
            Pilih Mode <span className="text-cyan-400">Generasi</span>
          </h2>
          <p className="text-sm sm:text-base text-stone-400 max-w-2xl mx-auto">
            Potong podcast panjang menjadi klip viral, atau biarkan AI menyusun
            video kompilasi dari satu keyword — semuanya diproses lokal di mesin Anda.
          </p>
        </motion.div>

        <AnimatePresence mode="wait">
          <ModeSelector onSelect={(mode) => setStage(mode)} />
        </AnimatePresence>
      </div>
    </section>
  );
};

const FlowBackButton: React.FC<{ onBack: () => void; label: string }> = ({
  onBack,
  label,
}) => (
  <div className="relative z-20 max-w-5xl mx-auto px-6 sm:px-10 pt-8">
    <motion.button
      type="button"
      onClick={onBack}
      whileHover={{ x: -3 }}
      className="inline-flex items-center gap-2 rounded-full border border-white/10 bg-white/[0.03] backdrop-blur-xl px-4 py-2 text-xs font-mono text-stone-300 hover:border-cyan-400/40 hover:text-cyan-300 transition-colors"
    >
      <ArrowLeft className="w-3.5 h-3.5" />
      {label}
    </motion.button>
  </div>
);
