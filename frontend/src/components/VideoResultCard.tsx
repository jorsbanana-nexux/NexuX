import React, { useState, useEffect, useRef } from 'react';
import { motion, useMotionValue, useSpring, useTransform } from 'motion/react';
import { 
  Play, 
  Pause, 
  Flame, 
  Download, 
  Sparkles, 
  Clock, 
  CheckCircle, 
  Copy 
} from 'lucide-react';
import { sound } from '../utils/soundEffects';
import { subtitleStore } from '../utils/subtitleStore';
import { SubtitleConfig, SubtitleScriptLine } from '../types/subtitles';
import { LiveSubtitleRenderer } from './LiveSubtitleRenderer';

export interface GeneratedClip {
  id: string;
  title: string;
  hookCategory: string;
  duration: string;
  viralScore: number;
  timestampRange: string;
  subtitleSnippet: string;
  aspectRatio: string;
  videoUrl: string;
  tags: string[];
}

interface VideoResultCardProps {
  clip: GeneratedClip;
  index: number;
  onPreview: (clip: GeneratedClip) => void;
}

export const VideoResultCard: React.FC<VideoResultCardProps> = ({ clip, index, onPreview }) => {
  const [currentScore, setCurrentScore] = useState(0);
  const [isPlaying, setIsPlaying] = useState(false);
  const [copied, setCopied] = useState(false);
  const [subConfig, setSubConfig] = useState<SubtitleConfig>(subtitleStore.get());
  const [wordIndex, setWordIndex] = useState(0);
  const cardRef = useRef<HTMLDivElement>(null);
  const videoRef = useRef<HTMLVideoElement>(null);

  useEffect(() => {
    const unsub = subtitleStore.subscribe((cfg) => setSubConfig(cfg));
    return () => unsub();
  }, []);

  // Parse words for high-fidelity subtitle rendering
  const words = React.useMemo(() => {
    return clip.subtitleSnippet.split(' ').map((w, idx) => ({
      text: w,
      highlight: idx % 2 === 0,
      emoji: idx === 1 ? '⚡' : undefined,
      colorType: (idx % 2 === 0 ? 'cyan' : 'normal') as any,
    }));
  }, [clip.subtitleSnippet]);

  const currentLine: SubtitleScriptLine = React.useMemo(() => ({
    lineText: clip.subtitleSnippet,
    words,
    hookScore: clip.viralScore,
  }), [clip.subtitleSnippet, words, clip.viralScore]);

  // Word stepper when hovering / playing video
  useEffect(() => {
    if (!isPlaying) {
      setWordIndex(0);
      return;
    }
    const timer = setInterval(() => {
      setWordIndex((prev) => (prev + 1) % words.length);
    }, 420);
    return () => clearInterval(timer);
  }, [isPlaying, words.length]);

  // High-performance 3D tilt via Motion Values (Apple/SpaceX standard)
  const normX = useMotionValue(0);
  const normY = useMotionValue(0);
  const springConfig = { damping: 20, stiffness: 260 };
  const rotateX = useSpring(useTransform(normY, [-0.5, 0.5], [7, -7]), springConfig);
  const rotateY = useSpring(useTransform(normX, [-0.5, 0.5], [-7, 7]), springConfig);

  // Fast count-up animation for Viral Potential Score (from 0 to clip.viralScore)
  useEffect(() => {
    let start = 0;
    const end = clip.viralScore;
    const duration = 1000;
    const stepTime = 16;
    const totalSteps = duration / stepTime;
    const increment = end / totalSteps;

    const timer = setInterval(() => {
      start += increment;
      if (start >= end) {
        setCurrentScore(end);
        clearInterval(timer);
      } else {
        setCurrentScore(Math.floor(start));
      }
    }, stepTime);

    return () => clearInterval(timer);
  }, [clip.viralScore]);

  // Handle Parallax 3D Tilt on mouse move
  const handleMouseMove = (e: React.MouseEvent<HTMLDivElement>) => {
    if (!cardRef.current) return;
    const rect = cardRef.current.getBoundingClientRect();
    normX.set((e.clientX - rect.left) / rect.width - 0.5);
    normY.set((e.clientY - rect.top) / rect.height - 0.5);
  };

  const handleMouseLeave = () => {
    normX.set(0);
    normY.set(0);
    if (videoRef.current) {
      videoRef.current.pause();
      setIsPlaying(false);
    }
  };

  const handleMouseEnter = () => {
    sound.playHover();
    if (videoRef.current) {
      videoRef.current.play().catch(() => {});
      setIsPlaying(true);
    }
  };

  const handleCopyHook = (e: React.MouseEvent) => {
    e.stopPropagation();
    sound.playClick();
    navigator.clipboard.writeText(clip.subtitleSnippet);
    setCopied(true);
    setTimeout(() => setCopied(false), 2000);
  };

  const handleCardClick = () => {
    sound.playClick();
    onPreview(clip);
  };

  return (
    <motion.div
      ref={cardRef}
      initial={{ opacity: 0, y: 40, scale: 0.94 }}
      animate={{ opacity: 1, y: 0, scale: 1 }}
      transition={{
        duration: 0.6,
        delay: index * 0.15,
        ease: [0.16, 1, 0.3, 1],
      }}
      onMouseMove={handleMouseMove}
      onMouseEnter={handleMouseEnter}
      onMouseLeave={handleMouseLeave}
      onClick={handleCardClick}
      data-cursor-text="PREVIEW 9:16"
      style={{
        transformStyle: 'preserve-3d',
        rotateX,
        rotateY,
        transformPerspective: 1000,
      }}
      className="group relative rounded-3xl bg-stone-900/90 border border-white/15 p-4 flex flex-col justify-between cursor-pointer shadow-[0_15px_40px_rgba(0,0,0,0.7)] hover:border-cyan-400/80 hover:shadow-[0_0_35px_rgba(6,182,212,0.3)] overflow-hidden select-none will-change-transform"
    >
      {/* Background Subtle Gradient Glow */}
      <div className="absolute -inset-1 bg-gradient-to-b from-cyan-500/10 via-transparent to-purple-500/10 rounded-3xl opacity-0 group-hover:opacity-100 transition-opacity duration-300 pointer-events-none" />

      {/* Top Header Information inside card */}
      <div className="flex items-center justify-between pb-3 z-10">
        <div className="inline-flex items-center gap-1.5 px-2.5 py-1 rounded-full bg-white/10 border border-white/10 text-[11px] font-mono text-cyan-300">
          <Sparkles className="w-3 h-3 text-cyan-400" />
          <span>{clip.hookCategory}</span>
        </div>

        {/* Viral Potential Counter Badge with Rapid Counting */}
        <div className="flex items-center gap-1.5 px-2.5 py-1 rounded-full bg-gradient-to-r from-red-500/20 to-amber-500/20 border border-amber-500/40 text-amber-300 font-mono text-xs font-bold shadow-[0_0_12px_rgba(245,158,11,0.3)]">
          <Flame className="w-3.5 h-3.5 text-amber-400 animate-pulse" />
          <span>VIRAL {currentScore}/99</span>
        </div>
      </div>

      {/* 9:16 Vertical Video Preview Stage */}
      <div className="relative aspect-[9/14] w-full rounded-2xl overflow-hidden bg-black/90 border border-white/10 my-2 flex items-center justify-center">
        {/* Video Element */}
        <video
          ref={videoRef}
          src={clip.videoUrl}
          loop
          muted
          playsInline
          className="w-full h-full object-cover group-hover:scale-105 transition-transform duration-500 will-change-transform"
        />

        {/* Gradient Vignette Overlay for Crisp Contrast */}
        <div className="absolute inset-0 bg-gradient-to-t from-black/85 via-transparent to-black/40 pointer-events-none" />

        {/* Subtitle Kinetic Mockup Over Video Dynamically Synced */}
        <div className={`absolute inset-x-3 text-center pointer-events-none transition-all duration-300 flex items-center justify-center ${
          subConfig.position === 'top' ? 'top-8' : subConfig.position === 'center' ? 'top-1/2 -translate-y-1/2' : 'bottom-6'
        }`}>
          <LiveSubtitleRenderer
            currentLine={currentLine}
            wordIndex={wordIndex}
            lineIndex={0}
            config={subConfig}
          />
        </div>

        {/* Play / Pause Indicator Icon */}
        <div className="absolute inset-0 flex items-center justify-center opacity-0 group-hover:opacity-100 transition-opacity pointer-events-none">
          <div className="w-12 h-12 rounded-full bg-cyan-400/90 text-black flex items-center justify-center shadow-[0_0_25px_rgba(34,211,238,0.8)]">
            {isPlaying ? <Pause className="w-5 h-5 fill-current" /> : <Play className="w-5 h-5 fill-current ml-0.5" />}
          </div>
        </div>

        {/* Time Stamp overlay badge */}
        <div className="absolute top-3 left-3 px-2 py-0.5 rounded-md bg-black/60 backdrop-blur-sm border border-white/10 text-[10px] font-mono text-stone-300 flex items-center gap-1">
          <Clock className="w-2.5 h-2.5 text-cyan-400" />
          <span>{clip.timestampRange}</span>
        </div>

        {/* Duration badge */}
        <div className="absolute top-3 right-3 px-2 py-0.5 rounded-md bg-black/60 backdrop-blur-sm border border-white/10 text-[10px] font-mono text-stone-300">
          {clip.duration}
        </div>
      </div>

      {/* Card Footer Details & Actions */}
      <div className="pt-2 space-y-3 z-10">
        <div>
          <h4 className="text-sm font-bold text-white font-display line-clamp-1 group-hover:text-cyan-300 transition-colors">
            {clip.title}
          </h4>
          <div className="flex flex-wrap gap-1 mt-1.5">
            {clip.tags.map((tag, idx) => (
              <span key={idx} className="text-[10px] font-mono text-stone-400 bg-white/5 px-2 py-0.5 rounded">
                #{tag}
              </span>
            ))}
          </div>
        </div>

        {/* Action button row */}
        <div className="flex items-center gap-2 pt-1 border-t border-white/10">
          <button
            onClick={handleCopyHook}
            onMouseEnter={() => sound.playHover()}
            title="Salin Kalimat Hook"
            className="flex-1 inline-flex items-center justify-center gap-1.5 py-2 px-3 rounded-xl bg-white/5 hover:bg-white/15 text-stone-300 hover:text-white text-xs font-mono transition-colors"
          >
            {copied ? (
              <>
                <CheckCircle className="w-3.5 h-3.5 text-emerald-400" />
                <span className="text-emerald-400">Tersalin</span>
              </>
            ) : (
              <>
                <Copy className="w-3.5 h-3.5" />
                <span>Salin Hook</span>
              </>
            )}
          </button>

          <button
            onClick={(e) => {
              e.stopPropagation();
              sound.playClick();
              onPreview(clip);
            }}
            onMouseEnter={() => sound.playHover()}
            title="Download Clip"
            className="p-2 rounded-xl bg-cyan-500/20 hover:bg-cyan-500/40 text-cyan-300 hover:text-cyan-100 border border-cyan-500/30 transition-colors"
          >
            <Download className="w-4 h-4" />
          </button>
        </div>
      </div>
    </motion.div>
  );
};
