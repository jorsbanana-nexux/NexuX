/**
 * NexuX V8.5 — Post-Render Personalization Editor
 * ================================================
 * 
 * This is the full-screen editor that appears AFTER clips are rendered.
 * Like Opus Clip's editor, it provides:
 * 
 * 1. VIDEO PREVIEW CANVAS — live preview with real-time edits
 * 2. CAPTION STUDIO — change subtitle style, font, color, animation, position
 * 3. EFFECTS PANEL — zoom, crop, color grade, speed ramp, transitions
 * 4. TEMPLATE GALLERY — famous creator templates (Hormozi, MrBeast, etc.)
 * 5. TRIM & CUT — fine-tune clip start/end, split, merge
 * 6. AUDIO MIXER — BGM volume, voice normalization, SFX
 * 7. LAYOUT & ASPECT — 9:16, 1:1, 4:5, 16:9 with auto-reframe
 * 8. BRANDING — watermark, logo, intro/outro
 * 9. EXPORT & PUBLISH — re-render with changes, then auto-post
 * 
 * Flow: ResultsGrid → Click "Personalize" → ClipEditorStudio opens full-screen
 */

import React, { useState, useRef, useEffect, useCallback } from 'react';
import { motion, AnimatePresence } from 'motion/react';
import {
  // Navigation
  ArrowLeft, X, Download, RotateCcw, Share2, Check,
  // Editor tabs
  Type, Sparkles, Scissors, Volume2, Layout, Palette, 
  Wand2, Film, Zap, Play, Pause, SkipBack, SkipForward,
  // Controls
  Sliders, Eye, Copy, ChevronRight, ChevronLeft,
  Bold, Italic, AlignLeft, AlignCenter, AlignRight,
  Maximize2, Minimize2, RotateCw, Crop,
  // Status
  Loader2, AlertCircle, CheckCircle2,
} from 'lucide-react';
import { sound } from '../utils/soundEffects';
import { MagneticElement } from './MagneticElement';
import { TiltCard } from './TiltCard';
import { LiveSubtitleRenderer } from './LiveSubtitleRenderer';
import { subtitleStore } from '../utils/subtitleStore';
import {
  SubtitleConfig, SubtitleAnimationStyle, SubtitleVisualPreset,
  SubtitlePosition, SubtitleFontSize, SubtitleFontFamily, SubtitleGlowStyle,
  SubtitleScriptLine,
} from '../types/subtitles';
import { GeneratedClip } from './VideoResultCard';
import { nexuxApi, buildOutputUrl } from '../api/nexuxApi';

// ── Types ──────────────────────────────────────────

type EditorTab =
  | 'captions'    // Subtitle/caption editing
  | 'effects'     // Visual effects (zoom, color, speed)
  | 'templates'   // Creator template gallery
  | 'trim'        // Trim & cut
  | 'audio'       // Audio mixing
  | 'layout'      // Aspect ratio & layout
  | 'branding'    // Watermark, logo, intro
  | 'export';     // Export & publish

type AspectRatio = '9:16' | '1:1' | '4:5' | '16:9';

interface EditorState {
  // Caption settings
  captionStyle: SubtitleVisualPreset;
  animation: SubtitleAnimationStyle;
  fontSize: SubtitleFontSize;
  fontFamily: SubtitleFontFamily;
  position: SubtitlePosition;
  glowStyle: SubtitleGlowStyle;
  primaryColor: string;
  highlightColor: string;
  showEmojis: boolean;
  highlightEmphasis: boolean;
  progressbar: boolean;

  // Effects
  zoomLevel: number;          // 1.0 = no zoom, 2.0 = 2x
  zoomStyle: 'subtle' | 'dramatic' | 'punch' | 'breathing' | 'none';
  colorGrade: 'none' | 'warm' | 'cool' | 'vibrant' | 'cinematic' | 'vintage';
  speedRamp: boolean;
  speedRampType: 'slowmo' | 'speedup' | 'punch' | 'none';

  // Layout
  aspectRatio: AspectRatio;
  autoReframe: boolean;
  faceTracking: boolean;

  // Audio
  bgmVolume: number;          // 0-100
  voiceVolume: number;        // 0-100
  normalizeAudio: boolean;
  bassBoost: boolean;
  sfxEnabled: boolean;

  // Branding
  watermarkText: string;
  watermarkPosition: 'top-left' | 'top-right' | 'bottom-left' | 'bottom-right';
  showWatermark: boolean;
  introEnabled: boolean;
  outroEnabled: boolean;

  // Trim
  trimStart: number;          // seconds
  trimEnd: number;            // seconds
}

interface ClipEditorStudioProps {
  clips: GeneratedClip[];
  jobId: string;
  onClose: () => void;
  onReRender?: (state: EditorState, clipIndex: number) => void;
}

// ── Creator Templates ──────────────────────────────

interface CreatorTemplate {
  id: string;
  name: string;
  creator: string;
  description: string;
  preset: SubtitleVisualPreset;
  animation: SubtitleAnimationStyle;
  fontSize: SubtitleFontSize;
  fontFamily: SubtitleFontFamily;
  glowStyle: SubtitleGlowStyle;
  primaryColor: string;
  highlightColor: string;
  position: SubtitlePosition;
  showEmojis: boolean;
  zoomStyle: 'subtle' | 'dramatic' | 'punch' | 'breathing' | 'none';
  colorGrade: 'none' | 'warm' | 'cool' | 'vibrant' | 'cinematic' | 'vintage';
  speedRamp: boolean;
  speedRampType: 'slowmo' | 'speedup' | 'punch' | 'none';
  badge: string;
  badgeColor: string;
}

const CREATOR_TEMPLATES: CreatorTemplate[] = [
  {
    id: 'hormozi',
    name: 'Hormozi Style',
    creator: 'Alex Hormozi',
    description: 'Bold yellow text, word-by-word pop, punchy zoom',
    preset: 'hormozi',
    animation: 'word-by-word',
    fontSize: 'large',
    fontFamily: 'display',
    glowStyle: 'intense',
    primaryColor: '#FFFFFF',
    highlightColor: '#FFD700',
    position: 'center',
    showEmojis: true,
    zoomStyle: 'punch',
    colorGrade: 'vibrant',
    speedRamp: true,
    speedRampType: 'punch',
    badge: '🔥 HOT',
    badgeColor: 'text-orange-400',
  },
  {
    id: 'mrbeast',
    name: 'MrBeast Style',
    creator: 'Jimmy Donaldson',
    description: 'Huge text, explosive animations, extreme energy',
    preset: 'mrbeast',
    animation: 'bounce-zoom',
    fontSize: 'huge',
    fontFamily: 'display',
    glowStyle: 'intense',
    primaryColor: '#FFFFFF',
    highlightColor: '#00FF00',
    position: 'center',
    showEmojis: true,
    zoomStyle: 'dramatic',
    colorGrade: 'vibrant',
    speedRamp: true,
    speedRampType: 'punch',
    badge: '💥 EXPLOSIVE',
    badgeColor: 'text-red-400',
  },
  {
    id: 'ali-abdaal',
    name: 'Ali Abdaal',
    creator: 'Ali Abdaal',
    description: 'Clean, minimal, professional — calm productivity',
    preset: 'ali-abdaal',
    animation: 'line-by-line',
    fontSize: 'normal',
    fontFamily: 'sans',
    glowStyle: 'outline-clean',
    primaryColor: '#FFFFFF',
    highlightColor: '#3B82F6',
    position: 'bottom',
    showEmojis: false,
    zoomStyle: 'subtle',
    colorGrade: 'cool',
    speedRamp: false,
    speedRampType: 'none',
    badge: '📚 CLEAN',
    badgeColor: 'text-blue-400',
  },
  {
    id: 'iman-gadzhi',
    name: 'Iman Gadzhi',
    creator: 'Iman Gadzhi',
    description: 'Dark aesthetic, gold accents, luxury feel',
    preset: 'iman-gadzhi',
    animation: 'kinetic-slide',
    fontSize: 'large',
    fontFamily: 'serif',
    glowStyle: 'subtle',
    primaryColor: '#F5F5F5',
    highlightColor: '#FFD700',
    position: 'center',
    showEmojis: false,
    zoomStyle: 'breathing',
    colorGrade: 'cinematic',
    speedRamp: false,
    speedRampType: 'none',
    badge: '👑 LUXURY',
    badgeColor: 'text-amber-400',
  },
  {
    id: 'gamer-comic',
    name: 'Gamer Comic',
    creator: 'Gaming Community',
    description: 'Comic book style, glitch effects, high energy',
    preset: 'gamer-comic',
    animation: 'typewriter-glitch',
    fontSize: 'large',
    fontFamily: 'display',
    glowStyle: 'intense',
    primaryColor: '#00FFFF',
    highlightColor: '#FF00FF',
    position: 'center',
    showEmojis: true,
    zoomStyle: 'dramatic',
    colorGrade: 'vibrant',
    speedRamp: true,
    speedRampType: 'speedup',
    badge: '🎮 GAMER',
    badgeColor: 'text-cyan-400',
  },
  {
    id: 'neon-cyberpunk',
    name: 'Neon Cyberpunk',
    creator: 'Cyberpunk Aesthetic',
    description: 'Futuristic neon, glitch transitions, dark mode',
    preset: 'neon-cyberpunk',
    animation: 'pulse-glow',
    fontSize: 'large',
    fontFamily: 'mono',
    glowStyle: 'intense',
    primaryColor: '#00FFFF',
    highlightColor: '#FF00FF',
    position: 'center',
    showEmojis: false,
    zoomStyle: 'breathing',
    colorGrade: 'cool',
    speedRamp: false,
    speedRampType: 'none',
    badge: '🌃 NEON',
    badgeColor: 'text-fuchsia-400',
  },
  {
    id: 'anime-impact',
    name: 'Anime Impact',
    creator: 'Anime Community',
    description: 'Explosive text, impact frames, dramatic pauses',
    preset: 'anime-impact',
    animation: 'flip-rotate',
    fontSize: 'huge',
    fontFamily: 'display',
    glowStyle: 'intense',
    primaryColor: '#FFFFFF',
    highlightColor: '#FF4444',
    position: 'center',
    showEmojis: true,
    zoomStyle: 'punch',
    colorGrade: 'vibrant',
    speedRamp: true,
    speedRampType: 'slowmo',
    badge: '⚔️ ANIME',
    badgeColor: 'text-red-400',
  },
  {
    id: 'minimal-aesthetic',
    name: 'Minimal Aesthetic',
    creator: 'Clean Design',
    description: 'Minimal text, subtle animations, elegant spacing',
    preset: 'minimal-aesthetic',
    animation: 'fade-drift',
    fontSize: 'compact',
    fontFamily: 'sans',
    glowStyle: 'outline-clean',
    primaryColor: '#FFFFFF',
    highlightColor: '#E5E5E5',
    position: 'bottom',
    showEmojis: false,
    zoomStyle: 'none',
    colorGrade: 'none',
    speedRamp: false,
    speedRampType: 'none',
    badge: '✨ MINIMAL',
    badgeColor: 'text-stone-300',
  },
  {
    id: 'podcast-pro',
    name: 'Podcast Pro',
    creator: 'Podcast Clips',
    description: 'Speaker labels, clean captions, professional cut',
    preset: 'hormozi',
    animation: 'word-by-word',
    fontSize: 'normal',
    fontFamily: 'sans',
    glowStyle: 'outline-clean',
    primaryColor: '#FFFFFF',
    highlightColor: '#22D3EE',
    position: 'bottom',
    showEmojis: false,
    zoomStyle: 'subtle',
    colorGrade: 'warm',
    speedRamp: false,
    speedRampType: 'none',
    badge: '🎙️ PODCAST',
    badgeColor: 'text-cyan-400',
  },
  {
    id: 'viral-tiktok',
    name: 'Viral TikTok',
    creator: 'TikTok Trends',
    description: 'Fast cuts, trending style, emoji-heavy captions',
    preset: 'hormozi',
    animation: 'word-by-word',
    fontSize: 'large',
    fontFamily: 'sans',
    glowStyle: 'intense',
    primaryColor: '#FFFFFF',
    highlightColor: '#00F5FF',
    position: 'center',
    showEmojis: true,
    zoomStyle: 'punch',
    colorGrade: 'vibrant',
    speedRamp: true,
    speedRampType: 'punch',
    badge: '📱 VIRAL',
    badgeColor: 'text-pink-400',
  },
  {
    id: 'cinematic-story',
    name: 'Cinematic Story',
    creator: 'Filmmaker Style',
    description: 'Cinematic bars, slow zoom, dramatic captions',
    preset: 'minimal-aesthetic',
    animation: 'fade-drift',
    fontSize: 'normal',
    fontFamily: 'serif',
    glowStyle: 'subtle',
    primaryColor: '#F0F0F0',
    highlightColor: '#D4AF37',
    position: 'bottom',
    showEmojis: false,
    zoomStyle: 'breathing',
    colorGrade: 'cinematic',
    speedRamp: true,
    speedRampType: 'slowmo',
    badge: '🎬 CINEMA',
    badgeColor: 'text-amber-400',
  },
  {
    id: 'news-viral',
    name: 'News Viral',
    creator: 'News Clip Style',
    description: 'Breaking news ticker, bold headlines, urgent feel',
    preset: 'hormozi',
    animation: 'bounce-zoom',
    fontSize: 'large',
    fontFamily: 'display',
    glowStyle: 'intense',
    primaryColor: '#FFFFFF',
    highlightColor: '#FF0000',
    position: 'top',
    showEmojis: false,
    zoomStyle: 'none',
    colorGrade: 'cool',
    speedRamp: false,
    speedRampType: 'none',
    badge: '📢 NEWS',
    badgeColor: 'text-red-400',
  },
];

// ── Color Swatches ─────────────────────────────────

const COLOR_SWATCHES = [
  { name: 'White', value: '#FFFFFF' },
  { name: 'Yellow', value: '#FFD700' },
  { name: 'Gold', value: '#D4AF37' },
  { name: 'Cyan', value: '#22D3EE' },
  { name: 'Green', value: '#00FF00' },
  { name: 'Red', value: '#FF4444' },
  { name: 'Magenta', value: '#FF00FF' },
  { name: 'Blue', value: '#3B82F6' },
  { name: 'Orange', value: '#FF8800' },
  { name: 'Purple', value: '#A855F7' },
  { name: 'Pink', value: '#FF00AA' },
  { name: 'Mint', value: '#00FFAA' },
];

// ── Default State ──────────────────────────────────

const DEFAULT_EDITOR_STATE: EditorState = {
  captionStyle: 'hormozi',
  animation: 'word-by-word',
  fontSize: 'large',
  fontFamily: 'display',
  position: 'center',
  glowStyle: 'intense',
  primaryColor: '#FFFFFF',
  highlightColor: '#FFD700',
  showEmojis: true,
  highlightEmphasis: true,
  progressbar: true,
  zoomLevel: 1.0,
  zoomStyle: 'subtle',
  colorGrade: 'none',
  speedRamp: false,
  speedRampType: 'none',
  aspectRatio: '9:16',
  autoReframe: true,
  faceTracking: true,
  bgmVolume: 30,
  voiceVolume: 100,
  normalizeAudio: true,
  bassBoost: false,
  sfxEnabled: true,
  watermarkText: '',
  watermarkPosition: 'bottom-right',
  showWatermark: false,
  introEnabled: false,
  outroEnabled: false,
  trimStart: 0,
  trimEnd: 45,
};

// ── Editor Tab Definitions ─────────────────────────

const EDITOR_TABS: { id: EditorTab; label: string; icon: typeof Type }[] = [
  { id: 'captions', label: 'Captions', icon: Type },
  { id: 'templates', label: 'Templates', icon: Sparkles },
  { id: 'effects', label: 'Effects', icon: Wand2 },
  { id: 'trim', label: 'Trim & Cut', icon: Scissors },
  { id: 'audio', label: 'Audio', icon: Volume2 },
  { id: 'layout', label: 'Layout', icon: Layout },
  { id: 'branding', label: 'Branding', icon: Palette },
  { id: 'export', label: 'Export', icon: Download },
];

// ── Main Component ─────────────────────────────────

export const ClipEditorStudio: React.FC<ClipEditorStudioProps> = ({
  clips,
  jobId,
  onClose,
  onReRender,
}) => {
  const [activeTab, setActiveTab] = useState<EditorTab>('templates');
  const [selectedClipIndex, setSelectedClipIndex] = useState(0);
  const [editorState, setEditorState] = useState<EditorState>(DEFAULT_EDITOR_STATE);
  const [isPlaying, setIsPlaying] = useState(false);
  const [currentTime, setCurrentTime] = useState(0);
  const [isReRendering, setIsReRendering] = useState(false);
  const [hasChanges, setHasChanges] = useState(false);
  const [showClipStrip, setShowClipStrip] = useState(true);
  const [renderResult, setRenderResult] = useState<{ success: boolean; message: string; changes?: string[] } | null>(null);
  const videoRef = useRef<HTMLVideoElement>(null);

  const selectedClip = clips[selectedClipIndex];

  // Update state helper
  const update = useCallback(<K extends keyof EditorState>(key: K, value: EditorState[K]) => {
    setEditorState(prev => ({ ...prev, [key]: value }));
    setHasChanges(true);
    sound.playClick();
  }, []);

  // Apply a creator template
  const applyTemplate = useCallback((template: CreatorTemplate) => {
    setEditorState(prev => ({
      ...prev,
      captionStyle: template.preset,
      animation: template.animation,
      fontSize: template.fontSize,
      fontFamily: template.fontFamily,
      glowStyle: template.glowStyle,
      primaryColor: template.primaryColor,
      highlightColor: template.highlightColor,
      position: template.position,
      showEmojis: template.showEmojis,
      zoomStyle: template.zoomStyle,
      colorGrade: template.colorGrade,
      speedRamp: template.speedRamp,
      speedRampType: template.speedRampType,
    }));
    setHasChanges(true);
    sound.playSuccess();
  }, []);

  // Sync subtitle store with editor state
  useEffect(() => {
    subtitleStore.update({
      animationStyle: editorState.animation,
      visualPreset: editorState.captionStyle,
      position: editorState.position,
      fontSize: editorState.fontSize,
      fontFamily: editorState.fontFamily,
      glowStyle: editorState.glowStyle,
      highlightColor: editorState.highlightColor,
      showEmojis: editorState.showEmojis,
      name: `editor-${editorState.captionStyle}`,
    });
  }, [editorState]);

  // Video controls
  const togglePlay = () => {
    if (videoRef.current) {
      if (isPlaying) {
        videoRef.current.pause();
      } else {
        videoRef.current.play();
      }
      setIsPlaying(!isPlaying);
    }
  };

  const skipTime = (delta: number) => {
    if (videoRef.current) {
      videoRef.current.currentTime = Math.max(0, Math.min(
        videoRef.current.duration || 45,
        videoRef.current.currentTime + delta
      ));
    }
  };

  // Mock subtitle line for preview
  const previewLine: SubtitleScriptLine = {
    lineText: selectedClip?.subtitleSnippet || 'Preview caption text',
    words: (selectedClip?.subtitleSnippet || 'Preview caption text').split(' ').map((w, i) => ({
      text: w,
      highlight: editorState.highlightEmphasis && i % 3 === 0,
      emoji: editorState.showEmojis && i === 1 ? '⚡' : undefined,
      colorType: (i % 3 === 0 ? 'cyan' : 'normal') as any,
    })),
    hookScore: selectedClip?.viralScore || 75,
  };

  // Re-render handler
  const handleReRender = async () => {
    setIsReRendering(true);
    sound.playClick();

    // Call custom handler if provided (for testing)
    if (onReRender) {
      onReRender(editorState, selectedClipIndex);
      setHasChanges(false);
      sound.playSuccess();
      setIsReRendering(false);
      return;
    }

    // Call API to re-render with all personalization settings
    try {
      const result = await nexuxApi.rerenderClip(jobId, selectedClipIndex, {
        subtitle_style: editorState.captionStyle,
        animation: editorState.animation,
        font_size: editorState.fontSize,
        font_family: editorState.fontFamily,
        position: editorState.position,
        glow_style: editorState.glowStyle,
        primary_color: editorState.primaryColor,
        highlight_color: editorState.highlightColor,
        show_emojis: editorState.showEmojis,
        zoom_style: editorState.zoomStyle,
        zoom_level: editorState.zoomLevel,
        color_grade: editorState.colorGrade,
        speed_ramp: editorState.speedRamp,
        speed_ramp_type: editorState.speedRampType,
        aspect_ratio: editorState.aspectRatio,
        auto_reframe: editorState.autoReframe,
        face_tracking: editorState.faceTracking,
        bgm_volume: editorState.bgmVolume,
        voice_volume: editorState.voiceVolume,
        normalize_audio: editorState.normalizeAudio,
        bass_boost: editorState.bassBoost,
        sfx_enabled: editorState.sfxEnabled,
        watermark_text: editorState.watermarkText,
        watermark_position: editorState.watermarkPosition,
        show_watermark: editorState.showWatermark,
        intro_enabled: editorState.introEnabled,
        outro_enabled: editorState.outroEnabled,
        trim_start: editorState.trimStart,
        trim_end: editorState.trimEnd,
      });
      setRenderResult({ success: true, message: 'Re-render complete!', changes: (result as any).changes_applied });
      setHasChanges(false);
      sound.playSuccess();
    } catch (e) {
      console.error('Re-render failed:', e);
      setRenderResult({ success: false, message: 'Re-render failed. Check server logs.' });
    }

    setIsReRendering(false);
  };

  // Aspect ratio dimensions
  const aspectDims: Record<AspectRatio, { w: number; h: number }> = {
    '9:16': { w: 9, h: 16 },
    '1:1': { w: 1, h: 1 },
    '4:5': { w: 4, h: 5 },
    '16:9': { w: 16, h: 9 },
  };

  const currentAspect = aspectDims[editorState.aspectRatio];

  return (
    <motion.div
      initial={{ opacity: 0, scale: 0.98 }}
      animate={{ opacity: 1, scale: 1 }}
      exit={{ opacity: 0, scale: 0.98 }}
      transition={{ duration: 0.3, ease: 'easeOut' }}
      className="fixed inset-0 z-50 bg-black/95 backdrop-blur-2xl flex flex-col overflow-hidden"
    >
      {/* ═══════════════════════════════════════════════════
          TOP BAR — Close, Title, Re-render Button
         ═══════════════════════════════════════════════════ */}
      <div className="flex items-center justify-between px-4 sm:px-6 py-3 border-b border-white/10 bg-black/60 flex-shrink-0">
        {/* Left: Close + Title */}
        <div className="flex items-center gap-3">
          <button
            onClick={() => { sound.playClick(); onClose(); }}
            onMouseEnter={() => sound.playHover()}
            className="flex items-center gap-2 px-3 py-2 rounded-xl bg-white/5 hover:bg-white/10 text-stone-300 hover:text-white border border-white/10 text-xs font-mono transition-colors"
          >
            <ArrowLeft className="w-4 h-4" />
            <span className="hidden sm:inline">Back to Results</span>
          </button>
          <div className="hidden md:flex items-center gap-2 ml-2">
            <Wand2 className="w-4 h-4 text-cyan-400" />
            <span className="font-display font-bold text-white text-sm tracking-wide">
              Clip Editor Studio
            </span>
            {hasChanges && (
              <span className="px-2 py-0.5 rounded-full bg-amber-500/20 border border-amber-500/40 text-amber-300 text-[10px] font-mono">
                UNSAVED CHANGES
              </span>
            )}
          </div>
        </div>

        {/* Right: Actions */}
        <div className="flex items-center gap-2">
          <button
            onClick={() => { sound.playClick(); setShowClipStrip(!showClipStrip); }}
            className="hidden sm:flex items-center gap-2 px-3 py-2 rounded-xl bg-white/5 hover:bg-white/10 text-stone-400 hover:text-white border border-white/10 text-xs font-mono transition-colors"
          >
            <Film className="w-3.5 h-3.5" />
            <span>Clips</span>
          </button>
          <button
            onClick={() => { sound.playClick(); setEditorState(DEFAULT_EDITOR_STATE); setHasChanges(false); }}
            onMouseEnter={() => sound.playHover()}
            className="flex items-center gap-2 px-3 py-2 rounded-xl bg-white/5 hover:bg-white/10 text-stone-400 hover:text-white border border-white/10 text-xs font-mono transition-colors"
          >
            <RotateCcw className="w-3.5 h-3.5" />
            <span className="hidden sm:inline">Reset</span>
          </button>
          <button
            onClick={handleReRender}
            disabled={isReRendering}
            onMouseEnter={() => sound.playHover()}
            className="flex items-center gap-2 px-4 py-2 rounded-xl bg-gradient-to-r from-cyan-500 to-blue-500 hover:from-cyan-400 hover:to-blue-400 text-white text-xs font-mono font-bold transition-colors disabled:opacity-50 disabled:cursor-wait shadow-[0_0_20px_rgba(34,211,238,0.3)]"
          >
            {isReRendering ? (
              <>
                <Loader2 className="w-4 h-4 animate-spin" />
                <span>Re-rendering...</span>
              </>
            ) : (
              <>
                <Sparkles className="w-4 h-4" />
                <span>Apply & Re-render</span>
              </>
            )}
          </button>
        </div>
      </div>

      {/* ═══════════════════════════════════════════════════
          MAIN BODY — 3-column layout
          Left: Tab Sidebar | Center: Video Preview | Right: Controls Panel
         ═══════════════════════════════════════════════════ */}
      <div className="flex-1 flex overflow-hidden min-h-0">
        {/* ── LEFT: Tab Navigation ── */}
        <div className="w-14 sm:w-20 flex-shrink-0 border-r border-white/10 bg-black/40 flex flex-col py-4 gap-1">
          {EDITOR_TABS.map((tab) => {
            const Icon = tab.icon;
            const isActive = activeTab === tab.id;
            return (
              <button
                key={tab.id}
                onClick={() => { sound.playClick(); setActiveTab(tab.id); }}
                onMouseEnter={() => sound.playHover()}
                className={`flex flex-col items-center gap-1.5 py-3 mx-2 rounded-xl transition-all ${
                  isActive
                    ? 'bg-cyan-500/20 text-cyan-300 border border-cyan-500/40 shadow-[0_0_15px_rgba(34,211,238,0.2)]'
                    : 'text-stone-500 hover:text-stone-300 hover:bg-white/5 border border-transparent'
                }`}
              >
                <Icon className="w-5 h-5" />
                <span className="text-[9px] font-mono font-medium hidden sm:block">
                  {tab.label}
                </span>
              </button>
            );
          })}
        </div>

        {/* ── CENTER: Video Preview Canvas ── */}
        <div className="flex-1 flex flex-col items-center justify-center min-w-0 relative bg-gradient-to-b from-black/80 to-stone-950/80 p-4">
          {/* Video Preview Container with aspect ratio */}
          <div
            className="relative bg-black rounded-2xl overflow-hidden border border-white/10 shadow-2xl"
            style={{
              aspectRatio: `${currentAspect.w} / ${currentAspect.h}`,
              maxHeight: '100%',
              maxWidth: '100%',
              width: editorState.aspectRatio === '16:9' ? '100%' : 'auto',
              height: editorState.aspectRatio === '16:9' ? 'auto' : '100%',
            }}
          >
            {/* Actual video */}
            {selectedClip?.videoUrl && (
              <video
                ref={videoRef}
                src={selectedClip.videoUrl}
                className="w-full h-full object-contain"
                onTimeUpdate={(e) => setCurrentTime(e.currentTarget.currentTime)}
                onEnded={() => setIsPlaying(false)}
                loop
                muted
                playsInline
              />
            )}

            {/* Color grade overlay */}
            {editorState.colorGrade !== 'none' && (
              <div
                className="absolute inset-0 pointer-events-none mix-blend-overlay"
                style={{
                  background:
                    editorState.colorGrade === 'warm' ? 'linear-gradient(135deg, rgba(255,140,0,0.15), rgba(255,200,0,0.08))' :
                    editorState.colorGrade === 'cool' ? 'linear-gradient(135deg, rgba(0,100,255,0.12), rgba(0,200,255,0.06))' :
                    editorState.colorGrade === 'vibrant' ? 'saturate(1.5) contrast(1.1)' :
                    editorState.colorGrade === 'cinematic' ? 'linear-gradient(180deg, rgba(0,0,0,0.2), transparent 30%, transparent 70%, rgba(0,0,0,0.2))' :
                    editorState.colorGrade === 'vintage' ? 'sepia(0.3) contrast(1.1)' : 'none',
                  filter:
                    editorState.colorGrade === 'vibrant' ? 'saturate(1.4)' :
                    editorState.colorGrade === 'vintage' ? 'sepia(0.3)' : 'none',
                }}
              />
            )}

            {/* Zoom indicator */}
            {editorState.zoomLevel > 1.0 && (
              <div
                className="absolute inset-0 pointer-events-none"
                style={{ transform: `scale(${editorState.zoomLevel})`, transformOrigin: 'center' }}
              >
                {/* This would apply the zoom in real implementation */}
              </div>
            )}

            {/* Cinematic bars (for cinematic color grade) */}
            {editorState.colorGrade === 'cinematic' && (
              <>
                <div className="absolute top-0 left-0 right-0 h-[8%] bg-black z-10 pointer-events-none" />
                <div className="absolute bottom-0 left-0 right-0 h-[8%] bg-black z-10 pointer-events-none" />
              </>
            )}

            {/* Live subtitle preview overlay */}
            <div className={`absolute left-0 right-0 z-20 pointer-events-none ${
              editorState.position === 'top' ? 'top-[10%]' :
              editorState.position === 'center' ? 'top-1/2 -translate-y-1/2' :
              'bottom-[12%]'
            }`}>
              <LiveSubtitleRenderer
                line={previewLine}
                wordIndex={Math.floor(currentTime * 3) % previewLine.words.length}
                config={subtitleStore.get()}
                isActive={true}
              />
            </div>

            {/* Progress bar */}
            {editorState.progressbar && (
              <div className="absolute bottom-0 left-0 right-0 h-1 bg-white/10 z-20">
                <div
                  className="h-full bg-cyan-400 transition-all"
                  style={{
                    width: `${videoRef.current ? (currentTime / (videoRef.current.duration || 45)) * 100 : 0}%`,
                  }}
                />
              </div>
            )}

            {/* Watermark */}
            {editorState.showWatermark && editorState.watermarkText && (
              <div className={`absolute z-20 pointer-events-none ${
                editorState.watermarkPosition === 'top-left' ? 'top-3 left-3' :
                editorState.watermarkPosition === 'top-right' ? 'top-3 right-3' :
                editorState.watermarkPosition === 'bottom-left' ? 'bottom-3 left-3' :
                'bottom-3 right-3'
              }`}>
                <span className="text-white/50 text-xs font-mono font-semibold drop-shadow-lg">
                  {editorState.watermarkText}
                </span>
              </div>
            )}

            {/* No video placeholder */}
            {!selectedClip?.videoUrl && (
              <div className="absolute inset-0 flex flex-col items-center justify-center text-stone-500">
                <Film className="w-12 h-12 mb-3 opacity-40" />
                <span className="text-sm font-mono">No video preview available</span>
              </div>
            )}
          </div>

          {/* Video controls */}
          <div className="mt-4 flex items-center gap-3 px-4 py-2 rounded-2xl bg-black/60 border border-white/10">
            <button onClick={() => skipTime(-5)} className="text-stone-400 hover:text-white transition-colors">
              <SkipBack className="w-4 h-4" />
            </button>
            <button
              onClick={togglePlay}
              className="w-10 h-10 rounded-full bg-cyan-500/20 border border-cyan-500/40 flex items-center justify-center text-cyan-300 hover:bg-cyan-500/30 transition-colors"
            >
              {isPlaying ? <Pause className="w-4 h-4" /> : <Play className="w-4 h-4 ml-0.5" />}
            </button>
            <button onClick={() => skipTime(5)} className="text-stone-400 hover:text-white transition-colors">
              <SkipForward className="w-4 h-4" />
            </button>
            <div className="text-stone-400 text-xs font-mono ml-2">
              {Math.floor(currentTime)}s / {selectedClip?.duration || '0:45'}
            </div>
            <div className="ml-auto text-stone-500 text-[10px] font-mono hidden sm:block">
              {editorState.aspectRatio} • {editorState.captionStyle} • {editorState.animation}
            </div>
          </div>
        </div>

        {/* ── RIGHT: Control Panel ── */}
        <div className="w-[280px] sm:w-[340px] flex-shrink-0 border-l border-white/10 bg-black/60 overflow-y-auto">
          <AnimatePresence mode="wait">
            {/* ━━━━━━━━ CAPTIONS TAB ━━━━━━━━ */}
            {activeTab === 'captions' && (
              <motion.div key="captions" initial={{ opacity: 0, x: 20 }} animate={{ opacity: 1, x: 0 }} exit={{ opacity: 0, x: -20 }} className="p-4 space-y-5">
                <PanelHeader icon={Type} title="Caption Studio" subtitle="Style, font, color, animation" />

                {/* Caption Style Preset */}
                <ControlSection label="Visual Preset">
                  <div className="grid grid-cols-2 gap-2">
                    {(['hormozi', 'mrbeast', 'minimal-aesthetic', 'gamer-comic', 'neon-cyberpunk', 'ali-abdaal', 'iman-gadzhi', 'anime-impact'] as SubtitleVisualPreset[]).map(p => (
                      <button
                        key={p}
                        onClick={() => update('captionStyle', p)}
                        className={`px-3 py-2 rounded-lg text-xs font-mono border transition-all ${
                          editorState.captionStyle === p
                            ? 'bg-cyan-500/20 text-cyan-300 border-cyan-500/40'
                            : 'bg-white/5 text-stone-400 border-white/10 hover:bg-white/10'
                        }`}
                      >
                        {p.replace(/-/g, ' ')}
                      </button>
                    ))}
                  </div>
                </ControlSection>

                {/* Animation Style */}
                <ControlSection label="Animation">
                  <div className="grid grid-cols-2 gap-2">
                    {(['word-by-word', 'line-by-line', 'bounce-zoom', 'typewriter-glitch', 'kinetic-slide', 'pulse-glow', 'flip-rotate', 'fade-drift'] as SubtitleAnimationStyle[]).map(a => (
                      <button
                        key={a}
                        onClick={() => update('animation', a)}
                        className={`px-3 py-2 rounded-lg text-xs font-mono border transition-all ${
                          editorState.animation === a
                            ? 'bg-cyan-500/20 text-cyan-300 border-cyan-500/40'
                            : 'bg-white/5 text-stone-400 border-white/10 hover:bg-white/10'
                        }`}
                      >
                        {a.replace(/-/g, ' ')}
                      </button>
                    ))}
                  </div>
                </ControlSection>

                {/* Position */}
                <ControlSection label="Position">
                  <div className="grid grid-cols-3 gap-2">
                    {(['top', 'center', 'bottom'] as SubtitlePosition[]).map(p => (
                      <button
                        key={p}
                        onClick={() => update('position', p)}
                        className={`px-3 py-2 rounded-lg text-xs font-mono border transition-all ${
                          editorState.position === p
                            ? 'bg-cyan-500/20 text-cyan-300 border-cyan-500/40'
                            : 'bg-white/5 text-stone-400 border-white/10 hover:bg-white/10'
                        }`}
                      >
                        {p}
                      </button>
                    ))}
                  </div>
                </ControlSection>

                {/* Font */}
                <ControlSection label="Font Family">
                  <div className="grid grid-cols-2 gap-2">
                    {(['sans', 'display', 'mono', 'serif'] as SubtitleFontFamily[]).map(f => (
                      <button
                        key={f}
                        onClick={() => update('fontFamily', f)}
                        className={`px-3 py-2 rounded-lg text-xs font-mono border transition-all ${
                          editorState.fontFamily === f
                            ? 'bg-cyan-500/20 text-cyan-300 border-cyan-500/40'
                            : 'bg-white/5 text-stone-400 border-white/10 hover:bg-white/10'
                        }`}
                      >
                        {f}
                      </button>
                    ))}
                  </div>
                </ControlSection>

                {/* Font Size */}
                <ControlSection label="Font Size">
                  <div className="grid grid-cols-4 gap-1.5">
                    {(['compact', 'normal', 'large', 'huge'] as SubtitleFontSize[]).map(s => (
                      <button
                        key={s}
                        onClick={() => update('fontSize', s)}
                        className={`px-2 py-2 rounded-lg text-[10px] font-mono border transition-all ${
                          editorState.fontSize === s
                            ? 'bg-cyan-500/20 text-cyan-300 border-cyan-500/40'
                            : 'bg-white/5 text-stone-400 border-white/10 hover:bg-white/10'
                        }`}
                      >
                        {s}
                      </button>
                    ))}
                  </div>
                </ControlSection>

                {/* Primary Color */}
                <ControlSection label="Primary Color">
                  <ColorSwatches value={editorState.primaryColor} onChange={(v) => update('primaryColor', v)} />
                </ControlSection>

                {/* Highlight Color */}
                <ControlSection label="Highlight Color">
                  <ColorSwatches value={editorState.highlightColor} onChange={(v) => update('highlightColor', v)} />
                </ControlSection>

                {/* Glow Style */}
                <ControlSection label="Glow Style">
                  <div className="grid grid-cols-3 gap-2">
                    {(['subtle', 'intense', 'outline-clean'] as SubtitleGlowStyle[]).map(g => (
                      <button
                        key={g}
                        onClick={() => update('glowStyle', g)}
                        className={`px-3 py-2 rounded-lg text-xs font-mono border transition-all ${
                          editorState.glowStyle === g
                            ? 'bg-cyan-500/20 text-cyan-300 border-cyan-500/40'
                            : 'bg-white/5 text-stone-400 border-white/10 hover:bg-white/10'
                        }`}
                      >
                        {g.replace(/-/g, ' ')}
                      </button>
                    ))}
                  </div>
                </ControlSection>

                {/* Toggles */}
                <div className="space-y-2">
                  <ToggleRow label="Emojis" value={editorState.showEmojis} onChange={(v) => update('showEmojis', v)} />
                  <ToggleRow label="Emphasis Highlight" value={editorState.highlightEmphasis} onChange={(v) => update('highlightEmphasis', v)} />
                  <ToggleRow label="Progress Bar" value={editorState.progressbar} onChange={(v) => update('progressbar', v)} />
                </div>
              </motion.div>
            )}

            {/* ━━━━━━━━ TEMPLATES TAB ━━━━━━━━ */}
            {activeTab === 'templates' && (
              <motion.div key="templates" initial={{ opacity: 0, x: 20 }} animate={{ opacity: 1, x: 0 }} exit={{ opacity: 0, x: -20 }} className="p-4 space-y-4">
                <PanelHeader icon={Sparkles} title="Creator Templates" subtitle="One-click famous styles" />

                <div className="space-y-3">
                  {CREATOR_TEMPLATES.map(tpl => (
                    <button
                      key={tpl.id}
                      onClick={() => applyTemplate(tpl)}
                      onMouseEnter={() => sound.playHover()}
                      className="w-full text-left p-3 rounded-xl bg-white/5 hover:bg-white/10 border border-white/10 hover:border-cyan-500/30 transition-all group"
                    >
                      <div className="flex items-center justify-between mb-1">
                        <span className="font-display font-bold text-white text-sm">{tpl.name}</span>
                        <span className={`text-[10px] font-mono font-bold ${tpl.badgeColor}`}>{tpl.badge}</span>
                      </div>
                      <p className="text-xs text-stone-400 font-mono">{tpl.description}</p>
                      <div className="mt-2 flex items-center gap-2">
                        <div className="w-3 h-3 rounded-full border border-white/20" style={{ background: tpl.primaryColor }} />
                        <div className="w-3 h-3 rounded-full border border-white/20" style={{ background: tpl.highlightColor }} />
                        <span className="text-[10px] text-stone-500 font-mono ml-1">{tpl.animation.replace(/-/g, ' ')}</span>
                        <ChevronRight className="w-3 h-3 text-stone-500 ml-auto group-hover:text-cyan-400 transition-colors" />
                      </div>
                    </button>
                  ))}
                </div>
              </motion.div>
            )}

            {/* ━━━━━━━━ EFFECTS TAB ━━━━━━━━ */}
            {activeTab === 'effects' && (
              <motion.div key="effects" initial={{ opacity: 0, x: 20 }} animate={{ opacity: 1, x: 0 }} exit={{ opacity: 0, x: -20 }} className="p-4 space-y-5">
                <PanelHeader icon={Wand2} title="Visual Effects" subtitle="Zoom, color, speed" />

                <ControlSection label="Zoom Style">
                  <div className="grid grid-cols-2 gap-2">
                    {(['none', 'subtle', 'dramatic', 'punch', 'breathing'] as const).map(z => (
                      <button
                        key={z}
                        onClick={() => update('zoomStyle', z)}
                        className={`px-3 py-2 rounded-lg text-xs font-mono border transition-all ${
                          editorState.zoomStyle === z
                            ? 'bg-cyan-500/20 text-cyan-300 border-cyan-500/40'
                            : 'bg-white/5 text-stone-400 border-white/10 hover:bg-white/10'
                        }`}
                      >
                        {z}
                      </button>
                    ))}
                  </div>
                </ControlSection>

                <ControlSection label={`Zoom Level: ${editorState.zoomLevel.toFixed(1)}x`}>
                  <input
                    type="range"
                    min={1}
                    max={3}
                    step={0.1}
                    value={editorState.zoomLevel}
                    onChange={(e) => update('zoomLevel', parseFloat(e.target.value))}
                    className="w-full accent-cyan-500"
                  />
                </ControlSection>

                <ControlSection label="Color Grade">
                  <div className="grid grid-cols-2 gap-2">
                    {(['none', 'warm', 'cool', 'vibrant', 'cinematic', 'vintage'] as const).map(c => (
                      <button
                        key={c}
                        onClick={() => update('colorGrade', c)}
                        className={`px-3 py-2 rounded-lg text-xs font-mono border transition-all ${
                          editorState.colorGrade === c
                            ? 'bg-cyan-500/20 text-cyan-300 border-cyan-500/40'
                            : 'bg-white/5 text-stone-400 border-white/10 hover:bg-white/10'
                        }`}
                      >
                        {c}
                      </button>
                    ))}
                  </div>
                </ControlSection>

                <ControlSection label="Speed Ramp">
                  <ToggleRow label="Enable Speed Ramp" value={editorState.speedRamp} onChange={(v) => update('speedRamp', v)} />
                  {editorState.speedRamp && (
                    <div className="grid grid-cols-3 gap-2 mt-2">
                      {(['slowmo', 'speedup', 'punch', 'none'] as const).map(s => (
                        <button
                          key={s}
                          onClick={() => update('speedRampType', s)}
                          className={`px-2 py-2 rounded-lg text-[10px] font-mono border transition-all ${
                            editorState.speedRampType === s
                              ? 'bg-cyan-500/20 text-cyan-300 border-cyan-500/40'
                              : 'bg-white/5 text-stone-400 border-white/10 hover:bg-white/10'
                          }`}
                        >
                          {s}
                        </button>
                      ))}
                    </div>
                  )}
                </ControlSection>
              </motion.div>
            )}

            {/* ━━━━━━━━ TRIM TAB ━━━━━━━━ */}
            {activeTab === 'trim' && (
              <motion.div key="trim" initial={{ opacity: 0, x: 20 }} animate={{ opacity: 1, x: 0 }} exit={{ opacity: 0, x: -20 }} className="p-4 space-y-5">
                <PanelHeader icon={Scissors} title="Trim & Cut" subtitle="Fine-tune clip timing" />

                <ControlSection label={`Start: ${editorState.trimStart.toFixed(1)}s`}>
                  <input
                    type="range"
                    min={0}
                    max={Math.max(0, (editorState.trimEnd - 1))}
                    step={0.1}
                    value={editorState.trimStart}
                    onChange={(e) => update('trimStart', parseFloat(e.target.value))}
                    className="w-full accent-cyan-500"
                  />
                </ControlSection>

                <ControlSection label={`End: ${editorState.trimEnd.toFixed(1)}s`}>
                  <input
                    type="range"
                    min={editorState.trimStart + 1}
                    max={120}
                    step={0.1}
                    value={editorState.trimEnd}
                    onChange={(e) => update('trimEnd', parseFloat(e.target.value))}
                    className="w-full accent-cyan-500"
                  />
                </ControlSection>

                <div className="p-3 rounded-xl bg-white/5 border border-white/10">
                  <div className="flex items-center justify-between text-xs font-mono">
                    <span className="text-stone-400">Duration:</span>
                    <span className="text-cyan-300 font-bold">
                      {(editorState.trimEnd - editorState.trimStart).toFixed(1)}s
                    </span>
                  </div>
                </div>

                <div className="space-y-2">
                  <button className="w-full flex items-center justify-center gap-2 px-3 py-2.5 rounded-xl bg-white/5 hover:bg-white/10 text-stone-300 border border-white/10 text-xs font-mono transition-colors">
                    <Scissors className="w-3.5 h-3.5" />
                    Split at Playhead
                  </button>
                  <button className="w-full flex items-center justify-center gap-2 px-3 py-2.5 rounded-xl bg-white/5 hover:bg-white/10 text-stone-300 border border-white/10 text-xs font-mono transition-colors">
                    <RotateCcw className="w-3.5 h-3.5" />
                    Reset Trim
                  </button>
                </div>
              </motion.div>
            )}

            {/* ━━━━━━━━ AUDIO TAB ━━━━━━━━ */}
            {activeTab === 'audio' && (
              <motion.div key="audio" initial={{ opacity: 0, x: 20 }} animate={{ opacity: 1, x: 0 }} exit={{ opacity: 0, x: -20 }} className="p-4 space-y-5">
                <PanelHeader icon={Volume2} title="Audio Mixer" subtitle="BGM, voice, SFX" />

                <ControlSection label={`BGM Volume: ${editorState.bgmVolume}%`}>
                  <input
                    type="range"
                    min={0}
                    max={100}
                    value={editorState.bgmVolume}
                    onChange={(e) => update('bgmVolume', parseInt(e.target.value))}
                    className="w-full accent-cyan-500"
                  />
                </ControlSection>

                <ControlSection label={`Voice Volume: ${editorState.voiceVolume}%`}>
                  <input
                    type="range"
                    min={0}
                    max={100}
                    value={editorState.voiceVolume}
                    onChange={(e) => update('voiceVolume', parseInt(e.target.value))}
                    className="w-full accent-cyan-500"
                  />
                </ControlSection>

                <div className="space-y-2">
                  <ToggleRow label="Normalize Audio" value={editorState.normalizeAudio} onChange={(v) => update('normalizeAudio', v)} />
                  <ToggleRow label="Bass Boost" value={editorState.bassBoost} onChange={(v) => update('bassBoost', v)} />
                  <ToggleRow label="Sound Effects (SFX)" value={editorState.sfxEnabled} onChange={(v) => update('sfxEnabled', v)} />
                </div>
              </motion.div>
            )}

            {/* ━━━━━━━━ LAYOUT TAB ━━━━━━━━ */}
            {activeTab === 'layout' && (
              <motion.div key="layout" initial={{ opacity: 0, x: 20 }} animate={{ opacity: 1, x: 0 }} exit={{ opacity: 0, x: -20 }} className="p-4 space-y-5">
                <PanelHeader icon={Layout} title="Layout & Aspect" subtitle="Aspect ratio, reframe" />

                <ControlSection label="Aspect Ratio">
                  <div className="grid grid-cols-2 gap-2">
                    {(['9:16', '1:1', '4:5', '16:9'] as AspectRatio[]).map(r => (
                      <button
                        key={r}
                        onClick={() => update('aspectRatio', r)}
                        className={`px-3 py-3 rounded-lg text-sm font-mono border transition-all flex flex-col items-center gap-1 ${
                          editorState.aspectRatio === r
                            ? 'bg-cyan-500/20 text-cyan-300 border-cyan-500/40'
                            : 'bg-white/5 text-stone-400 border-white/10 hover:bg-white/10'
                        }`}
                      >
                        <span className="font-bold">{r}</span>
                        <span className="text-[9px] text-stone-500">
                          {r === '9:16' ? 'TikTok/Reels' : r === '1:1' ? 'Instagram' : r === '4:5' ? 'Feed Post' : 'YouTube'}
                        </span>
                      </button>
                    ))}
                  </div>
                </ControlSection>

                <div className="space-y-2">
                  <ToggleRow label="Auto-Reframe (Face Track)" value={editorState.autoReframe} onChange={(v) => update('autoReframe', v)} />
                  <ToggleRow label="Face Tracking" value={editorState.faceTracking} onChange={(v) => update('faceTracking', v)} />
                </div>
              </motion.div>
            )}

            {/* ━━━━━━━━ BRANDING TAB ━━━━━━━━ */}
            {activeTab === 'branding' && (
              <motion.div key="branding" initial={{ opacity: 0, x: 20 }} animate={{ opacity: 1, x: 0 }} exit={{ opacity: 0, x: -20 }} className="p-4 space-y-5">
                <PanelHeader icon={Palette} title="Branding" subtitle="Watermark, intro, outro" />

                <ToggleRow label="Show Watermark" value={editorState.showWatermark} onChange={(v) => update('showWatermark', v)} />

                {editorState.showWatermark && (
                  <>
                    <ControlSection label="Watermark Text">
                      <input
                        type="text"
                        value={editorState.watermarkText}
                        onChange={(e) => update('watermarkText', e.target.value)}
                        placeholder="@yourbrand"
                        className="w-full px-3 py-2 rounded-lg bg-white/5 border border-white/10 text-white text-xs font-mono placeholder-stone-500 focus:border-cyan-500/40 focus:outline-none"
                      />
                    </ControlSection>

                    <ControlSection label="Watermark Position">
                      <div className="grid grid-cols-2 gap-2">
                        {(['top-left', 'top-right', 'bottom-left', 'bottom-right'] as const).map(p => (
                          <button
                            key={p}
                            onClick={() => update('watermarkPosition', p)}
                            className={`px-3 py-2 rounded-lg text-xs font-mono border transition-all ${
                              editorState.watermarkPosition === p
                                ? 'bg-cyan-500/20 text-cyan-300 border-cyan-500/40'
                                : 'bg-white/5 text-stone-400 border-white/10 hover:bg-white/10'
                            }`}
                          >
                            {p.replace(/-/g, ' ')}
                          </button>
                        ))}
                      </div>
                    </ControlSection>
                  </>
                )}

                <ToggleRow label="Intro Animation" value={editorState.introEnabled} onChange={(v) => update('introEnabled', v)} />
                <ToggleRow label="Outro Animation" value={editorState.outroEnabled} onChange={(v) => update('outroEnabled', v)} />
              </motion.div>
            )}

            {/* ━━━━━━━━ EXPORT TAB ━━━━━━━━ */}
            {activeTab === 'export' && (
              <motion.div key="export" initial={{ opacity: 0, x: 20 }} animate={{ opacity: 1, x: 0 }} exit={{ opacity: 0, x: -20 }} className="p-4 space-y-5">
                <PanelHeader icon={Download} title="Export & Publish" subtitle="Re-render and share" />

                {hasChanges && (
                  <div className="p-3 rounded-xl bg-amber-500/10 border border-amber-500/30 flex items-center gap-2">
                    <AlertCircle className="w-4 h-4 text-amber-400 flex-shrink-0" />
                    <span className="text-xs text-amber-300 font-mono">
                      You have unsaved changes. Re-render to apply.
                    </span>
                  </div>
                )}

                <button
                  onClick={handleReRender}
                  disabled={isReRendering}
                  className="w-full flex items-center justify-center gap-2 px-4 py-3 rounded-xl bg-gradient-to-r from-cyan-500 to-blue-500 text-white text-sm font-mono font-bold transition-colors disabled:opacity-50 shadow-[0_0_20px_rgba(34,211,238,0.3)]"
                >
                  {isReRendering ? (
                    <><Loader2 className="w-4 h-4 animate-spin" /> Re-rendering...</>
                  ) : (
                    <><Sparkles className="w-4 h-4" /> Apply & Re-render</>
                  )}
                </button>

                <div className="space-y-2">
                  <button className="w-full flex items-center justify-center gap-2 px-3 py-2.5 rounded-xl bg-white/5 hover:bg-white/10 text-stone-300 border border-white/10 text-xs font-mono transition-colors">
                    <Download className="w-3.5 h-3.5" />
                    Download Clip
                  </button>
                  <button className="w-full flex items-center justify-center gap-2 px-3 py-2.5 rounded-xl bg-white/5 hover:bg-white/10 text-stone-300 border border-white/10 text-xs font-mono transition-colors">
                    <Share2 className="w-3.5 h-3.5" />
                    Auto-Post to All Platforms
                  </button>
                  <button className="w-full flex items-center justify-center gap-2 px-3 py-2.5 rounded-xl bg-white/5 hover:bg-white/10 text-stone-300 border border-white/10 text-xs font-mono transition-colors">
                    <Copy className="w-3.5 h-3.5" />
                    Copy Share Link
                  </button>
                </div>

                <div className="p-3 rounded-xl bg-white/5 border border-white/10 space-y-1.5">
                  <div className="flex justify-between text-xs font-mono">
                    <span className="text-stone-400">Resolution:</span>
                    <span className="text-cyan-300">1080×1920</span>
                  </div>
                  <div className="flex justify-between text-xs font-mono">
                    <span className="text-stone-400">Aspect:</span>
                    <span className="text-cyan-300">{editorState.aspectRatio}</span>
                  </div>
                  <div className="flex justify-between text-xs font-mono">
                    <span className="text-stone-400">Style:</span>
                    <span className="text-cyan-300">{editorState.captionStyle}</span>
                  </div>
                  <div className="flex justify-between text-xs font-mono">
                    <span className="text-stone-400">Animation:</span>
                    <span className="text-cyan-300">{editorState.animation.replace(/-/g, ' ')}</span>
                  </div>
                  <div className="flex justify-between text-xs font-mono">
                    <span className="text-stone-400">Color Grade:</span>
                    <span className="text-cyan-300">{editorState.colorGrade}</span>
                  </div>
                </div>
              </motion.div>
            )}
          </AnimatePresence>
        </div>
      </div>

      {/* ═══════════════════════════════════════════════════
          BOTTOM: Clip Strip — horizontal scroll of all clips
         ═══════════════════════════════════════════════════ */}
      <AnimatePresence>
        {showClipStrip && clips.length > 1 && (
          <motion.div
            initial={{ height: 0, opacity: 0 }}
            animate={{ height: 'auto', opacity: 1 }}
            exit={{ height: 0, opacity: 0 }}
            className="border-t border-white/10 bg-black/60 flex-shrink-0 overflow-hidden"
          >
            <div className="flex items-center gap-3 px-4 py-3 overflow-x-auto">
              {clips.map((clip, idx) => (
                <button
                  key={clip.id}
                  onClick={() => { sound.playClick(); setSelectedClipIndex(idx); }}
                  onMouseEnter={() => sound.playHover()}
                  className={`flex-shrink-0 w-20 h-32 rounded-lg overflow-hidden border-2 transition-all relative ${
                    selectedClipIndex === idx
                      ? 'border-cyan-400 shadow-[0_0_15px_rgba(34,211,238,0.4)]'
                      : 'border-white/10 hover:border-white/30'
                  }`}
                >
                  {clip.videoUrl ? (
                    <video src={clip.videoUrl} className="w-full h-full object-cover" muted playsInline />
                  ) : (
                    <div className="w-full h-full bg-white/5 flex flex-col items-center justify-center">
                      <Film className="w-4 h-4 text-stone-500 mb-1" />
                      <span className="text-[9px] text-stone-500 font-mono">Clip {idx + 1}</span>
                    </div>
                  )}
                  <div className="absolute bottom-0 left-0 right-0 bg-gradient-to-t from-black/90 to-transparent px-1 py-1">
                    <span className="text-[8px] text-white font-mono">{clip.duration}</span>
                    <span className="ml-1 text-[8px] text-amber-400 font-mono">★{clip.viralScore}</span>
                  </div>
                  {selectedClipIndex === idx && (
                    <div className="absolute top-1 right-1 w-4 h-4 rounded-full bg-cyan-400 flex items-center justify-center">
                      <Check className="w-2.5 h-2.5 text-black" />
                    </div>
                  )}
                </button>
              ))}
            </div>
          </motion.div>
        )}
      </AnimatePresence>

      {/* V8.5: Re-render Result Toast */}
      <AnimatePresence>
        {renderResult && (
          <motion.div
            initial={{ opacity: 0, y: 20, x: '-50%' }}
            animate={{ opacity: 1, y: 0, x: '-50%' }}
            exit={{ opacity: 0, y: 20, x: '-50%' }}
            className="fixed bottom-8 left-1/2 z-[60] px-5 py-4 rounded-2xl border backdrop-blur-xl shadow-2xl max-w-md"
            style={{
              background: renderResult.success ? 'rgba(16,185,129,0.15)' : 'rgba(239,68,68,0.15)',
              borderColor: renderResult.success ? 'rgba(16,185,129,0.4)' : 'rgba(239,68,68,0.4)',
            }}
          >
            <div className="flex items-start gap-3">
              {renderResult.success ? (
                <CheckCircle2 className="w-5 h-5 text-emerald-400 flex-shrink-0 mt-0.5" />
              ) : (
                <AlertCircle className="w-5 h-5 text-red-400 flex-shrink-0 mt-0.5" />
              )}
              <div className="flex-1">
                <p className="text-sm font-mono font-bold text-white">{renderResult.message}</p>
                {renderResult.changes && renderResult.changes.length > 0 && (
                  <ul className="mt-1.5 space-y-0.5">
                    {renderResult.changes.map((c, i) => (
                      <li key={i} className="text-[11px] font-mono text-stone-300">• {c}</li>
                    ))}
                  </ul>
                )}
              </div>
              <button
                onClick={() => setRenderResult(null)}
                className="text-stone-400 hover:text-white transition-colors flex-shrink-0"
              >
                <X className="w-4 h-4" />
              </button>
            </div>
          </motion.div>
        )}
      </AnimatePresence>
    </motion.div>
  );
};

// ── Helper Components ───────────────────────────────

function PanelHeader({ icon: Icon, title, subtitle }: { icon: typeof Type; title: string; subtitle: string }) {
  return (
    <div className="flex items-center gap-3 pb-3 border-b border-white/10">
      <div className="w-9 h-9 rounded-xl bg-cyan-500/10 border border-cyan-500/20 flex items-center justify-center text-cyan-400">
        <Icon className="w-4 h-4" />
      </div>
      <div>
        <h3 className="font-display font-bold text-white text-sm">{title}</h3>
        <p className="text-[10px] text-stone-500 font-mono">{subtitle}</p>
      </div>
    </div>
  );
}

function ControlSection({ label, children }: { label: string; children: React.ReactNode }) {
  return (
    <div className="space-y-2">
      <label className="text-[11px] font-mono font-semibold text-stone-400 uppercase tracking-wider">
        {label}
      </label>
      {children}
    </div>
  );
}

function ColorSwatches({ value, onChange }: { value: string; onChange: (v: string) => void }) {
  return (
    <div className="grid grid-cols-6 gap-2">
      {COLOR_SWATCHES.map(c => (
        <button
          key={c.value}
          onClick={() => { onChange(c.value); sound.playClick(); }}
          className={`w-8 h-8 rounded-lg border-2 transition-all ${
            value === c.value ? 'border-cyan-400 scale-110' : 'border-white/20 hover:border-white/40'
          }`}
          style={{ background: c.value }}
          title={c.name}
        />
      ))}
    </div>
  );
}

function ToggleRow({ label, value, onChange }: { label: string; value: boolean; onChange: (v: boolean) => void }) {
  return (
    <button
      onClick={() => { onChange(!value); sound.playClick(); }}
      className="w-full flex items-center justify-between px-3 py-2 rounded-lg bg-white/5 hover:bg-white/10 border border-white/10 text-xs font-mono transition-colors"
    >
      <span className="text-stone-300">{label}</span>
      <div className={`w-9 h-5 rounded-full transition-colors ${value ? 'bg-cyan-500' : 'bg-white/10'}`}>
        <div className={`w-4 h-4 rounded-full bg-white transition-transform ${value ? 'translate-x-4' : 'translate-x-0.5'} mt-0.5`} />
      </div>
    </button>
  );
}
