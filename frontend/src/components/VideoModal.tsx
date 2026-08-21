import React, { useState, useEffect } from 'react';
import { motion, AnimatePresence } from 'motion/react';
import { X, Rocket, Sparkles, Smartphone, Monitor, Eye, Volume2 } from 'lucide-react';
import { sound } from '../utils/soundEffects';
import { subtitleStore } from '../utils/subtitleStore';
import { SubtitleConfig, SubtitleScriptLine } from '../types/subtitles';
import { LiveSubtitleRenderer } from './LiveSubtitleRenderer';

interface VideoModalProps {
  isOpen: boolean;
  onClose: () => void;
  clipTitle?: string;
  clipSubtitle?: string;
}

export const VideoModal: React.FC<VideoModalProps> = ({ 
  isOpen, 
  onClose,
  clipTitle = 'SPACEX STARSHIP // ORBITAL ASCENT SHOWREEL',
  clipSubtitle = 'NEVER TRADE YOUR TIME FOR HOURLY WAGES'
}) => {
  const [subConfig, setSubConfig] = useState<SubtitleConfig>(subtitleStore.get());
  const [aspectMode, setAspectMode] = useState<'9:16' | '16:9'>('9:16');
  const [showSubtitles, setShowSubtitles] = useState(true);
  const [wordIndex, setWordIndex] = useState(0);

  useEffect(() => {
    const unsub = subtitleStore.subscribe((cfg) => setSubConfig(cfg));
    return () => unsub();
  }, []);

  const words = React.useMemo(() => {
    return clipSubtitle.split(' ').map((w, idx) => ({
      text: w,
      highlight: idx % 2 === 0,
      emoji: idx === 1 ? '🔥' : undefined,
      colorType: (idx % 2 === 0 ? 'cyan' : 'normal') as any,
    }));
  }, [clipSubtitle]);

  const currentLine: SubtitleScriptLine = React.useMemo(() => ({
    lineText: clipSubtitle,
    words,
    hookScore: 98,
  }), [clipSubtitle, words]);

  useEffect(() => {
    if (!isOpen) {
      setWordIndex(0);
      return;
    }
    const timer = setInterval(() => {
      setWordIndex((prev) => (prev + 1) % words.length);
    }, 450);
    return () => clearInterval(timer);
  }, [isOpen, words.length]);

  if (!isOpen) return null;

  return (
    <AnimatePresence>
      <div className="fixed inset-0 z-50 flex items-center justify-center p-4 sm:p-6 select-none">
        {/* Backdrop */}
        <motion.div
          initial={{ opacity: 0 }}
          animate={{ opacity: 1 }}
          exit={{ opacity: 0 }}
          onClick={onClose}
          className="absolute inset-0 bg-black/90 backdrop-blur-2xl"
        />

        {/* Modal Window */}
        <motion.div
          initial={{ opacity: 0, scale: 0.95 }}
          animate={{ opacity: 1, scale: 1 }}
          exit={{ opacity: 0, scale: 0.95 }}
          className="relative w-full max-w-2xl bg-stone-950 border border-white/20 rounded-3xl overflow-hidden shadow-[0_0_90px_rgba(0,0,0,0.95)] z-10 flex flex-col max-h-[90vh]"
        >
          {/* Header */}
          <div className="p-4 border-b border-white/10 flex items-center justify-between bg-black/80">
            <div className="flex items-center gap-2">
              <Rocket className="w-4 h-4 text-cyan-400 animate-pulse" />
              <span className="text-xs font-mono uppercase tracking-widest text-white font-bold truncate max-w-[280px] sm:max-w-md">
                {clipTitle}
              </span>
            </div>

            <div className="flex items-center gap-2">
              {/* Aspect Ratio Toggle */}
              <div className="flex items-center bg-white/10 p-0.5 rounded-lg border border-white/10 text-[10px] font-mono">
                <button
                  onClick={() => { sound.playClick(); setAspectMode('9:16'); }}
                  className={`px-2 py-1 rounded flex items-center gap-1 ${
                    aspectMode === '9:16' ? 'bg-cyan-500 text-black font-bold' : 'text-stone-400 hover:text-white'
                  }`}
                >
                  <Smartphone className="w-3 h-3" />
                  <span>9:16</span>
                </button>
                <button
                  onClick={() => { sound.playClick(); setAspectMode('16:9'); }}
                  className={`px-2 py-1 rounded flex items-center gap-1 ${
                    aspectMode === '16:9' ? 'bg-cyan-500 text-black font-bold' : 'text-stone-400 hover:text-white'
                  }`}
                >
                  <Monitor className="w-3 h-3" />
                  <span>16:9</span>
                </button>
              </div>

              <button
                onClick={onClose}
                className="p-1.5 rounded-lg bg-white/10 hover:bg-white/20 text-stone-300 hover:text-white transition-colors"
              >
                <X className="w-4 h-4" />
              </button>
            </div>
          </div>

          {/* Video Player Box */}
          <div className="relative bg-black flex items-center justify-center p-4 overflow-hidden flex-1 min-h-[360px]">
            <div className={`relative rounded-2xl overflow-hidden shadow-2xl border border-white/15 bg-stone-900 transition-all duration-300 flex items-center justify-center ${
              aspectMode === '9:16' ? 'w-full max-w-[290px] aspect-[9/16]' : 'w-full aspect-video'
            }`}>
              <video
                autoPlay
                controls
                loop
                playsInline
                className="w-full h-full object-cover"
                poster="https://images.unsplash.com/photo-1517976487508-36a54054a7c0?q=80&w=2070&auto=format&fit=crop"
              >
                <source
                  src="https://upload.wikimedia.org/wikipedia/commons/transcoded/1/14/SpaceX_CRS-20_Launch_to_the_International_Space_Station.webm/SpaceX_CRS-20_Launch_to_the_International_Space_Station.webm.720p.vp9.webm"
                  type="video/webm"
                />
                <source
                  src="https://assets.mixkit.co/videos/preview/mixkit-stars-in-space-1610-large.mp4"
                  type="video/mp4"
                />
              </video>

              {/* Contrast Vignette */}
              <div className="absolute inset-0 bg-gradient-to-t from-black/80 via-transparent to-black/30 pointer-events-none" />

              {/* Real-Time Synced Subtitle Overlay */}
              {showSubtitles && (
                <div className={`absolute inset-x-3 text-center pointer-events-none transition-all duration-300 flex items-center justify-center ${
                  subConfig.position === 'top' ? 'top-8' : subConfig.position === 'center' ? 'top-1/2 -translate-y-1/2' : 'bottom-12'
                }`}>
                  <LiveSubtitleRenderer
                    currentLine={currentLine}
                    wordIndex={wordIndex}
                    lineIndex={0}
                    config={subConfig}
                  />
                </div>
              )}
            </div>
          </div>

          {/* Footer details */}
          <div className="p-4 bg-stone-950 border-t border-white/10 flex flex-wrap items-center justify-between text-[11px] font-mono text-stone-400 gap-2">
            <div className="flex items-center gap-3">
              <span className="text-cyan-300 font-bold">Preset: {subConfig.name}</span>
              <button
                onClick={() => setShowSubtitles(!showSubtitles)}
                className={`px-2 py-0.5 rounded border text-[10px] ${
                  showSubtitles ? 'border-emerald-400/40 text-emerald-300 bg-emerald-950/40' : 'border-white/10 text-stone-400'
                }`}
              >
                Captions: {showSubtitles ? 'ON' : 'OFF'}
              </button>
            </div>
            <div className="text-cyan-400 font-bold">
              1080p 60FPS • Ready for TikTok & Reels
            </div>
          </div>
        </motion.div>
      </div>
    </AnimatePresence>
  );
};
