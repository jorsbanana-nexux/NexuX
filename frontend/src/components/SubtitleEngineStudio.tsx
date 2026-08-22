import React, { useState, useEffect, useRef } from 'react';
import { motion, AnimatePresence } from 'motion/react';
import { 
  Sparkles, 
  Type, 
  Layers, 
  Play, 
  Pause, 
  Flame, 
  Zap, 
  Gamepad2, 
  BookOpen, 
  Smile, 
  Sliders, 
  Check, 
  Copy,
  RotateCcw,
  CheckCircle2,
  Terminal,
  Activity,
  ArrowRight,
  TrendingUp,
  Cpu,
  Palette,
  Eye,
  Crown,
  FastForward,
  ShieldAlert,
  Volume2
} from 'lucide-react';
import { 
  SubtitleAnimationStyle, 
  SubtitleVisualPreset, 
  SubtitlePosition, 
  SubtitleFontSize, 
  SubtitleFontFamily,
  SubtitleGlowStyle,
  SubtitleScriptLine,
  SubtitleConfig 
} from '../types/subtitles';
import { subtitleStore, DEFAULT_SUBTITLE_CONFIG } from '../utils/subtitleStore';
import { LiveSubtitleRenderer } from './LiveSubtitleRenderer';

// Rich Viral Scripts with Realistic Spoken Timing
const SCRIPT_LIBRARIES: { [key: string]: { label: string; lines: SubtitleScriptLine[] } } = {
  business: {
    label: '💼 Business & High-Income ($100M Leads)',
    lines: [
      {
        lineText: 'NEVER TRADE YOUR TIME FOR HOURLY WAGES',
        words: [
          { text: 'NEVER', highlight: true, emoji: '⚡' },
          { text: 'TRADE' },
          { text: 'YOUR', highlight: true },
          { text: 'TIME' },
          { text: 'FOR' },
          { text: 'HOURLY', highlight: true, emoji: '💰' },
          { text: 'WAGES' },
        ],
        hookScore: 99,
      },
      {
        lineText: 'BUILD AN AUTONOMOUS DISTRIBUTION SYSTEM',
        words: [
          { text: 'BUILD', highlight: true, emoji: '🚀' },
          { text: 'AN' },
          { text: 'AUTONOMOUS', highlight: true },
          { text: 'DISTRIBUTION', highlight: true, emoji: '🔥' },
          { text: 'SYSTEM' },
        ],
        hookScore: 98,
      },
      {
        lineText: 'THAT PRINTS LEVERAGE WHILE YOU SLEEP',
        words: [
          { text: 'THAT' },
          { text: 'PRINTS', highlight: true, emoji: '📈' },
          { text: 'LEVERAGE', highlight: true },
          { text: 'WHILE' },
          { text: 'YOU', highlight: true, emoji: '🧠' },
          { text: 'SLEEP' },
        ],
        hookScore: 97,
      },
    ],
  },
  gaming: {
    label: '🎮 Gaming & High-Energy Clutch',
    lines: [
      {
        lineText: 'WATCH THIS INSANE 1V5 CLUTCH!',
        words: [
          { text: 'WATCH', colorType: 'normal' },
          { text: 'THIS', colorType: 'normal' },
          { text: 'INSANE', colorType: 'rage', highlight: true, emoji: '💥' },
          { text: '1V5', colorType: 'cyan', highlight: true },
          { text: 'CLUTCH!', colorType: 'win', highlight: true, emoji: '🏆' },
        ],
        hookScore: 99,
      },
      {
        lineText: 'NO WAY HE HIT THAT FLICK SHOT!',
        words: [
          { text: 'NO', colorType: 'rage', highlight: true },
          { text: 'WAY' },
          { text: 'HE' },
          { text: 'HIT', colorType: 'combo', highlight: true, emoji: '🎯' },
          { text: 'THAT' },
          { text: 'FLICK', colorType: 'win', highlight: true, emoji: '🔥' },
          { text: 'SHOT!' },
        ],
        hookScore: 96,
      },
    ],
  },
  mindset: {
    label: '🌌 Philosophy & Aesthetic Vlog',
    lines: [
      {
        lineText: 'In the deep silence of the cosmos,',
        words: [
          { text: 'In' },
          { text: 'the' },
          { text: 'deep', highlight: true },
          { text: 'silence', highlight: true, emoji: '✨' },
          { text: 'of' },
          { text: 'the' },
          { text: 'cosmos,', highlight: true },
        ],
        hookScore: 94,
      },
      {
        lineText: 'we find the courage to begin again.',
        words: [
          { text: 'we' },
          { text: 'find' },
          { text: 'the' },
          { text: 'courage', highlight: true, emoji: '🌱' },
          { text: 'to' },
          { text: 'begin', highlight: true },
          { text: 'again.' },
        ],
        hookScore: 95,
      },
    ],
  },
  tech: {
    label: '⚡ AI Engineering & Future Tech',
    lines: [
      {
        lineText: 'AI IS NOT REPLACING DEVELOPERS,',
        words: [
          { text: 'AI', highlight: true, emoji: '🤖' },
          { text: 'IS' },
          { text: 'NOT', highlight: true },
          { text: 'REPLACING', highlight: true, emoji: '⚠️' },
          { text: 'DEVELOPERS,' },
        ],
        hookScore: 98,
      },
      {
        lineText: 'IT EMPOWERS 100X UNSTOPPABLE ARCHITECTS.',
        words: [
          { text: 'IT' },
          { text: 'EMPOWERS', highlight: true, emoji: '🚀' },
          { text: '100X', highlight: true, emoji: '⚡' },
          { text: 'UNSTOPPABLE', highlight: true },
          { text: 'ARCHITECTS.' },
        ],
        hookScore: 99,
      },
    ],
  },
};

const SAMPLE_BG_VIDEOS = [
  { id: 'space-orbit', label: 'Space 4K Launch', url: 'https://assets.mixkit.co/videos/preview/mixkit-stars-in-space-1610-large.mp4' },
  { id: 'tech-desk', label: 'Creator Setup', url: 'https://assets.mixkit.co/videos/preview/mixkit-hands-of-a-man-working-on-a-computer-keyboard-41399-large.mp4' },
  { id: 'speaker', label: 'Podcast Host', url: 'https://assets.mixkit.co/videos/preview/mixkit-young-woman-talking-on-video-call-with-a-laptop-42995-large.mp4' },
  { id: 'cyber-city', label: 'Neon Cyber City', url: 'https://assets.mixkit.co/videos/preview/mixkit-futuristic-city-with-flying-cars-41551-large.mp4' },
];

const COLOR_PALETTES = [
  { id: '#facc15', label: 'Hormozi Gold', hex: '#facc15', bgClass: 'bg-yellow-400', textClass: 'text-yellow-400' },
  { id: '#22d3ee', label: 'MrBeast Violet', hex: '#22d3ee', bgClass: 'bg-violet-400', textClass: 'text-violet-400' },
  { id: '#10b981', label: 'Emerald Lime', hex: '#10b981', bgClass: 'bg-emerald-400', textClass: 'text-emerald-400' },
  { id: '#f43f5e', label: 'Neon Rose', hex: '#f43f5e', bgClass: 'bg-rose-500', textClass: 'text-rose-400' },
  { id: '#f97316', label: 'Solar Orange', hex: '#f97316', bgClass: 'bg-orange-500', textClass: 'text-orange-400' },
  { id: '#ffffff', label: 'Diamond White', hex: '#ffffff', bgClass: 'bg-white', textClass: 'text-white' },
];

export const SubtitleEngineStudio: React.FC = () => {
  // Config state
  const [selectedAnimation, setSelectedAnimation] = useState<SubtitleAnimationStyle>('word-by-word');
  const [selectedPreset, setSelectedPreset] = useState<SubtitleVisualPreset>('hormozi');
  const [selectedPosition, setSelectedPosition] = useState<SubtitlePosition>('bottom');
  const [selectedFontSize, setSelectedFontSize] = useState<SubtitleFontSize>('large');
  const [selectedFontFamily, setSelectedFontFamily] = useState<SubtitleFontFamily>('sans');
  const [selectedGlowStyle, setSelectedGlowStyle] = useState<SubtitleGlowStyle>('intense');
  const [highlightColor, setHighlightColor] = useState<string>('#facc15');
  const [showEmojis, setShowEmojis] = useState(true);
  const [activeCategory, setActiveCategory] = useState<string>('business');
  const [activeBgVideoIdx, setActiveBgVideoIdx] = useState(0);

  // Playback engine
  const [isPlaying, setIsPlaying] = useState(true);
  const [lineIndex, setLineIndex] = useState(0);
  const [wordIndex, setWordIndex] = useState(0);
  const [playbackSpeed, setPlaybackSpeed] = useState<number>(1);
  
  // Interaction & Application feedback
  const [isCopied, setIsCopied] = useState(false);
  const [isApplied, setIsApplied] = useState(false);
  const [appliedToast, setAppliedToast] = useState<string | null>(null);

  const currentCategoryData = SCRIPT_LIBRARIES[activeCategory] || SCRIPT_LIBRARIES.business;
  const currentLines = currentCategoryData.lines;
  const currentLine = currentLines[lineIndex % currentLines.length];

  // 120 FPS Clock / Precise Subtitle Word Timers
  useEffect(() => {
    if (!isPlaying) return;

    const baseDelay = Math.floor(400 / playbackSpeed);

    if (selectedAnimation === 'line-by-line') {
      const timer = setInterval(() => {
        setLineIndex((prev) => (prev + 1) % currentLines.length);
      }, Math.floor(1800 / playbackSpeed));
      return () => clearInterval(timer);
    } else {
      const timer = setInterval(() => {
        setWordIndex((prev) => {
          if (prev + 1 >= currentLine.words.length) {
            setLineIndex((l) => (l + 1) % currentLines.length);
            return 0;
          }
          return prev + 1;
        });
      }, baseDelay);
      return () => clearInterval(timer);
    }
  }, [isPlaying, selectedAnimation, currentLine, currentLines.length, playbackSpeed]);

  // Auto sync active settings to global subtitleStore reactive pipeline
  useEffect(() => {
    const presetNames: { [key in SubtitleVisualPreset]: string } = {
      hormozi: 'Alex Hormozi ($100M Viral)',
      mrbeast: 'MrBeast Hyper-Retention',
      'minimal-aesthetic': 'Minimalis Estetik (Podcast)',
      'gamer-comic': 'Gamer / Comic Book (Arcade)',
      'neon-cyberpunk': 'Neon Cyberpunk 2077',
      'ali-abdaal': 'Ali Abdaal (Notion Highlighter)',
      'iman-gadzhi': 'Iman Gadzhi (Luxury Editorial)',
      'anime-impact': 'Anime & Manga Speed Impact',
    };

    const currentConfig: SubtitleConfig = {
      animationStyle: selectedAnimation,
      visualPreset: selectedPreset,
      position: selectedPosition,
      fontSize: selectedFontSize,
      fontFamily: selectedFontFamily,
      glowStyle: selectedGlowStyle,
      showEmojis,
      highlightColor,
      name: `${presetNames[selectedPreset]} • ${selectedAnimation.toUpperCase()}`,
      appliedAt: Date.now(),
    };

    subtitleStore.set(currentConfig);
  }, [
    selectedAnimation,
    selectedPreset,
    selectedPosition,
    selectedFontSize,
    selectedFontFamily,
    selectedGlowStyle,
    showEmojis,
    highlightColor,
  ]);

  const liveConfig: SubtitleConfig = {
    animationStyle: selectedAnimation,
    visualPreset: selectedPreset,
    position: selectedPosition,
    fontSize: selectedFontSize,
    fontFamily: selectedFontFamily,
    glowStyle: selectedGlowStyle,
    showEmojis,
    highlightColor,
    name: `${selectedPreset} • ${selectedAnimation}`,
  };

  const handleAnimationSelect = (style: SubtitleAnimationStyle) => {
    
    setSelectedAnimation(style);
    setWordIndex(0);
    setLineIndex(0);
  };

  const handlePresetSelect = (preset: SubtitleVisualPreset) => {
    
    setSelectedPreset(preset);
    
    // Smart auto-color and category pairing for effortless viral aesthetics
    if (preset === 'hormozi') {
      setHighlightColor('#facc15');
      setSelectedFontFamily('sans');
      setActiveCategory('business');
    } else if (preset === 'mrbeast') {
      setHighlightColor('#22d3ee');
      setSelectedFontFamily('display');
      setActiveCategory('business');
    } else if (preset === 'gamer-comic') {
      setHighlightColor('#f43f5e');
      setSelectedFontFamily('display');
      setActiveCategory('gaming');
    } else if (preset === 'minimal-aesthetic') {
      setHighlightColor('#22d3ee');
      setSelectedFontFamily('sans');
      setActiveCategory('mindset');
    } else if (preset === 'neon-cyberpunk') {
      setHighlightColor('#22d3ee');
      setSelectedFontFamily('mono');
      setActiveCategory('tech');
    } else if (preset === 'ali-abdaal') {
      setHighlightColor('#10b981');
      setSelectedFontFamily('sans');
      setActiveCategory('mindset');
    } else if (preset === 'iman-gadzhi') {
      setHighlightColor('#facc15');
      setSelectedFontFamily('serif');
      setActiveCategory('business');
    } else if (preset === 'anime-impact') {
      setHighlightColor('#f97316');
      setSelectedFontFamily('display');
      setActiveCategory('gaming');
    }
  };

  const handleApplyPreset = () => {
    
    

    const presetNames: { [key in SubtitleVisualPreset]: string } = {
      hormozi: 'Alex Hormozi ($100M Viral)',
      mrbeast: 'MrBeast Hyper-Retention',
      'minimal-aesthetic': 'Minimalis Estetik (Podcast)',
      'gamer-comic': 'Gamer / Comic Book (Arcade)',
      'neon-cyberpunk': 'Neon Cyberpunk 2077',
      'ali-abdaal': 'Ali Abdaal (Notion Highlighter)',
      'iman-gadzhi': 'Iman Gadzhi (Luxury Editorial)',
      'anime-impact': 'Anime & Manga Speed Impact',
    };

    const newConfig: SubtitleConfig = {
      animationStyle: selectedAnimation,
      visualPreset: selectedPreset,
      position: selectedPosition,
      fontSize: selectedFontSize,
      fontFamily: selectedFontFamily,
      glowStyle: selectedGlowStyle,
      showEmojis,
      highlightColor,
      name: `${presetNames[selectedPreset]} • ${selectedAnimation.toUpperCase()}`,
      appliedAt: Date.now(),
    };

    subtitleStore.set(newConfig);
    setIsApplied(true);
    setAppliedToast(`Subtitle Berhasil Disinkronkan ke AI Pipeline (Cockpit & 9:16 Video)!`);

    setTimeout(() => {
      setIsApplied(false);
      setAppliedToast(null);
    }, 4000);
  };

  const handleCopyPresetConfig = () => {
    
    const configExport = JSON.stringify({
      animationStyle: selectedAnimation,
      visualPreset: selectedPreset,
      position: selectedPosition,
      fontSize: selectedFontSize,
      fontFamily: selectedFontFamily,
      glowStyle: selectedGlowStyle,
      highlightColor,
      showEmojis,
      category: activeCategory,
    }, null, 2);

    navigator.clipboard?.writeText?.(configExport);
    setIsCopied(true);
    setTimeout(() => setIsCopied(false), 2000);
  };

  // Font Size Classes
  const getFontSizeClass = () => {
    if (selectedFontSize === 'compact') return 'text-base sm:text-lg';
    if (selectedFontSize === 'normal') return 'text-lg sm:text-xl';
    if (selectedFontSize === 'huge') return 'text-2xl sm:text-3xl';
    return 'text-xl sm:text-2xl'; // large
  };

  // Font Family Classes
  const getFontFamilyClass = () => {
    if (selectedFontFamily === 'display') return 'font-display font-black tracking-tight';
    if (selectedFontFamily === 'mono') return 'font-mono font-bold tracking-normal';
    if (selectedFontFamily === 'serif') return 'font-serif font-bold italic tracking-wide';
    return 'font-sans font-extrabold tracking-tight'; // modern sans
  };

  return (
    <section id="subtitle-engine" className="relative py-24 px-6 sm:px-10 max-w-7xl mx-auto z-10 select-none">
      {/* 1. Header Section */}
      <div className="text-center max-w-3xl mx-auto space-y-4 mb-16">
        <div className="inline-flex items-center gap-2 px-4 py-1.5 rounded-full border border-violet-500/30 bg-violet-950/30 text-violet-300 font-mono text-xs uppercase tracking-widest shadow-[0_0_20px_rgba(34,211,238,0.2)]">
          <Sparkles className="w-3.5 h-3.5 text-violet-400 animate-pulse" />
          <span>VIRAL SUBTITLE & DYNAMIC ANIMATION STUDIO // 字幕スタジオ</span>
        </div>

        <h2 className="text-3xl sm:text-5xl font-display font-bold text-white tracking-tight leading-tight">
          Visual Subtitles & Dynamic Animations
        </h2>

        <p className="text-stone-300 text-sm sm:text-base leading-relaxed max-w-2xl mx-auto">
          Pilih animasi kemunculan kata presisi 120 FPS dan preset estetika viral berdefinisi tinggi tanpa distorsi warna untuk memaksimalkan retensi video TikTok, Reels, dan YouTube Shorts.
        </p>
      </div>

      {/* 2. Main Studio Interactive Layout */}
      <div className="grid grid-cols-1 lg:grid-cols-12 gap-8 items-start">
        
        {/* Left Column: Animation Styles, Visual Presets & Personalization (7 cols) */}
        <div className="lg:col-span-7 space-y-8">
          
          {/* SECTION 1: ANIMASI MUNCULNYA TEKS (8 Dynamic Options) */}
          <div className="bg-[#131316] rounded-2xl p-6 border border-white/15 spacex- space-y-5 bg-black/60 backdrop-blur-xl">
            <div className="flex items-center justify-between border-b border-white/10 pb-3">
              <div className="flex items-center gap-2.5">
                <Type className="w-4 h-4 text-violet-400" />
                <h3 className="font-display font-bold text-base text-white">
                  1. Animasi Munculnya Teks (Dynamic Motion Engine)
                </h3>
              </div>
              <span className="text-[10px] font-mono text-violet-300 bg-violet-950/60 px-2.5 py-0.5 rounded-full border border-violet-500/30">
                8 VIRAL MOTION MODES
              </span>
            </div>

            <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-3">
              {/* Option 1: Word by Word */}
              <button
                onClick={() => handleAnimationSelect('word-by-word')}
                onMouseEnter={() => void 0}
                className={`p-3.5 rounded-xl text-left border transition-all relative flex flex-col justify-between ${
                  selectedAnimation === 'word-by-word'
                    ? 'bg-gradient-to-b from-violet-950/90 to-blue-950/90 border-violet-400 shadow-[0_0_20px_rgba(34,211,238,0.3)]'
                    : 'bg-black/40 border-white/10 hover:border-white/25 hover:bg-white/5'
                }`}
              >
                <div className="space-y-1.5">
                  <div className="flex items-center justify-between">
                    <span className="text-[11px] font-mono font-bold text-violet-400 uppercase tracking-wider">01 • Karaoke</span>
                    {selectedAnimation === 'word-by-word' && <span className="w-2 h-2 rounded-full bg-violet-400 animate-ping" />}
                  </div>
                  <h4 className="font-bold text-white text-sm">Kata Per Kata</h4>
                  <p className="text-xs text-stone-300 leading-relaxed">
                    Highlight menyala tepat di kata yang diucapkan.
                  </p>
                </div>
              </button>

              {/* Option 2: Line by Line */}
              <button
                onClick={() => handleAnimationSelect('line-by-line')}
                onMouseEnter={() => void 0}
                className={`p-3.5 rounded-xl text-left border transition-all relative flex flex-col justify-between ${
                  selectedAnimation === 'line-by-line'
                    ? 'bg-gradient-to-b from-purple-950/90 to-blue-950/90 border-purple-400 shadow-[0_0_20px_rgba(192,132,252,0.3)]'
                    : 'bg-black/40 border-white/10 hover:border-white/25 hover:bg-white/5'
                }`}
              >
                <div className="space-y-1.5">
                  <div className="flex items-center justify-between">
                    <span className="text-[11px] font-mono font-bold text-purple-400 uppercase tracking-wider">02 • Story</span>
                    {selectedAnimation === 'line-by-line' && <span className="w-2 h-2 rounded-full bg-purple-400 animate-ping" />}
                  </div>
                  <h4 className="font-bold text-white text-sm">Baris demi Baris</h4>
                  <p className="text-xs text-stone-300 leading-relaxed">
                    Menampilkan 3-4 kata sekaligus dengan transisi santai.
                  </p>
                </div>
              </button>

              {/* Option 3: Bounce & Pop-Up Zoom */}
              <button
                onClick={() => handleAnimationSelect('bounce-zoom')}
                onMouseEnter={() => void 0}
                className={`p-3.5 rounded-xl text-left border transition-all relative flex flex-col justify-between ${
                  selectedAnimation === 'bounce-zoom'
                    ? 'bg-gradient-to-b from-amber-950/90 to-red-950/90 border-amber-400 shadow-[0_0_20px_rgba(251,191,36,0.3)]'
                    : 'bg-black/40 border-white/10 hover:border-white/25 hover:bg-white/5'
                }`}
              >
                <div className="space-y-1.5">
                  <div className="flex items-center justify-between">
                    <span className="text-[11px] font-mono font-bold text-amber-400 uppercase tracking-wider">03 • Pop Bounce</span>
                    {selectedAnimation === 'bounce-zoom' && <span className="w-2 h-2 rounded-full bg-amber-400 animate-ping" />}
                  </div>
                  <h4 className="font-bold text-white text-sm">Pop-Up Memantul</h4>
                  <p className="text-xs text-stone-300 leading-relaxed">
                    Efek pegas dinamis (*spring overshoot*) berenergi tinggi.
                  </p>
                </div>
              </button>

              {/* Option 4: Typewriter & Glitch */}
              <button
                onClick={() => handleAnimationSelect('typewriter-glitch')}
                onMouseEnter={() => void 0}
                className={`p-3.5 rounded-xl text-left border transition-all relative flex flex-col justify-between ${
                  selectedAnimation === 'typewriter-glitch'
                    ? 'bg-gradient-to-b from-emerald-950/90 to-violet-950/90 border-emerald-400 shadow-[0_0_20px_rgba(52,211,153,0.3)]'
                    : 'bg-black/40 border-white/10 hover:border-white/25 hover:bg-white/5'
                }`}
              >
                <div className="space-y-1.5">
                  <div className="flex items-center justify-between">
                    <span className="text-[11px] font-mono font-bold text-emerald-400 uppercase tracking-wider">04 • Cyber</span>
                    {selectedAnimation === 'typewriter-glitch' && <span className="w-2 h-2 rounded-full bg-emerald-400 animate-ping" />}
                  </div>
                  <h4 className="font-bold text-white text-sm">Typewriter Glitch</h4>
                  <p className="text-xs text-stone-300 leading-relaxed">
                    Ketikan terminal AI super cepat dengan kursor pendar.
                  </p>
                </div>
              </button>

              {/* Option 5: Kinetic Slide-Up */}
              <button
                onClick={() => handleAnimationSelect('kinetic-slide')}
                onMouseEnter={() => void 0}
                className={`p-3.5 rounded-xl text-left border transition-all relative flex flex-col justify-between ${
                  selectedAnimation === 'kinetic-slide'
                    ? 'bg-gradient-to-b from-rose-950/90 to-orange-950/90 border-rose-400 shadow-[0_0_20px_rgba(251,113,133,0.3)]'
                    : 'bg-black/40 border-white/10 hover:border-white/25 hover:bg-white/5'
                }`}
              >
                <div className="space-y-1.5">
                  <div className="flex items-center justify-between">
                    <span className="text-[11px] font-mono font-bold text-rose-400 uppercase tracking-wider">05 • Kinetic</span>
                    {selectedAnimation === 'kinetic-slide' && <span className="w-2 h-2 rounded-full bg-rose-400 animate-ping" />}
                  </div>
                  <h4 className="font-bold text-white text-sm">Kinetic Slide-Up</h4>
                  <p className="text-xs text-stone-300 leading-relaxed">
                    Kata meluncur naik dari bawah dengan mulus.
                  </p>
                </div>
              </button>

              {/* Option 6: Neon Pulse & Wave */}
              <button
                onClick={() => handleAnimationSelect('pulse-glow')}
                onMouseEnter={() => void 0}
                className={`p-3.5 rounded-xl text-left border transition-all relative flex flex-col justify-between ${
                  selectedAnimation === 'pulse-glow'
                    ? 'bg-gradient-to-b from-fuchsia-950/90 to-indigo-950/90 border-fuchsia-400 shadow-[0_0_20px_rgba(232,121,249,0.3)]'
                    : 'bg-black/40 border-white/10 hover:border-white/25 hover:bg-white/5'
                }`}
              >
                <div className="space-y-1.5">
                  <div className="flex items-center justify-between">
                    <span className="text-[11px] font-mono font-bold text-fuchsia-400 uppercase tracking-wider">06 • Glow Wave</span>
                    {selectedAnimation === 'pulse-glow' && <span className="w-2 h-2 rounded-full bg-fuchsia-400 animate-ping" />}
                  </div>
                  <h4 className="font-bold text-white text-sm">Pulse & Glow Wave</h4>
                  <p className="text-xs text-stone-300 leading-relaxed">
                    Gelombang pendaran neon berpindah kata per kata.
                  </p>
                </div>
              </button>

              {/* Option 7: 3D Flip Rotate */}
              <button
                onClick={() => handleAnimationSelect('flip-rotate')}
                onMouseEnter={() => void 0}
                className={`p-3.5 rounded-xl text-left border transition-all relative flex flex-col justify-between ${
                  selectedAnimation === 'flip-rotate'
                    ? 'bg-gradient-to-b from-teal-950/90 to-emerald-950/90 border-teal-400 shadow-[0_0_20px_rgba(45,212,191,0.3)]'
                    : 'bg-black/40 border-white/10 hover:border-white/25 hover:bg-white/5'
                }`}
              >
                <div className="space-y-1.5">
                  <div className="flex items-center justify-between">
                    <span className="text-[11px] font-mono font-bold text-teal-400 uppercase tracking-wider">07 • 3D Flip</span>
                    {selectedAnimation === 'flip-rotate' && <span className="w-2 h-2 rounded-full bg-teal-400 animate-ping" />}
                  </div>
                  <h4 className="font-bold text-white text-sm">3D Flip Rotate</h4>
                  <p className="text-xs text-stone-300 leading-relaxed">
                    Rotasi kartu 3D flip 720° yang sangat memikat mata.
                  </p>
                </div>
              </button>

              {/* Option 8: Atmospheric Fade Drift */}
              <button
                onClick={() => handleAnimationSelect('fade-drift')}
                onMouseEnter={() => void 0}
                className={`p-3.5 rounded-xl text-left border transition-all relative flex flex-col justify-between ${
                  selectedAnimation === 'fade-drift'
                    ? 'bg-gradient-to-b from-sky-950/90 to-indigo-950/90 border-sky-400 shadow-[0_0_20px_rgba(56,189,248,0.3)]'
                    : 'bg-black/40 border-white/10 hover:border-white/25 hover:bg-white/5'
                }`}
              >
                <div className="space-y-1.5">
                  <div className="flex items-center justify-between">
                    <span className="text-[11px] font-mono font-bold text-sky-400 uppercase tracking-wider">08 • Drift</span>
                    {selectedAnimation === 'fade-drift' && <span className="w-2 h-2 rounded-full bg-sky-400 animate-ping" />}
                  </div>
                  <h4 className="font-bold text-white text-sm">Cinematic Drift</h4>
                  <p className="text-xs text-stone-300 leading-relaxed">
                    Transisi kabut pendar halus sinematik kelas atas.
                  </p>
                </div>
              </button>
            </div>
          </div>

          {/* SECTION 2: DESAIN VISUAL & ESTETIKA (8 Top Creator Presets) */}
          <div className="bg-[#131316] rounded-2xl p-6 border border-white/15 spacex- space-y-5 bg-black/60 backdrop-blur-xl">
            <div className="flex items-center justify-between border-b border-white/10 pb-3">
              <div className="flex items-center gap-2.5">
                <Layers className="w-4 h-4 text-amber-400" />
                <h3 className="font-display font-bold text-base text-white">
                  2. Desain Visual & Estetika (Visual Preset Style)
                </h3>
              </div>
              <span className="text-xs font-mono text-amber-300 bg-amber-950/60 px-3 py-1 rounded-full border border-amber-500/30 font-semibold">
                8 CREATOR PRESETS
              </span>
            </div>

            <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-3">
              {/* Preset 1: Alex Hormozi */}
              <button
                onClick={() => handlePresetSelect('hormozi')}
                onMouseEnter={() => void 0}
                className={`p-3.5 rounded-xl text-left border transition-all flex flex-col justify-between ${
                  selectedPreset === 'hormozi'
                    ? 'bg-amber-950/50 border-amber-400 shadow-[0_0_20px_rgba(251,191,36,0.35)]'
                    : 'bg-black/40 border-white/10 hover:border-white/25 hover:bg-white/5'
                }`}
              >
                <div className="space-y-1.5">
                  <div className="flex items-center justify-between">
                    <span className="text-[11px] font-mono font-bold text-yellow-400">HORMOZI $100M</span>
                    <Smile className="w-4 h-4 text-yellow-400" />
                  </div>
                  <h4 className="font-bold text-white text-sm">Alex Hormozi</h4>
                  <p className="text-xs text-stone-300 leading-relaxed">
                    Font tebal putih bersih, kata aktif berlatar emas kuning menyala + auto-emoji 3D.
                  </p>
                </div>
              </button>

              {/* Preset 2: MrBeast Hyper-Retention */}
              <button
                onClick={() => handlePresetSelect('mrbeast')}
                onMouseEnter={() => void 0}
                className={`p-3.5 rounded-xl text-left border transition-all flex flex-col justify-between ${
                  selectedPreset === 'mrbeast'
                    ? 'bg-violet-950/50 border-violet-400 shadow-[0_0_20px_rgba(34,211,238,0.35)]'
                    : 'bg-black/40 border-white/10 hover:border-white/25 hover:bg-white/5'
                }`}
              >
                <div className="space-y-1.5">
                  <div className="flex items-center justify-between">
                    <span className="text-[11px] font-mono font-bold text-violet-300">MRBEAST HYPER</span>
                    <Flame className="w-4 h-4 text-violet-400" />
                  </div>
                  <h4 className="font-bold text-white text-sm">MrBeast Action</h4>
                  <p className="text-xs text-stone-300 leading-relaxed">
                    Display font tilt -2°, aksen Violet Neon cerah & bayangan tajam bebas bercak hitam.
                  </p>
                </div>
              </button>

              {/* Preset 3: Minimalist Aesthetic */}
              <button
                onClick={() => handlePresetSelect('minimal-aesthetic')}
                onMouseEnter={() => void 0}
                className={`p-3.5 rounded-xl text-left border transition-all flex flex-col justify-between ${
                  selectedPreset === 'minimal-aesthetic'
                    ? 'bg-stone-900/80 border-white/50 shadow-[0_0_20px_rgba(255,255,255,0.2)]'
                    : 'bg-black/40 border-white/10 hover:border-white/25 hover:bg-white/5'
                }`}
              >
                <div className="space-y-1.5">
                  <div className="flex items-center justify-between">
                    <span className="text-[11px] font-mono font-bold text-stone-300">MINIMAL VLOG</span>
                    <BookOpen className="w-4 h-4 text-stone-400" />
                  </div>
                  <h4 className="font-bold text-white text-sm">Minimalis Estetik</h4>
                  <p className="text-xs text-stone-300 leading-relaxed">
                    Kapsul kaca hitam transparan lembut, teks putih jernih dengan underline bercahaya.
                  </p>
                </div>
              </button>

              {/* Preset 4: Gamer / Comic Book */}
              <button
                onClick={() => handlePresetSelect('gamer-comic')}
                onMouseEnter={() => void 0}
                className={`p-3.5 rounded-xl text-left border transition-all flex flex-col justify-between ${
                  selectedPreset === 'gamer-comic'
                    ? 'bg-rose-950/50 border-rose-400 shadow-[0_0_20px_rgba(244,63,94,0.35)]'
                    : 'bg-black/40 border-white/10 hover:border-white/25 hover:bg-white/5'
                }`}
              >
                <div className="space-y-1.5">
                  <div className="flex items-center justify-between">
                    <span className="text-[11px] font-mono font-bold text-rose-400">GAMER ARCADE</span>
                    <Gamepad2 className="w-4 h-4 text-rose-400" />
                  </div>
                  <h4 className="font-bold text-white text-sm">Gamer Comic</h4>
                  <p className="text-xs text-stone-300 leading-relaxed">
                    Warna emosi per kata (Merah Rage, Hijau Menang, Violet Combo) berkontras tinggi.
                  </p>
                </div>
              </button>

              {/* Preset 5: Neon Cyberpunk 2077 */}
              <button
                onClick={() => handlePresetSelect('neon-cyberpunk')}
                onMouseEnter={() => void 0}
                className={`p-3.5 rounded-xl text-left border transition-all flex flex-col justify-between ${
                  selectedPreset === 'neon-cyberpunk'
                    ? 'bg-indigo-950/50 border-violet-400 shadow-[0_0_20px_rgba(6,182,212,0.35)]'
                    : 'bg-black/40 border-white/10 hover:border-white/25 hover:bg-white/5'
                }`}
              >
                <div className="space-y-1.5">
                  <div className="flex items-center justify-between">
                    <span className="text-[11px] font-mono font-bold text-violet-400">CYBER HUD</span>
                    <Activity className="w-4 h-4 text-fuchsia-400" />
                  </div>
                  <h4 className="font-bold text-white text-sm">Cyberpunk 2077</h4>
                  <p className="text-xs text-stone-300 leading-relaxed">
                    Glow Neon Violet & Magenta, bracket HUD futuristik `[ ... ]` bersinar tajam.
                  </p>
                </div>
              </button>

              {/* Preset 6: Ali Abdaal Notion Highlighter */}
              <button
                onClick={() => handlePresetSelect('ali-abdaal')}
                onMouseEnter={() => void 0}
                className={`p-3.5 rounded-xl text-left border transition-all flex flex-col justify-between ${
                  selectedPreset === 'ali-abdaal'
                    ? 'bg-emerald-950/50 border-emerald-400 shadow-[0_0_20px_rgba(52,211,153,0.35)]'
                    : 'bg-black/40 border-white/10 hover:border-white/25 hover:bg-white/5'
                }`}
              >
                <div className="space-y-1.5">
                  <div className="flex items-center justify-between">
                    <span className="text-[11px] font-mono font-bold text-emerald-400">ALI ABDAAL</span>
                    <Sparkles className="w-4 h-4 text-emerald-400" />
                  </div>
                  <h4 className="font-bold text-white text-sm">Notion Highlight</h4>
                  <p className="text-xs text-stone-300 leading-relaxed">
                    Efek stabilo fluorescent di belakang kata kunci, sangat elegan untuk edukasi.
                  </p>
                </div>
              </button>

              {/* Preset 7: Iman Gadzhi Luxury Serif */}
              <button
                onClick={() => handlePresetSelect('iman-gadzhi')}
                onMouseEnter={() => void 0}
                className={`p-3.5 rounded-xl text-left border transition-all flex flex-col justify-between ${
                  selectedPreset === 'iman-gadzhi'
                    ? 'bg-amber-950/50 border-yellow-200 shadow-[0_0_20px_rgba(254,240,138,0.35)]'
                    : 'bg-black/40 border-white/10 hover:border-white/25 hover:bg-white/5'
                }`}
              >
                <div className="space-y-1.5">
                  <div className="flex items-center justify-between">
                    <span className="text-[11px] font-mono font-bold text-yellow-200">LUXURY SERIF</span>
                    <Crown className="w-4 h-4 text-yellow-300" />
                  </div>
                  <h4 className="font-bold text-white text-sm">Iman Gadzhi</h4>
                  <p className="text-xs text-stone-300 leading-relaxed">
                    Tipografi Serif editorial mewah dengan pendaran emas champagne sinematik.
                  </p>
                </div>
              </button>

              {/* Preset 8: Anime Impact */}
              <button
                onClick={() => handlePresetSelect('anime-impact')}
                onMouseEnter={() => void 0}
                className={`p-3.5 rounded-xl text-left border transition-all flex flex-col justify-between ${
                  selectedPreset === 'anime-impact'
                    ? 'bg-orange-950/50 border-orange-400 shadow-[0_0_20px_rgba(249,115,22,0.35)]'
                    : 'bg-black/40 border-white/10 hover:border-white/25 hover:bg-white/5'
                }`}
              >
                <div className="space-y-1.5">
                  <div className="flex items-center justify-between">
                    <span className="text-[11px] font-mono font-bold text-orange-400">SHONEN SPEED</span>
                    <FastForward className="w-4 h-4 text-orange-400" />
                  </div>
                  <h4 className="font-bold text-white text-sm">Anime Impact</h4>
                  <p className="text-xs text-stone-300 leading-relaxed">
                    Gaya Manga dengan getaran kecepatan visual dan aksen api membara.
                  </p>
                </div>
              </button>
            </div>
          </div>

          {/* SECTION 3: PERSONALISASI DETAIL (Warna, Tipografi, Posisi, Ukuran, Emojis) */}
          <div className="bg-[#131316] rounded-2xl p-6 border border-white/15 bg-black/60 backdrop-blur-xl space-y-6">
            <div className="flex items-center justify-between border-b border-white/10 pb-3">
              <span className="text-sm font-mono font-bold text-white uppercase tracking-wider flex items-center gap-2">
                <Sliders className="w-4 h-4 text-violet-400" />
                <span>3. Personalisasi Warna, Font & Tata Letak Geometry</span>
              </span>
              <span className="text-xs font-mono text-emerald-400 flex items-center gap-1.5 bg-emerald-950/50 px-2.5 py-0.5 rounded-full border border-emerald-500/30">
                <Activity className="w-3.5 h-3.5 animate-pulse" />
                <span>120 FPS ZERO BUG</span>
              </span>
            </div>

            <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-5 text-xs">
              
              {/* Highlight Color Palette Picker */}
              <div className="space-y-2">
                <label className="text-xs font-mono font-bold text-stone-300 flex items-center gap-2">
                  <Palette className="w-3.5 h-3.5 text-violet-400" />
                  <span>WARNA HIGHLIGHT AKTIF:</span>
                </label>
                <div className="flex items-center gap-2 p-1.5 rounded-xl bg-black/60 border border-white/10">
                  {COLOR_PALETTES.map((color) => (
                    <button
                      key={color.id}
                      onClick={() => {  setHighlightColor(color.hex); }}
                      className={`w-7 h-7 rounded-lg transition-all flex items-center justify-center ${color.bgClass} ${
                        highlightColor === color.hex ? 'ring-2 ring-white scale-110 shadow-lg' : 'opacity-60 hover:opacity-100'
                      }`}
                      title={color.label}
                    >
                      {highlightColor === color.hex && <Check className="w-4 h-4 text-black" />}
                    </button>
                  ))}
                </div>
              </div>

              {/* Typography / Font Family Picker */}
              <div className="space-y-2">
                <label className="text-xs font-mono font-bold text-stone-300 flex items-center gap-2">
                  <Type className="w-3.5 h-3.5 text-amber-400" />
                  <span>GAYA TIPOGRAFI / FONT:</span>
                </label>
                <div className="grid grid-cols-4 rounded-xl bg-black/60 border border-white/10 p-1">
                  <button
                    onClick={() => {  setSelectedFontFamily('sans'); }}
                    className={`py-1.5 px-2 rounded-lg text-xs font-bold font-sans transition-all truncate ${
                      selectedFontFamily === 'sans' ? 'bg-violet-500 text-black shadow-md' : 'text-stone-400 hover:text-white'
                    }`}
                  >
                    Sans
                  </button>
                  <button
                    onClick={() => {  setSelectedFontFamily('display'); }}
                    className={`py-1.5 px-2 rounded-lg text-xs font-bold font-display transition-all truncate ${
                      selectedFontFamily === 'display' ? 'bg-violet-500 text-black shadow-md' : 'text-stone-400 hover:text-white'
                    }`}
                  >
                    Display
                  </button>
                  <button
                    onClick={() => {  setSelectedFontFamily('mono'); }}
                    className={`py-1.5 px-2 rounded-lg text-xs font-bold font-mono transition-all truncate ${
                      selectedFontFamily === 'mono' ? 'bg-violet-500 text-black shadow-md' : 'text-stone-400 hover:text-white'
                    }`}
                  >
                    Mono
                  </button>
                  <button
                    onClick={() => {  setSelectedFontFamily('serif'); }}
                    className={`py-1.5 px-2 rounded-lg text-xs font-bold font-serif italic transition-all truncate ${
                      selectedFontFamily === 'serif' ? 'bg-violet-500 text-black shadow-md' : 'text-stone-400 hover:text-white'
                    }`}
                  >
                    Serif
                  </button>
                </div>
              </div>

              {/* Vertical Position */}
              <div className="space-y-2">
                <label className="text-xs font-mono font-bold text-stone-300 block">POSISI VERTIKAL:</label>
                <div className="flex rounded-xl bg-black/60 border border-white/10 p-1">
                  <button
                    onClick={() => {  setSelectedPosition('top'); }}
                    className={`flex-1 py-1.5 px-2 rounded-lg text-xs font-mono font-bold transition-all ${
                      selectedPosition === 'top' ? 'bg-amber-500 text-black shadow-md' : 'text-stone-400 hover:text-white'
                    }`}
                  >
                    Top
                  </button>
                  <button
                    onClick={() => {  setSelectedPosition('center'); }}
                    className={`flex-1 py-1.5 px-2 rounded-lg text-xs font-mono font-bold transition-all ${
                      selectedPosition === 'center' ? 'bg-amber-500 text-black shadow-md' : 'text-stone-400 hover:text-white'
                    }`}
                  >
                    Center
                  </button>
                  <button
                    onClick={() => {  setSelectedPosition('bottom'); }}
                    className={`flex-1 py-1.5 px-2 rounded-lg text-xs font-mono font-bold transition-all ${
                      selectedPosition === 'bottom' ? 'bg-amber-500 text-black shadow-md' : 'text-stone-400 hover:text-white'
                    }`}
                  >
                    Bottom
                  </button>
                </div>
              </div>

              {/* Font Size */}
              <div className="space-y-2">
                <label className="text-xs font-mono font-bold text-stone-300 block">UKURAN FONT:</label>
                <div className="grid grid-cols-4 rounded-xl bg-black/60 border border-white/10 p-1">
                  <button
                    onClick={() => {  setSelectedFontSize('compact'); }}
                    className={`py-1.5 px-1 rounded-lg text-xs font-mono font-bold transition-all ${
                      selectedFontSize === 'compact' ? 'bg-rose-500 text-white shadow-md' : 'text-stone-400 hover:text-white'
                    }`}
                  >
                    S
                  </button>
                  <button
                    onClick={() => {  setSelectedFontSize('normal'); }}
                    className={`py-1.5 px-1 rounded-lg text-xs font-mono font-bold transition-all ${
                      selectedFontSize === 'normal' ? 'bg-rose-500 text-white shadow-md' : 'text-stone-400 hover:text-white'
                    }`}
                  >
                    M
                  </button>
                  <button
                    onClick={() => {  setSelectedFontSize('large'); }}
                    className={`py-1.5 px-1 rounded-lg text-xs font-mono font-bold transition-all ${
                      selectedFontSize === 'large' ? 'bg-rose-500 text-white shadow-md' : 'text-stone-400 hover:text-white'
                    }`}
                  >
                    L
                  </button>
                  <button
                    onClick={() => {  setSelectedFontSize('huge'); }}
                    className={`py-1.5 px-1 rounded-lg text-xs font-mono font-bold transition-all ${
                      selectedFontSize === 'huge' ? 'bg-rose-500 text-white shadow-md' : 'text-stone-400 hover:text-white'
                    }`}
                  >
                    XL
                  </button>
                </div>
              </div>

              {/* Glow Intensity */}
              <div className="space-y-2">
                <label className="text-xs font-mono font-bold text-stone-300 block">INTENSITAS GLOW & BAYANGAN:</label>
                <div className="grid grid-cols-3 rounded-xl bg-black/60 border border-white/10 p-1">
                  <button
                    onClick={() => {  setSelectedGlowStyle('subtle'); }}
                    className={`py-1.5 px-2 rounded-lg text-xs font-mono font-bold transition-all truncate ${
                      selectedGlowStyle === 'subtle' ? 'bg-purple-500 text-white shadow-md' : 'text-stone-400 hover:text-white'
                    }`}
                  >
                    Halus
                  </button>
                  <button
                    onClick={() => {  setSelectedGlowStyle('intense'); }}
                    className={`py-1.5 px-2 rounded-lg text-xs font-mono font-bold transition-all truncate ${
                      selectedGlowStyle === 'intense' ? 'bg-purple-500 text-white shadow-md' : 'text-stone-400 hover:text-white'
                    }`}
                  >
                    Intens
                  </button>
                  <button
                    onClick={() => {  setSelectedGlowStyle('outline-clean'); }}
                    className={`py-1.5 px-2 rounded-lg text-xs font-mono font-bold transition-all truncate ${
                      selectedGlowStyle === 'outline-clean' ? 'bg-purple-500 text-white shadow-md' : 'text-stone-400 hover:text-white'
                    }`}
                  >
                    Outline
                  </button>
                </div>
              </div>

              {/* Auto Emojis Toggle */}
              <div className="space-y-2">
                <label className="text-xs font-mono font-bold text-stone-300 block">AUTO 3D EMOJI:</label>
                <button
                  onClick={() => {  setShowEmojis(!showEmojis); }}
                  className={`w-full py-2 px-3 rounded-xl border font-mono text-xs font-bold flex items-center justify-between transition-all ${
                    showEmojis 
                      ? 'bg-emerald-950/60 border-emerald-400/40 text-emerald-300 shadow-[0_0_15px_rgba(52,211,153,0.2)]' 
                      : 'bg-black/60 border-white/10 text-stone-400 hover:border-white/20'
                  }`}
                >
                  <span className="flex items-center gap-2">
                    <Smile className="w-4 h-4 text-emerald-400" />
                    <span>3D Viral Emojis</span>
                  </span>
                  <span className="font-mono text-xs font-bold">{showEmojis ? 'AKTIF' : 'NONAKTIF'}</span>
                </button>
              </div>

            </div>
          </div>

          {/* Compact Apply & Sync Action Bar */}
          <div className="flex items-center justify-between p-3 px-4 rounded-xl bg-black/60 border border-white/10 backdrop-blur-xl">
            <div className="flex items-center gap-2 text-xs font-mono text-stone-300">
              <span className="w-2 h-2 rounded-full bg-violet-400 animate-pulse" />
              <span className="text-white font-bold uppercase">{selectedPreset}</span>
              <span className="text-stone-500">•</span>
              <span className="text-stone-400 uppercase">{selectedAnimation}</span>
            </div>

            <div className="flex items-center gap-2">
              <button
                onClick={handleCopyPresetConfig}
                onMouseEnter={() => void 0}
                className="px-2.5 py-1.5 rounded-lg bg-white/5 hover:bg-white/10 text-stone-400 hover:text-white border border-white/10 text-xs font-mono flex items-center gap-1 transition-all"
                title="Copy JSON Config"
              >
                {isCopied ? <Check className="w-3 h-3 text-emerald-400" /> : <Copy className="w-3 h-3 text-stone-400" />}
                <span>JSON</span>
              </button>

              <button
                onClick={handleApplyPreset}
                onMouseEnter={() => void 0}
                className={`px-4 py-1.5 rounded-lg font-mono text-xs font-bold uppercase tracking-wider flex items-center gap-1.5 transition-all active:scale-95 ${
                  isApplied
                    ? 'bg-emerald-400 text-black shadow-[0_0_15px_rgba(52,211,153,0.6)]'
                    : 'bg-white text-black hover:bg-violet-400 shadow-[0_0_15px_rgba(255,255,255,0.3)]'
                }`}
              >
                {isApplied ? (
                  <>
                    <CheckCircle2 className="w-3.5 h-3.5 text-black" />
                    <span>Applied</span>
                  </>
                ) : (
                  <>
                    <Zap className="w-3.5 h-3.5 fill-black text-black" />
                    <span>Apply</span>
                  </>
                )}
              </button>
            </div>
          </div>

          {/* Minimalist Toast Feedback */}
          <AnimatePresence>
            {appliedToast && (
              <motion.div
                initial={{ opacity: 0, y: -6 }}
                animate={{ opacity: 1, y: 0 }}
                exit={{ opacity: 0, y: -6 }}
                className="p-2.5 px-3.5 rounded-xl bg-emerald-950/90 border border-emerald-400/50 text-emerald-300 text-xs font-mono flex items-center justify-between shadow-[0_0_20px_rgba(16,185,129,0.2)]"
              >
                <div className="flex items-center gap-2">
                  <CheckCircle2 className="w-3.5 h-3.5 text-emerald-400" />
                  <span>{appliedToast}</span>
                </div>
                <span className="text-[10px] text-emerald-400/80 uppercase font-bold">100% SYNCED</span>
              </motion.div>
            )}
          </AnimatePresence>
        </div>

        {/* Right Column: 9:16 Authentic High-End Sandbox Simulator (5 cols) */}
        <div className="lg:col-span-5 flex flex-col items-center">
          <div className="w-full max-w-sm rounded-3xl border border-white/10 p-4 space-y-4 bg-[#131316]">
            {/* Phone Simulator Top Bar */}
            <div className="flex items-center justify-between px-2 text-[10px] font-mono text-stone-400">
              <div className="flex items-center gap-2">
                <span className="w-2 h-2 rounded-full bg-emerald-400 animate-pulse" />
                <span className="text-violet-300 font-bold tracking-wider">9:16 VIRAL SIMULATOR</span>
              </div>
              <div className="flex items-center gap-1.5">
                <button
                  onClick={() => {
                    
                    setPlaybackSpeed((prev) => (prev === 1 ? 1.25 : prev === 1.25 ? 1.5 : prev === 1.5 ? 0.75 : 1));
                  }}
                  className="px-1.5 py-0.5 rounded bg-white/10 hover:bg-white/20 text-stone-300 text-[10px] font-mono"
                  title="Kecepatan Bicara"
                >
                  {playbackSpeed}x
                </button>
                <button
                  onClick={() => {
                    
                    setIsPlaying(!isPlaying);
                  }}
                  className="p-1.5 rounded bg-white/10 hover:bg-white/20 text-white"
                  title={isPlaying ? 'Pause Simulation' : 'Play Simulation'}
                >
                  {isPlaying ? <Pause className="w-3 h-3" /> : <Play className="w-3 h-3" />}
                </button>
                <button
                  onClick={() => {
                    
                    setWordIndex(0);
                    setLineIndex(0);
                  }}
                  className="p-1.5 rounded bg-white/10 hover:bg-white/20 text-stone-300 hover:text-white"
                  title="Restart dari Awal"
                >
                  <RotateCcw className="w-3 h-3" />
                </button>
              </div>
            </div>

            {/* Script Category Switcher Pills */}
            <div className="grid grid-cols-4 gap-1 p-1 rounded-xl bg-black/60 border border-white/10 text-[9px] font-mono">
              {Object.keys(SCRIPT_LIBRARIES).map((key) => {
                const isActive = activeCategory === key;
                return (
                  <button
                    key={key}
                    onClick={() => {
                      
                      setActiveCategory(key);
                      setWordIndex(0);
                      setLineIndex(0);
                    }}
                    className={`py-1 px-1 rounded-lg truncate font-bold transition-all text-center ${
                      isActive
                        ? 'bg-violet-500 text-black shadow-[0_0_10px_rgba(34,211,238,0.4)]'
                        : 'text-stone-400 hover:text-white hover:bg-white/5'
                    }`}
                  >
                    {key.toUpperCase()}
                  </button>
                );
              })}
            </div>

            {/* 9:16 Video Display Area with 120 FPS Subtitle Rendering */}
            <div className="relative aspect-[9/16] w-full rounded-2xl overflow-hidden bg-stone-950 border border-white/15 shadow-2xl flex flex-col justify-between p-4 select-none">
              
              {/* Background Video Layer */}
              <video
                key={SAMPLE_BG_VIDEOS[activeBgVideoIdx].id}
                autoPlay
                loop
                muted
                playsInline
                className="absolute inset-0 w-full h-full object-cover scale-105 opacity-75 filter brightness-95 will-change-transform"
              >
                <source src={SAMPLE_BG_VIDEOS[activeBgVideoIdx].url} type="video/mp4" />
              </video>

              {/* Realistic Contrast Vignette (Guarantees Perfect Legibility) */}
              <div className="absolute inset-0 bg-gradient-to-t from-black/85 via-black/20 to-black/60 pointer-events-none" />

              {/* Top HUD Badges */}
              <div className="relative z-10 flex items-center justify-between text-[10px] font-mono text-white/90">
                <span className="bg-black/60 px-2 py-0.5 rounded backdrop-blur-md border border-white/15">
                  {selectedAnimation.toUpperCase()}
                </span>
                <div className="flex items-center gap-1">
                  <span className="bg-amber-500/20 text-amber-300 px-2 py-0.5 rounded font-bold backdrop-blur-md border border-amber-500/30">
                    HOOK: {currentLine.hookScore || 98}%
                  </span>
                </div>
              </div>

              {/* RENDERED SUBTITLE STAGE (Position Dependent: Top, Center, Bottom) */}
              <div 
                className={`relative z-10 px-2 py-3 text-center transition-all duration-300 flex items-center justify-center ${
                  selectedPosition === 'top' ? 'mt-8 mb-auto' : selectedPosition === 'center' ? 'my-auto' : 'mt-auto mb-6'
                }`}
              >
                <LiveSubtitleRenderer
                  currentLine={currentLine}
                  wordIndex={wordIndex}
                  lineIndex={lineIndex}
                  config={liveConfig}
                />
              </div>

              {/* Bottom Video Switcher Footer */}
              <div className="relative z-10 flex items-center justify-between text-[10px] font-mono text-stone-400 bg-black/75 p-2 rounded-xl border border-white/10 backdrop-blur-md">
                <div className="flex items-center gap-1.5">
                  <span className="text-stone-400">BG:</span>
                  {SAMPLE_BG_VIDEOS.map((vid, idx) => (
                    <button
                      key={vid.id}
                      onClick={() => {  setActiveBgVideoIdx(idx); }}
                      className={`px-1.5 py-0.5 rounded text-[9px] ${
                        activeBgVideoIdx === idx ? 'bg-white/20 text-white font-bold' : 'text-stone-500 hover:text-stone-300'
                      }`}
                    >
                      0{idx + 1}
                    </button>
                  ))}
                </div>
                <div className="text-violet-300 font-bold flex items-center gap-1">
                  <Activity className="w-3 h-3 text-emerald-400" />
                  <span>120 FPS GPU</span>
                </div>
              </div>

            </div>
          </div>
        </div>
      </div>
    </section>
  );
};
