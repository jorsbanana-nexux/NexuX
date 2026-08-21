import React, { useState, useEffect } from 'react';
import { motion, AnimatePresence } from 'motion/react';
import { 
  Volume2, 
  VolumeX, 
  Sparkles, 
  Moon, 
  Radio, 
  Music,
  Zap
} from 'lucide-react';
import { sound } from '../utils/soundEffects';
import { MagneticElement } from './MagneticElement';

export type CosmicThemeMode = 'nebula' | 'deep-space';

interface AudioCosmicControlsProps {
  currentTheme: CosmicThemeMode;
  onThemeChange: (newTheme: CosmicThemeMode) => void;
  onTriggerWarp?: (label: string) => void;
}

export const AudioCosmicControls: React.FC<AudioCosmicControlsProps> = ({
  currentTheme,
  onThemeChange,
  onTriggerWarp,
}) => {
  const [isMuted, setIsMuted] = useState(false);
  const [isAmbientPlaying, setIsAmbientPlaying] = useState(false);
  const [showTooltip, setShowTooltip] = useState(false);

  // Sync mute state on mount
  useEffect(() => {
    setIsMuted(sound.getMuted());
  }, []);

  const handleToggleMute = () => {
    sound.playClick();
    const muted = sound.toggleMute();
    setIsMuted(muted);
  };

  const handleToggleAmbientMusic = () => {
    sound.playClick();
    if (isAmbientPlaying) {
      sound.stopAmbientMusic();
      setIsAmbientPlaying(false);
    } else {
      sound.startAmbientMusic();
      setIsAmbientPlaying(true);
    }
  };

  const handleToggleTheme = () => {
    sound.playClick();
    const nextTheme = currentTheme === 'nebula' ? 'deep-space' : 'nebula';
    if (onTriggerWarp) {
      onTriggerWarp(
        nextTheme === 'deep-space'
          ? 'ENTERING DEEP SPACE OLED // 真の暗黒モード'
          : 'ENTERING NEBULA ATMOSPHERE // 星雲モード'
      );
    }
    onThemeChange(nextTheme);
  };

  return (
    <div className="fixed bottom-6 right-6 z-50 flex items-center gap-3 select-none">
      {/* Floating Cockpit HUD Control Pill */}
      <motion.div
        initial={{ y: 20, opacity: 0 }}
        animate={{ y: 0, opacity: 1 }}
        transition={{ duration: 0.5, delay: 0.2 }}
        className="hud-glass-panel rounded-full p-1.5 border border-white/20 shadow-2xl flex items-center gap-1.5 backdrop-blur-2xl"
      >
        {/* 1. Ambient Music Generator Button with Equalizer Bars */}
        <MagneticElement strength={0.3} radius={45}>
          <button
            id="toggle-ambient-music-btn"
            onClick={handleToggleAmbientMusic}
            onMouseEnter={() => sound.playHover()}
            data-cursor-text={isAmbientPlaying ? 'PAUSE AMBIENT' : 'PLAY AMBIENT'}
            title={isAmbientPlaying ? 'Pause Ambient Deep Space Synth' : 'Play Ambient Deep Space Synth'}
            className={`px-3 py-1.5 rounded-full font-mono text-[11px] font-semibold flex items-center gap-2 transition-all ${
              isAmbientPlaying
                ? 'bg-cyan-500/25 border border-cyan-400/60 text-cyan-200 shadow-[0_0_15px_rgba(34,211,238,0.4)]'
                : 'bg-black/60 hover:bg-white/10 text-stone-400 hover:text-white border border-white/10'
            }`}
          >
            {isAmbientPlaying ? (
              <div className="flex items-center gap-0.5 h-3">
                <span className="w-0.5 h-2 bg-cyan-400 animate-pulse" />
                <span className="w-0.5 h-3 bg-cyan-300 animate-ping" />
                <span className="w-0.5 h-1.5 bg-cyan-400 animate-pulse" />
              </div>
            ) : (
              <Music className="w-3.5 h-3.5 text-stone-400" />
            )}
            <span className="hidden sm:inline">
              {isAmbientPlaying ? 'Ambient: ON' : 'Ambient'}
            </span>
          </button>
        </MagneticElement>

        {/* 2. Global Mute / Sound FX Button */}
        <MagneticElement strength={0.3} radius={45}>
          <button
            id="toggle-sound-mute-btn"
            onClick={handleToggleMute}
            onMouseEnter={() => sound.playHover()}
            data-cursor-text={isMuted ? 'UNMUTE' : 'MUTE'}
            title={isMuted ? 'Unmute UI Sound Effects' : 'Mute UI Sound Effects'}
            className={`p-2 rounded-full font-mono text-xs transition-all ${
              isMuted
                ? 'bg-red-950/40 text-red-400 border border-red-500/30'
                : 'bg-black/60 hover:bg-white/10 text-stone-300 hover:text-cyan-300 border border-white/10'
            }`}
          >
            {isMuted ? (
              <VolumeX className="w-4 h-4 text-red-400" />
            ) : (
              <Volume2 className="w-4 h-4 text-cyan-400" />
            )}
          </button>
        </MagneticElement>

        <div className="h-4 w-[1px] bg-white/15 mx-0.5" />

        {/* 3. Cosmic Mode Switcher: Nebula vs Deep Space */}
        <MagneticElement strength={0.3} radius={45}>
          <button
            id="toggle-cosmic-theme-btn"
            onClick={handleToggleTheme}
            onMouseEnter={() => sound.playHover()}
            data-cursor-text="THEME"
            title={`Current: ${currentTheme === 'nebula' ? 'Nebula Glow Mode' : 'Deep Space OLED Mode'}. Click to switch.`}
            className={`px-3 py-1.5 rounded-full font-mono text-[11px] font-semibold flex items-center gap-1.5 transition-all ${
              currentTheme === 'nebula'
                ? 'bg-purple-950/40 border border-purple-400/50 text-purple-200 shadow-[0_0_15px_rgba(168,85,247,0.3)]'
                : 'bg-stone-900 border border-white/30 text-stone-200'
            }`}
          >
            {currentTheme === 'nebula' ? (
              <>
                <Sparkles className="w-3.5 h-3.5 text-purple-400" />
                <span className="hidden sm:inline">Nebula</span>
              </>
            ) : (
              <>
                <Moon className="w-3.5 h-3.5 text-stone-300" />
                <span className="hidden sm:inline">Deep Space</span>
              </>
            )}
          </button>
        </MagneticElement>
      </motion.div>
    </div>
  );
};
