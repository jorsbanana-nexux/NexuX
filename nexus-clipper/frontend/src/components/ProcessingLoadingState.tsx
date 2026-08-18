import React from 'react';
import { motion } from 'motion/react';
import { Activity, X, Clock } from 'lucide-react';

interface LoadingStateProps {
  progress: number;
  stageLabel: string;
  onCancel?: () => void;
  etaSeconds?: number;
  elapsedSeconds?: number;
  fastPath?: boolean;
}

export const ProcessingLoadingState: React.FC<LoadingStateProps> = ({
  progress,
  stageLabel,
  onCancel,
  etaSeconds,
  elapsedSeconds,
  fastPath,
}) => {
  const getStageMessage = (stage: string): string => {
    const s = stage.toLowerCase();
    if (s.includes('metadata')) return 'Fetching video info...';
    if (s.includes('transcri')) return fastPath ? 'Fetching YouTube auto-captions (fast path!)...' : 'Transcribing audio with Whisper...';
    if (s.includes('analy')) return 'AI selecting viral moments from transcript...';
    if (s.includes('download')) return 'Downloading selected video sections (partial)...';
    if (s.includes('render')) return 'Rendering clips in parallel with FFmpeg...';
    if (s.includes('critique') || s.includes('quality')) return 'Running quality gate...';
    if (s.includes('enhanc')) return 'Enhancing audio...';
    if (s.includes('final')) return 'Assembling final output...';
    if (s.includes('complete')) return 'Complete!';
    if (s.includes('error')) return 'Pipeline error — check logs';
    return stage.replace(/_/g, ' ').replace(/\b\w/g, c => c.toUpperCase());
  };

  const displayText = getStageMessage(stageLabel);
  const displayProgress = Math.max(0, Math.min(100, progress));

  const fmtTime = (s?: number): string => {
    if (!s || s < 0) return '--';
    if (s < 60) return `${Math.round(s)}s`;
    return `${Math.floor(s / 60)}m ${Math.round(s % 60)}s`;
  };

  return (
    <motion.div
      initial={{ opacity: 0, scale: 0.94 }}
      animate={{ opacity: 1, scale: 1 }}
      exit={{ opacity: 0, scale: 0.94, filter: 'blur(8px)' }}
      transition={{ duration: 0.5, ease: [0.16, 1, 0.3, 1] }}
      className="relative w-full py-10 sm:py-16 flex flex-col items-center justify-center text-center space-y-8 sm:space-y-10 will-change-transform"
    >
      {/* Space Radar & Dynamic Audio Waveform Visualizer */}
      <div className="relative w-56 h-56 sm:w-80 sm:h-80 flex items-center justify-center">
        {/* Concentric Rotating Space Radar Rings */}
        <motion.div
          animate={{ rotate: 360 }}
          transition={{ duration: 18, repeat: Infinity, ease: 'linear' }}
          className="absolute inset-0 rounded-full border border-cyan-500/20 border-dashed will-change-transform"
        />

        <motion.div
          animate={{ rotate: -360 }}
          transition={{ duration: 12, repeat: Infinity, ease: 'linear' }}
          className="absolute inset-4 rounded-full border border-white/15 border-t-cyan-400/80 border-b-cyan-400/80 will-change-transform"
        />

        <motion.div
          animate={{ scale: [0.96, 1.04, 0.96], opacity: [0.3, 0.7, 0.3] }}
          transition={{ duration: 2.5, repeat: Infinity, ease: 'easeInOut' }}
          className="absolute inset-8 sm:inset-10 rounded-full border border-cyan-400/30 bg-cyan-950/20 shadow-[0_0_35px_rgba(6,182,212,0.25)] will-change-transform"
        />

        {/* Radar Sweeping Beam */}
        <motion.div
          animate={{ rotate: 360 }}
          transition={{ duration: 3.2, repeat: Infinity, ease: 'linear' }}
          className="absolute inset-0 rounded-full pointer-events-none will-change-transform"
          style={{
            background: 'conic-gradient(from 0deg, transparent 0deg, transparent 270deg, rgba(34, 211, 238, 0.35) 360deg)',
          }}
        />

        {/* Crosshair HUD Lines */}
        <div className="absolute inset-x-0 top-1/2 h-[1px] bg-cyan-400/20 pointer-events-none" />
        <div className="absolute inset-y-0 left-1/2 w-[1px] bg-cyan-400/20 pointer-events-none" />

        {/* Center Glowing Core with Audio Waveform bars */}
        <div className="relative z-10 w-28 h-28 sm:w-32 sm:h-32 rounded-full bg-black/90 border border-white/20 backdrop-blur-xl flex flex-col items-center justify-center p-3 shadow-[0_0_30px_rgba(255,255,255,0.2)]">
          {/* Animated Waveform Bars */}
          <div className="flex items-center gap-1 sm:gap-1.5 h-8 sm:h-10 px-2">
            {[40, 75, 95, 60, 100, 80, 50, 90, 65, 85].map((height, i) => (
              <motion.span
                key={i}
                animate={{
                  transform: [`scaleY(0.25)`, `scaleY(1)`, `scaleY(0.3)`],
                }}
                transition={{
                  duration: 0.8 + (i % 3) * 0.2,
                  repeat: Infinity,
                  repeatType: 'mirror',
                  ease: 'easeInOut',
                  delay: i * 0.08,
                }}
                style={{ height: `${height}%`, originY: 0.5 }}
                className="w-1 rounded-full bg-cyan-400 shadow-[0_0_6px_#22d3ee] will-change-transform"
              />
            ))}
          </div>

          <div className="text-[10px] font-mono text-cyan-300 font-bold tracking-widest mt-1">
            {displayProgress}%
          </div>
        </div>
      </div>

      {/* Stage Label */}
      <div className="space-y-3 max-w-xl mx-auto px-4 w-full">
        <div className="inline-flex items-center gap-2 px-3 py-1 rounded-full bg-white/5 border border-white/10 text-xs font-mono text-stone-400">
          <Activity className="w-3.5 h-3.5 text-cyan-400 animate-pulse" />
          <span>NEURAL PIPELINE // {stageLabel.toUpperCase()}</span>
        </div>

        {/* Current stage text */}
        <div className="min-h-[3rem] flex items-center justify-center px-2">
          <p className="text-sm sm:text-base md:text-lg font-mono text-white tracking-wide leading-snug">
            {displayText}
            <span className="inline-block w-1.5 sm:w-2 h-3.5 sm:h-4 ml-1 bg-cyan-400 animate-pulse align-middle" />
          </p>
        </div>

        {/* Real Progress Bar from API */}
        <div className="w-full max-w-md mx-auto bg-stone-900 rounded-full h-2 p-0.5 border border-white/15 overflow-hidden">
          <div
            className="h-full rounded-full bg-gradient-to-r from-cyan-500 via-white to-blue-500 shadow-[0_0_15px_rgba(6,182,212,0.8)] transition-all duration-500 will-change-[width]"
            style={{ width: `${displayProgress}%` }}
          />
        </div>

        {/* Time info row */}
        <div className="flex items-center justify-center gap-4 text-[10px] sm:text-[11px] font-mono text-stone-500">
          {elapsedSeconds != null && (
            <span className="flex items-center gap-1">
              <Clock className="w-3 h-3" />
              {fmtTime(elapsedSeconds)}
            </span>
          )}
          {etaSeconds != null && etaSeconds > 0 && (
            <span className="text-cyan-400/70">
              ETA: {fmtTime(etaSeconds)}
            </span>
          )}
        </div>

        {/* Footer badges */}
        <div className="flex items-center justify-between text-[10px] sm:text-[11px] font-mono text-stone-500 max-w-md mx-auto px-1 pt-1">
          <span>NEXUX V8.0</span>
          <span>SMART DOWNLOAD</span>
          <span className="text-cyan-400">{fastPath ? 'AUTO-CAPTIONS' : 'LOCAL-FIRST'}</span>
        </div>

        {/* Cancel button */}
        {onCancel && (
          <button
            onClick={onCancel}
            className="inline-flex items-center gap-1.5 px-4 py-2 rounded-xl bg-red-500/10 hover:bg-red-500/20 text-red-400 border border-red-500/30 text-xs font-mono transition-colors mt-4"
          >
            <X className="w-3.5 h-3.5" />
            Cancel Job
          </button>
        )}
      </div>
    </motion.div>
  );
};
