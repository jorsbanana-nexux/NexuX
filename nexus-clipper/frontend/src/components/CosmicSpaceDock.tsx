import React, { useState, useEffect } from 'react';
import { motion, AnimatePresence } from 'motion/react';
import { 
  Rocket, 
  Volume2, 
  VolumeX, 
  Music, 
  Sparkles, 
  Moon, 
  SkipForward, 
  Play, 
  Pause, 
  Activity, 
  ChevronUp, 
  ChevronDown,
  Layers,
  Flame
} from 'lucide-react';
import { sound } from '../utils/soundEffects';
import { SPACE_4K_VARIANTS, RocketVideoTrack } from './Rocket4KVideoBackground';
import { CosmicThemeMode } from './AudioCosmicControls';

interface CosmicSpaceDockProps {
  currentTrackIndex: number;
  onTrackSelect: (index: number) => void;
  isAutoCycle: boolean;
  onToggleAutoCycle: () => void;
  currentTheme: CosmicThemeMode;
  onThemeChange: (newTheme: CosmicThemeMode) => void;
  onTriggerWarp?: (label: string) => void;
}

export const CosmicSpaceDock: React.FC<CosmicSpaceDockProps> = ({
  currentTrackIndex,
  onTrackSelect,
  isAutoCycle,
  onToggleAutoCycle,
  currentTheme,
  onThemeChange,
  onTriggerWarp,
}) => {
  const [isMuted, setIsMuted] = useState(false);
  const [isAmbientPlaying, setIsAmbientPlaying] = useState(false);
  const [isExpanded, setIsExpanded] = useState(false);
  const [showTelemetry, setShowTelemetry] = useState(false);
  const [liveVelocity, setLiveVelocity] = useState(17450);

  const currentTrack: RocketVideoTrack = SPACE_4K_VARIANTS[currentTrackIndex % SPACE_4K_VARIANTS.length];

  useEffect(() => {
    setIsMuted(sound.getMuted());
  }, []);

  // Subtle speed fluctuation for live cockpit immersion
  useEffect(() => {
    const base = parseInt(currentTrack.telemetry.speed.replace(/[^0-9]/g, '')) || 17450;
    setLiveVelocity(base);
    const interval = setInterval(() => {
      setLiveVelocity((prev) => prev + Math.floor((Math.random() - 0.48) * 12));
    }, 500);
    return () => clearInterval(interval);
  }, [currentTrackIndex, currentTrack]);

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
          ? 'DEEP SPACE OLED // 真の宇宙暗黒'
          : 'NEBULA ATMOSPHERE // 星雲モード'
      );
    }
    onThemeChange(nextTheme);
  };

  const handleNextTrack = () => {
    sound.playClick();
    onTrackSelect((currentTrackIndex + 1) % SPACE_4K_VARIANTS.length);
  };

  return (
    <div className="fixed bottom-4 sm:bottom-6 right-4 sm:right-6 z-50 select-none max-w-[calc(100vw-2rem)]">
      {/* 1. Collapsible Popover Panel for 10 4K Space Variants & Live Telemetry */}
      <AnimatePresence>
        {isExpanded && (
          <motion.div
            initial={{ opacity: 0, y: 16, scale: 0.96 }}
            animate={{ opacity: 1, y: 0, scale: 1 }}
            exit={{ opacity: 0, y: 16, scale: 0.96 }}
            transition={{ duration: 0.25 }}
            className="mb-3 w-80 sm:w-96 rounded-2xl bg-black/90 border border-cyan-500/30 backdrop-blur-2xl shadow-[0_0_40px_rgba(0,0,0,0.9)] overflow-hidden font-mono text-white p-4 space-y-3.5"
          >
            {/* Header */}
            <div className="flex items-center justify-between border-b border-white/10 pb-2.5 text-xs">
              <div className="flex items-center gap-2">
                <Rocket className="w-4 h-4 text-cyan-400 animate-pulse" />
                <span className="font-bold tracking-wider text-cyan-200">
                  4K SPACE STREAMS ({SPACE_4K_VARIANTS.length} VARIANTS)
                </span>
              </div>
              <span className="text-[10px] text-stone-400 bg-white/10 px-2 py-0.5 rounded-full">
                5s AUTO-CYCLE: {isAutoCycle ? 'ON' : 'PAUSED'}
              </span>
            </div>

            {/* List of 10 4K Variants (Scrollable) */}
            <div className="max-h-48 overflow-y-auto space-y-1.5 pr-1 custom-scrollbar">
              {SPACE_4K_VARIANTS.map((track, idx) => {
                const isActive = idx === currentTrackIndex;
                return (
                  <button
                    key={track.id}
                    onClick={() => {
                      sound.playClick();
                      onTrackSelect(idx);
                    }}
                    className={`w-full p-2 rounded-xl text-left text-xs transition-all flex items-center justify-between ${
                      isActive
                        ? 'bg-gradient-to-r from-cyan-950/80 to-blue-950/80 border border-cyan-400/50 text-cyan-200 shadow-[0_0_15px_rgba(34,211,238,0.2)]'
                        : 'bg-white/5 hover:bg-white/10 text-stone-300 border border-transparent'
                    }`}
                  >
                    <div className="flex items-center gap-2.5 truncate">
                      <span className={`text-[10px] font-bold ${isActive ? 'text-cyan-400' : 'text-stone-500'}`}>
                        0{idx + 1}
                      </span>
                      <div className="truncate">
                        <div className="font-bold truncate text-[11px]">{track.title}</div>
                        <div className="text-[9px] text-stone-400 truncate">{track.stage}</div>
                      </div>
                    </div>
                    {isActive && (
                      <span className="shrink-0 px-2 py-0.5 rounded-full bg-cyan-400/20 text-cyan-300 text-[9px] font-bold border border-cyan-400/40">
                        LIVE
                      </span>
                    )}
                  </button>
                );
              })}
            </div>

            {/* Telemetry Card */}
            <div className="p-2.5 rounded-xl bg-black/60 border border-white/10 text-[10px] space-y-1.5">
              <div className="flex items-center justify-between text-stone-400">
                <span>MISSION TELEMETRY:</span>
                <span className="text-emerald-400 font-bold">{currentTrack.missionName}</span>
              </div>
              <div className="grid grid-cols-2 gap-2 text-[10px]">
                <div className="bg-white/5 p-1.5 rounded">
                  <span className="text-stone-500 block text-[9px]">VELOCITY:</span>
                  <span className="font-bold text-cyan-300">{liveVelocity.toLocaleString()} km/h</span>
                </div>
                <div className="bg-white/5 p-1.5 rounded">
                  <span className="text-stone-500 block text-[9px]">ALTITUDE:</span>
                  <span className="font-bold text-amber-300">{currentTrack.telemetry.altitude}</span>
                </div>
              </div>
            </div>
          </motion.div>
        )}
      </AnimatePresence>

      {/* 2. Primary Unified Sleek Floating Dock */}
      <motion.div
        initial={{ y: 20, opacity: 0 }}
        animate={{ y: 0, opacity: 1 }}
        transition={{ duration: 0.4 }}
        className="hud-glass-panel rounded-full p-1.5 border border-cyan-500/30 bg-black/85 shadow-[0_0_30px_rgba(0,0,0,0.8)] flex items-center gap-1 sm:gap-2 backdrop-blur-2xl"
      >
        {/* Quick Rocket Stream Indicator & Expand Button */}
        <button
          onClick={() => {
            sound.playClick();
            setIsExpanded(!isExpanded);
          }}
          onMouseEnter={() => sound.playHover()}
          title="Toggle 10 4K Space Backgrounds & Telemetry"
          className={`px-3 py-1.5 rounded-full text-xs font-mono font-semibold flex items-center gap-2 transition-all ${
            isExpanded
              ? 'bg-cyan-500 text-black font-bold shadow-[0_0_15px_rgba(34,211,238,0.6)]'
              : 'bg-cyan-950/40 text-cyan-200 border border-cyan-400/30 hover:bg-cyan-900/40'
          }`}
        >
          <Rocket className="w-3.5 h-3.5" />
          <span className="hidden sm:inline">
            4K Space: 0{currentTrackIndex + 1}/10
          </span>
          <span className="sm:hidden">
            0{currentTrackIndex + 1}/10
          </span>
          {isExpanded ? (
            <ChevronDown className="w-3 h-3" />
          ) : (
            <ChevronUp className="w-3 h-3 text-cyan-400" />
          )}
        </button>

        {/* 5s Auto-Cycle Toggle */}
        <button
          onClick={() => {
            sound.playClick();
            onToggleAutoCycle();
          }}
          onMouseEnter={() => sound.playHover()}
          title={isAutoCycle ? '5s Auto-Cycle is ON (Click to Pause)' : '5s Auto-Cycle is PAUSED (Click to Resume)'}
          className={`p-2 rounded-full transition-all text-xs ${
            isAutoCycle
              ? 'bg-emerald-950/50 border border-emerald-400/40 text-emerald-300 shadow-[0_0_12px_rgba(16,185,129,0.3)]'
              : 'bg-white/5 border border-white/10 text-stone-400 hover:text-white'
          }`}
        >
          {isAutoCycle ? <Play className="w-3 h-3 fill-current" /> : <Pause className="w-3 h-3" />}
        </button>

        {/* Fast Next Track */}
        <button
          onClick={handleNextTrack}
          onMouseEnter={() => sound.playHover()}
          title="Next 4K Space Stream (Skip)"
          className="p-2 rounded-full bg-white/5 hover:bg-white/15 text-stone-300 hover:text-white border border-white/10 transition-all active:scale-90"
        >
          <SkipForward className="w-3 h-3" />
        </button>

        <div className="h-4 w-[1px] bg-white/15 mx-0.5" />

        {/* Ambient Space Synth */}
        <button
          onClick={handleToggleAmbientMusic}
          onMouseEnter={() => sound.playHover()}
          title={isAmbientPlaying ? 'Pause Ambient Deep Space Synth' : 'Play Ambient Deep Space Synth'}
          className={`px-2.5 py-1.5 rounded-full font-mono text-xs flex items-center gap-1.5 transition-all ${
            isAmbientPlaying
              ? 'bg-purple-950/50 border border-purple-400/40 text-purple-200 shadow-[0_0_12px_rgba(168,85,247,0.3)]'
              : 'bg-white/5 hover:bg-white/15 text-stone-400 hover:text-white border border-white/10'
          }`}
        >
          <Music className="w-3 h-3 text-purple-400" />
          <span className="hidden md:inline text-[11px]">
            {isAmbientPlaying ? 'Synth ON' : 'Synth'}
          </span>
        </button>

        {/* Sound FX Mute */}
        <button
          onClick={handleToggleMute}
          onMouseEnter={() => sound.playHover()}
          title={isMuted ? 'Unmute Sound Effects' : 'Mute Sound Effects'}
          className={`p-2 rounded-full font-mono text-xs transition-all ${
            isMuted
              ? 'bg-red-950/50 border border-red-500/40 text-red-300'
              : 'bg-white/5 hover:bg-white/15 text-stone-300 hover:text-cyan-300 border border-white/10'
          }`}
        >
          {isMuted ? <VolumeX className="w-3.5 h-3.5 text-red-400" /> : <Volume2 className="w-3.5 h-3.5 text-cyan-400" />}
        </button>

        {/* Theme Switcher */}
        <button
          onClick={handleToggleTheme}
          onMouseEnter={() => sound.playHover()}
          title={`Theme: ${currentTheme === 'nebula' ? 'Nebula Atmosphere' : 'Deep Space OLED'}. Click to switch.`}
          className={`p-2 rounded-full font-mono text-xs transition-all ${
            currentTheme === 'nebula'
              ? 'bg-purple-950/40 text-purple-300 border border-purple-500/30'
              : 'bg-stone-900 text-stone-300 border border-white/20'
          }`}
        >
          {currentTheme === 'nebula' ? <Sparkles className="w-3.5 h-3.5 text-purple-400" /> : <Moon className="w-3.5 h-3.5 text-stone-300" />}
        </button>
      </motion.div>
    </div>
  );
};
