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
  Wand2, Film, Zap, Play, Pause, SkipBack, SkipForward, Activity,
  // Controls
  Sliders, Eye, Copy, ChevronRight, ChevronLeft,
  Bold, Italic, AlignLeft, AlignCenter, AlignRight,
  Maximize2, Minimize2, RotateCw, Crop,
  // Status
  Loader2, AlertCircle, CheckCircle2,
  // History & Overlays
  Undo, Redo, Plus, Trash2, Move, Lock, Unlock, EyeOff,
} from 'lucide-react';
import { InsightsPanel } from './InsightsPanel';
import { TitleStudio } from './TitleStudio';
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
import { editorApi } from '../api/editorApi';

// ── Types ──────────────────────────────────────────

type EditorTab =
  | 'captions'    // Subtitle/caption editing
  | 'effects'     // Visual effects (zoom, color, speed)
  | 'templates'   // Creator template gallery
  | 'trim'        // Trim & cut
  | 'audio'       // Audio mixing
  | 'layout'      // Aspect ratio & layout
  | 'branding'    // Watermark, logo, intro
  | 'insights'    // V9.6: retention heatmap + hook lab
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
  { id: 'insights', label: 'Insights', icon: Activity },
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

  // Undo / Redo History State
  const historyRef = useRef<{ past: EditorState[]; future: EditorState[] }>({ past: [], future: [] });
  const [historyVersion, setHistoryVersion] = useState(0);

  // Overlay state & drag tracking
  const [overlays, setOverlays] = useState<Array<{
    id: string;
    type: string;
    content: string;
    x: number;
    y: number;
    width: number;
    height: number;
    rotation: number;
    fontSize: number;
    color: string;
    bgColor: string;
    start: number;
    end: number;
    animationIn: string;
    animationOut: string;
    locked: boolean;
    visible: boolean;
    zIndex: number;
  }>>([]);
  const [selectedOverlayId, setSelectedOverlayId] = useState<string | null>(null);
  const [draggingOverlayId, setDraggingOverlayId] = useState<string | null>(null);
  const dragStartPos = useRef<{ mouseX: number; mouseY: number; overlayX: number; overlayY: number }>({ mouseX: 0, mouseY: 0, overlayX: 0, overlayY: 0 });
  const previewContainerRef = useRef<HTMLDivElement>(null);

  // FFmpeg Preview state
  const [previewLoading, setPreviewLoading] = useState(false);
  const [previewUrl, setPreviewUrl] = useState<string | null>(null);

  const selectedClip = clips[selectedClipIndex];

  // History functions
  const pushHistory = useCallback((state: EditorState) => {
    historyRef.current.past.push(state);
    historyRef.current.future = [];
    setHistoryVersion(v => v + 1);
  }, []);

  const undo = useCallback(() => {
    if (historyRef.current.past.length === 0) return;
    const previous = historyRef.current.past.pop()!;
    setEditorState(current => {
      historyRef.current.future.push(current);
      return previous;
    });
    setHasChanges(true);
    setHistoryVersion(v => v + 1);
    sound.playClick();
  }, []);

  const redo = useCallback(() => {
    if (historyRef.current.future.length === 0) return;
    const next = historyRef.current.future.pop()!;
    setEditorState(current => {
      historyRef.current.past.push(current);
      return next;
    });
    setHasChanges(true);
    setHistoryVersion(v => v + 1);
    sound.playClick();
  }, []);

  // Update state helper with undo/redo history
  const update = useCallback(<K extends keyof EditorState>(key: K, value: EditorState[K]) => {
    setEditorState(prev => {
      pushHistory(prev);
      return { ...prev, [key]: value };
    });
    setHasChanges(true);
    sound.playClick();
  }, [pushHistory]);

  // Apply a creator template with undo/redo history
  const applyTemplate = useCallback((template: CreatorTemplate) => {
    setEditorState(prev => {
      pushHistory(prev);
      return {
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
      };
    });
    setHasChanges(true);
    sound.playSuccess();
  }, [pushHistory]);

  // Overlay management functions
  const addTextOverlay = useCallback(() => {
    const newOverlay = {
      id: `overlay_${Date.now()}_${Math.random().toString(36).substring(2, 6)}`,
      type: 'text',
      content: 'New Text Overlay',
      x: 50,
      y: 50,
      width: 200,
      height: 50,
      rotation: 0,
      fontSize: 24,
      color: '#ffffff',
      bgColor: 'rgba(0, 0, 0, 0.6)',
      start: 0,
      end: 10,
      animationIn: 'fade',
      animationOut: 'fade',
      locked: false,
      visible: true,
      zIndex: overlays.length + 1,
    };
    setOverlays(prev => [...prev, newOverlay]);
    setSelectedOverlayId(newOverlay.id);
    setHasChanges(true);
    sound.playClick();
  }, [overlays.length]);

  const updateOverlay = useCallback((id: string, props: Partial<(typeof overlays)[0]>) => {
    setOverlays(prev => prev.map(o => o.id === id ? { ...o, ...props } : o));
    setHasChanges(true);
  }, []);

  const removeOverlay = useCallback((id: string) => {
    setOverlays(prev => prev.filter(o => o.id !== id));
    if (selectedOverlayId === id) setSelectedOverlayId(null);
    setHasChanges(true);
    sound.playClick();
  }, [selectedOverlayId]);

  const selectOverlay = useCallback((id: string | null) => {
    setSelectedOverlayId(id);
  }, []);

  const handleOverlayMouseDown = (e: React.MouseEvent, overlay: (typeof overlays)[0]) => {
    if (overlay.locked || !overlay.visible) return;
    e.stopPropagation();
    selectOverlay(overlay.id);
    setDraggingOverlayId(overlay.id);
    dragStartPos.current = {
      mouseX: e.clientX,
      mouseY: e.clientY,
      overlayX: overlay.x,
      overlayY: overlay.y,
    };
  };

  // Drag tracking mouse listeners
  useEffect(() => {
    if (!draggingOverlayId) return;

    const handleMouseMove = (e: MouseEvent) => {
      if (!previewContainerRef.current) return;
      const rect = previewContainerRef.current.getBoundingClientRect();
      if (rect.width === 0 || rect.height === 0) return;

      const deltaXPixels = e.clientX - dragStartPos.current.mouseX;
      const deltaYPixels = e.clientY - dragStartPos.current.mouseY;

      const deltaXPercent = (deltaXPixels / rect.width) * 100;
      const deltaYPercent = (deltaYPixels / rect.height) * 100;

      const newX = Math.max(0, Math.min(100, dragStartPos.current.overlayX + deltaXPercent));
      const newY = Math.max(0, Math.min(100, dragStartPos.current.overlayY + deltaYPercent));

      setOverlays(prev => prev.map(o => o.id === draggingOverlayId ? { ...o, x: Math.round(newX * 10) / 10, y: Math.round(newY * 10) / 10 } : o));
      setHasChanges(true);
    };

    const handleMouseUp = () => {
      setDraggingOverlayId(null);
    };

    window.addEventListener('mousemove', handleMouseMove);
    window.addEventListener('mouseup', handleMouseUp);
    return () => {
      window.removeEventListener('mousemove', handleMouseMove);
      window.removeEventListener('mouseup', handleMouseUp);
    };
  }, [draggingOverlayId]);

  // Generate FFmpeg Preview
  const generatePreview = async () => {
    setPreviewLoading(true);
    try {
      const res = await editorApi.previewRender(jobId, selectedClipIndex, {
        subtitle_style: editorState.captionStyle,
        zoom_style: editorState.zoomStyle,
        color_grade: editorState.colorGrade,
        aspect_ratio: editorState.aspectRatio,
        preview_duration: 5,
      });
      if (res && res.preview_url) {
        setPreviewUrl(buildOutputUrl(res.preview_url));
        sound.playSuccess();
      } else {
        setPreviewUrl(null);
      }
    } catch (err) {
      console.warn('FFmpeg preview render failed, falling back to CSS preview:', err);
      setPreviewUrl(null);
    } finally {
      setPreviewLoading(false);
    }
  };

  // Sync subtitle store with editor state
  useEffect(() => {
    subtitleStore.set({
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

    // Call editorApi to re-render with all personalization settings including overlays
    try {
      const settings = {
        subtitle_style: editorState.captionStyle,
        font: editorState.fontFamily,
        font_size: { compact: 42, normal: 52, large: 64, huge: 78 }[editorState.fontSize] ?? 64,
        primary_color: editorState.primaryColor,
        highlight_color: editorState.highlightColor,
        position: editorState.position,
        animation: editorState.animation,
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
        overlays: overlays as any,
      };

      const result = await editorApi.reRenderClip(jobId, selectedClipIndex, settings);
      setRenderResult({ success: true, message: 'Re-render complete!', changes: result.changes_applied });
      setHasChanges(false);
      sound.playSuccess();
    } catch (e) {
      console.error('Re-render failed:', e);
      setRenderResult({ success: false, message: 'Re-render failed. Check server logs.' });
    }

    setIsReRendering(false);
  };

  // Keyboard Shortcuts Listener
  useEffect(() => {
    const handleKeyDown = (e: KeyboardEvent) => {
      const target = e.target as HTMLElement | null;
      const isInput = target && (
        target.tagName === 'INPUT' ||
        target.tagName === 'TEXTAREA' ||
        target.tagName === 'SELECT' ||
        target.isContentEditable
      );

      // Ctrl+Z or Cmd+Z = undo
      if ((e.ctrlKey || e.metaKey) && e.key.toLowerCase() === 'z' && !e.shiftKey) {
        e.preventDefault();
        undo();
        return;
      }

      // Ctrl+Shift+Z or Ctrl+Y = redo
      if (
        ((e.ctrlKey || e.metaKey) && e.shiftKey && e.key.toLowerCase() === 'z') ||
        ((e.ctrlKey || e.metaKey) && e.key.toLowerCase() === 'y')
      ) {
        e.preventDefault();
        redo();
        return;
      }

      // Ctrl+S = handleReRender
      if ((e.ctrlKey || e.metaKey) && e.key.toLowerCase() === 's') {
        e.preventDefault();
        handleReRender();
        return;
      }

      // Escape = onClose
      if (e.key === 'Escape') {
        e.preventDefault();
        onClose();
        return;
      }

      if (isInput) return;

      // Space = togglePlay (prevent default scroll)
      if (e.code === 'Space' || e.key === ' ') {
        e.preventDefault();
        togglePlay();
        return;
      }

      // ArrowLeft = skipTime(-5)
      if (e.key === 'ArrowLeft') {
        e.preventDefault();
        skipTime(-5);
        return;
      }

      // ArrowRight = skipTime(+5)
      if (e.key === 'ArrowRight') {
        e.preventDefault();
        skipTime(5);
        return;
      }

      // Tab = cycle to next tab (prevent default)
      if (e.key === 'Tab') {
        e.preventDefault();
        const tabKeys = EDITOR_TABS.map(t => t.id);
        setActiveTab(prevTab => {
          const currentIndex = tabKeys.indexOf(prevTab);
          const nextIndex = (currentIndex + 1) % tabKeys.length;
          return tabKeys[nextIndex];
        });
        return;
      }

      // 1-8 = switch tab by index
      if (e.key >= '1' && e.key <= '8') {
        const index = parseInt(e.key, 10) - 1;
        if (index >= 0 && index < EDITOR_TABS.length) {
          e.preventDefault();
          setActiveTab(EDITOR_TABS[index].id);
          return;
        }
      }
    };

    document.addEventListener('keydown', handleKeyDown);
    return () => {
      document.removeEventListener('keydown', handleKeyDown);
    };
  }, [undo, redo, togglePlay, skipTime, handleReRender, onClose]);

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
            onClick={() => { sound.playClick(); pushHistory(editorState); setEditorState(DEFAULT_EDITOR_STATE); setHasChanges(false); }}
            onMouseEnter={() => sound.playHover()}
            className="flex items-center gap-2 px-3 py-2 rounded-xl bg-white/5 hover:bg-white/10 text-stone-400 hover:text-white border border-white/10 text-xs font-mono transition-colors"
          >
            <RotateCcw className="w-3.5 h-3.5" />
            <span className="hidden sm:inline">Reset</span>
          </button>
          <button
            onClick={undo}
            disabled={historyRef.current.past.length === 0}
            onMouseEnter={() => sound.playHover()}
            className="flex items-center gap-2 px-3 py-2 rounded-xl bg-white/5 hover:bg-white/10 text-stone-400 hover:text-white border border-white/10 text-xs font-mono transition-colors disabled:opacity-40 disabled:cursor-not-allowed"
            title="Undo (Ctrl+Z)"
          >
            <Undo className="w-3.5 h-3.5" />
            <span className="hidden sm:inline">Undo</span>
          </button>
          <button
            onClick={redo}
            disabled={historyRef.current.future.length === 0}
            onMouseEnter={() => sound.playHover()}
            className="flex items-center gap-2 px-3 py-2 rounded-xl bg-white/5 hover:bg-white/10 text-stone-400 hover:text-white border border-white/10 text-xs font-mono transition-colors disabled:opacity-40 disabled:cursor-not-allowed"
            title="Redo (Ctrl+Shift+Z)"
          >
            <Redo className="w-3.5 h-3.5" />
            <span className="hidden sm:inline">Redo</span>
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
            ref={previewContainerRef}
            onClick={() => selectOverlay(null)}
            className="relative bg-black rounded-2xl overflow-hidden border border-white/10 shadow-2xl"
            style={{
              aspectRatio: `${currentAspect.w} / ${currentAspect.h}`,
              maxHeight: '100%',
              maxWidth: '100%',
              width: editorState.aspectRatio === '16:9' ? '100%' : 'auto',
              height: editorState.aspectRatio === '16:9' ? 'auto' : '100%',
            }}
          >
            {/* FFmpeg Preview video or standard video */}
            {previewUrl ? (
              <video
                src={previewUrl}
                className="w-full h-full object-contain"
                autoPlay
                loop
                muted
                playsInline
              />
            ) : selectedClip?.videoUrl ? (
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
            ) : null}

            {/* Loading spinner for FFmpeg preview */}
            {previewLoading && (
              <div className="absolute inset-0 z-40 bg-black/70 backdrop-blur-sm flex flex-col items-center justify-center gap-3">
                <Loader2 className="w-10 h-10 text-cyan-400 animate-spin" />
                <span className="text-xs font-mono text-cyan-200">Rendering FFmpeg Preview...</span>
              </div>
            )}

            {/* FFmpeg Preview indicator badge */}
            {previewUrl && (
              <div className="absolute top-3 left-3 z-30 flex items-center gap-2 px-2.5 py-1 rounded-full bg-cyan-500/20 border border-cyan-500/40 text-cyan-300 text-[10px] font-mono">
                <span>FFmpeg Preview (5s)</span>
                <button
                  onClick={(e) => { e.stopPropagation(); setPreviewUrl(null); }}
                  className="hover:text-white"
                  title="Switch back to live CSS preview"
                >
                  <X className="w-3 h-3" />
                </button>
              </div>
            )}

            {/* Color grade overlay */}
            {editorState.colorGrade !== 'none' && !previewUrl && (
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
            {editorState.zoomLevel > 1.0 && !previewUrl && (
              <div
                className="absolute inset-0 pointer-events-none"
                style={{ transform: `scale(${editorState.zoomLevel})`, transformOrigin: 'center' }}
              />
            )}

            {/* Cinematic bars */}
            {editorState.colorGrade === 'cinematic' && !previewUrl && (
              <>
                <div className="absolute top-0 left-0 right-0 h-[8%] bg-black z-10 pointer-events-none" />
                <div className="absolute bottom-0 left-0 right-0 h-[8%] bg-black z-10 pointer-events-none" />
              </>
            )}

            {/* Live subtitle preview overlay */}
            {!previewUrl && (
              <div className={`absolute left-0 right-0 z-20 pointer-events-none ${
                editorState.position === 'top' ? 'top-[10%]' :
                editorState.position === 'center' ? 'top-1/2 -translate-y-1/2' :
                'bottom-[12%]'
              }`}>
                <LiveSubtitleRenderer
                  currentLine={previewLine}
                  lineIndex={0}
                  wordIndex={Math.floor(currentTime * 3) % previewLine.words.length}
                  config={subtitleStore.get()}
                />
              </div>
            )}

            {/* Draggable Overlays */}
            {overlays.filter(o => o.visible).map(overlay => {
              const isSelected = overlay.id === selectedOverlayId;
              return (
                <div
                  key={overlay.id}
                  onMouseDown={(e) => handleOverlayMouseDown(e, overlay)}
                  onClick={(e) => { e.stopPropagation(); selectOverlay(overlay.id); }}
                  className={`absolute select-none transition-shadow ${
                    overlay.locked ? 'cursor-not-allowed' : 'cursor-move'
                  } ${
                    isSelected ? 'ring-2 ring-cyan-400 ring-offset-1 ring-offset-black' : 'hover:ring-1 hover:ring-white/50'
                  }`}
                  style={{
                    left: `${overlay.x}%`,
                    top: `${overlay.y}%`,
                    transform: `translate(-50%, -50%) rotate(${overlay.rotation || 0}deg)`,
                    zIndex: overlay.zIndex || 25,
                    color: overlay.color,
                    backgroundColor: overlay.bgColor,
                    fontSize: `${overlay.fontSize}px`,
                    padding: '4px 12px',
                    borderRadius: '6px',
                    whiteSpace: 'nowrap',
                    fontWeight: 600,
                  }}
                >
                  {overlay.content}
                  {isSelected && (
                    <div className="absolute -top-6 left-1/2 -translate-x-1/2 px-1.5 py-0.5 rounded bg-cyan-500 text-[9px] font-mono text-black font-bold flex items-center gap-1 pointer-events-none">
                      <span>{Math.round(overlay.x)}%, {Math.round(overlay.y)}%</span>
                      {overlay.locked && <Lock className="w-2.5 h-2.5" />}
                    </div>
                  )}
                </div>
              );
            })}

            {/* Progress bar */}
            {editorState.progressbar && !previewUrl && (
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
            {editorState.showWatermark && editorState.watermarkText && !previewUrl && (
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
            {!selectedClip?.videoUrl && !previewUrl && (
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

                {/* Overlays Management Section */}
                <div className="pt-3 border-t border-white/10 space-y-3">
                  <div className="flex items-center justify-between">
                    <span className="text-xs font-mono font-bold text-white uppercase tracking-wider">Overlays ({overlays.length})</span>
                    <button
                      onClick={addTextOverlay}
                      className="flex items-center gap-1 px-2.5 py-1 rounded-lg bg-cyan-500/20 hover:bg-cyan-500/30 text-cyan-300 border border-cyan-500/40 text-xs font-mono transition-colors"
                    >
                      <Plus className="w-3 h-3" />
                      <span>Add Text Overlay</span>
                    </button>
                  </div>

                  {overlays.length === 0 ? (
                    <div className="p-3 rounded-xl bg-white/5 border border-dashed border-white/10 text-center text-stone-500 text-xs font-mono">
                      No text overlays. Click "Add Text Overlay" and drag it on the video preview canvas.
                    </div>
                  ) : (
                    <div className="space-y-2 max-h-60 overflow-y-auto pr-1">
                      {overlays.map(overlay => (
                        <div
                          key={overlay.id}
                          onClick={() => selectOverlay(overlay.id)}
                          className={`p-2.5 rounded-xl border transition-all text-xs font-mono space-y-2 ${
                            selectedOverlayId === overlay.id
                              ? 'bg-cyan-950/40 border-cyan-500/50 text-white'
                              : 'bg-white/5 border-white/10 text-stone-300 hover:bg-white/10'
                          }`}
                        >
                          <div className="flex items-center justify-between gap-2">
                            <input
                              type="text"
                              value={overlay.content}
                              onChange={(e) => updateOverlay(overlay.id, { content: e.target.value })}
                              onClick={(e) => e.stopPropagation()}
                              className="flex-1 px-2 py-1 rounded bg-black/50 border border-white/10 text-xs text-white focus:outline-none focus:border-cyan-400"
                            />
                            <div className="flex items-center gap-1">
                              <button
                                onClick={(e) => { e.stopPropagation(); updateOverlay(overlay.id, { visible: !overlay.visible }); }}
                                className={`p-1 rounded ${overlay.visible ? 'text-cyan-400' : 'text-stone-600'}`}
                                title={overlay.visible ? 'Hide' : 'Show'}
                              >
                                {overlay.visible ? <Eye className="w-3.5 h-3.5" /> : <EyeOff className="w-3.5 h-3.5" />}
                              </button>
                              <button
                                onClick={(e) => { e.stopPropagation(); updateOverlay(overlay.id, { locked: !overlay.locked }); }}
                                className={`p-1 rounded ${overlay.locked ? 'text-amber-400' : 'text-stone-600'}`}
                                title={overlay.locked ? 'Unlock drag' : 'Lock position'}
                              >
                                {overlay.locked ? <Lock className="w-3.5 h-3.5" /> : <Unlock className="w-3.5 h-3.5" />}
                              </button>
                              <button
                                onClick={(e) => { e.stopPropagation(); removeOverlay(overlay.id); }}
                                className="p-1 rounded text-stone-500 hover:text-red-400"
                                title="Remove overlay"
                              >
                                <Trash2 className="w-3.5 h-3.5" />
                              </button>
                            </div>
                          </div>
                          {selectedOverlayId === overlay.id && (
                            <div className="grid grid-cols-2 gap-2 pt-1 border-t border-white/10">
                              <div>
                                <label className="text-[10px] text-stone-400 block mb-1">Color</label>
                                <input
                                  type="color"
                                  value={overlay.color}
                                  onChange={(e) => updateOverlay(overlay.id, { color: e.target.value })}
                                  className="w-full h-6 rounded bg-transparent cursor-pointer"
                                />
                              </div>
                              <div>
                                <label className="text-[10px] text-stone-400 block mb-1">Font Size ({overlay.fontSize}px)</label>
                                <input
                                  type="range"
                                  min="12"
                                  max="72"
                                  value={overlay.fontSize}
                                  onChange={(e) => updateOverlay(overlay.id, { fontSize: parseInt(e.target.value, 10) })}
                                  className="w-full"
                                />
                              </div>
                            </div>
                          )}
                        </div>
                      ))}
                    </div>
                  )}
                </div>
              </motion.div>
            )}

            {/* ━━━━━━━━ EXPORT TAB ━━━━━━━━ */}
            {activeTab === 'insights' && (
              <motion.div key="insights" initial={{ opacity: 0, x: 20 }} animate={{ opacity: 1, x: 0 }} exit={{ opacity: 0, x: -20 }}>
                <div className="pt-4 px-4">
                  <PanelHeader icon={Activity} title="Beyond-Opus Insights" subtitle="Retention heatmap & hook lab" />
                </div>
                <InsightsPanel jobId={jobId} clipIndex={selectedClipIndex} />
              </motion.div>
            )}

            {activeTab === 'export' && (
              <motion.div key="export" initial={{ opacity: 0, x: 20 }} animate={{ opacity: 1, x: 0 }} exit={{ opacity: 0, x: -20 }} className="p-4 space-y-5">
                <PanelHeader icon={Download} title="Export & Publish" subtitle="Re-render and share" />

                <TitleStudio
                  initialTitle={selectedClip?.title || ''}
                  clipText={selectedClip?.subtitleSnippet || ''}
                />

                {hasChanges && (
                  <div className="p-3 rounded-xl bg-amber-500/10 border border-amber-500/30 flex items-center gap-2">
                    <AlertCircle className="w-4 h-4 text-amber-400 flex-shrink-0" />
                    <span className="text-xs text-amber-300 font-mono">
                      You have unsaved changes. Re-render to apply.
                    </span>
                  </div>
                )}

                <div className="space-y-2">
                  <button
                    onClick={generatePreview}
                    disabled={previewLoading}
                    className="w-full flex items-center justify-center gap-2 px-4 py-2.5 rounded-xl bg-purple-600/30 hover:bg-purple-600/40 text-purple-200 border border-purple-500/40 text-xs font-mono font-bold transition-colors disabled:opacity-50"
                  >
                    {previewLoading ? (
                      <><Loader2 className="w-4 h-4 animate-spin text-purple-300" /> Generating FFmpeg Preview...</>
                    ) : (
                      <><Sparkles className="w-4 h-4 text-purple-300" /> Generate FFmpeg Preview (5s)</>
                    )}
                  </button>

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
                </div>

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
