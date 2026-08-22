import React, { useState, useEffect, useRef } from 'react';
import { motion, AnimatePresence } from 'motion/react';
import {
  Search,
  Sparkles,
  Wand2,
  Volume2,
  VolumeX,
  Music,
  Zap,
  ZapOff,
  Clock,
  Download,
  Play,
  Hash,
  FileText,
  Image as ImageIcon,
  Loader2,
  ChevronDown,
  ChevronUp,
  Mic,
  SlidersHorizontal,
} from 'lucide-react';
import { mode2Api, buildOutputUrl, type Mode2Response, type Mode2Voice } from '../api/nexuxApi';
import { v2Api, type Mode2StoryboardResult } from '../api/v2Api';
import { ClipEditorStudio } from './ClipEditorStudio';
import type { GeneratedClip } from './VideoResultCard';
import { sound } from '../utils/soundEffects';

interface Mode2ConsoleProps {
  onBack?: () => void;
}

export const Mode2Console: React.FC<Mode2ConsoleProps> = ({ onBack }) => {
  const [keyword, setKeyword] = useState('');
  const [stage, setStage] = useState<'input' | 'processing' | 'results' | 'error'>('input');
  const [progress, setProgress] = useState(0);
  const [progressMsg, setProgressMsg] = useState('');
  const [result, setResult] = useState<Mode2Response | null>(null);
  const [showAdvanced, setShowAdvanced] = useState(false);
  const [showEditor, setShowEditor] = useState(false);

  // Storyboard
  const [storyboard, setStoryboard] = useState<Mode2StoryboardResult | null>(null);
  const [storyboardLoading, setStoryboardLoading] = useState(false);

  // Settings
  const [voiceEnabled, setVoiceEnabled] = useState(true);
  const [voiceName, setVoiceName] = useState('id-ID-ArdiNeural');
  const [sfxEnabled, setSfxEnabled] = useState(true);
  const [bgmEnabled, setBgmEnabled] = useState(true);
  const [targetDuration, setTargetDuration] = useState(60);
  const [maxSources, setMaxSources] = useState(10);

  // Voices
  const [voices, setVoices] = useState<Mode2Voice[]>([]);

  const inputRef = useRef<HTMLInputElement>(null);

  useEffect(() => {
    // Fetch available voices
    mode2Api.voices().then(res => setVoices(res.voices || [])).catch(() => {});
    inputRef.current?.focus();
  }, []);

  const handleStoryboard = async () => {
    if (!keyword.trim()) return;
    setStoryboardLoading(true);
    setStoryboard(null);
    try {
      const res = await v2Api.mode2Storyboard({ keyword: keyword.trim(), max_clips: 5 });
      setStoryboard(res);
    } catch {
      // ignore — user can still hit Generate
    } finally {
      setStoryboardLoading(false);
    }
  };

  const handleGenerateFromStoryboard = async () => {
    if (!storyboard || storyboard.total_clips === 0) return;
    setStage('processing');
    setProgress(0);
    setProgressMsg('Compiling storyboard...');
    setResult(null);
    try {
      const res = await mode2Api.generate({
        keyword: keyword.trim(),
        voice_enabled: voiceEnabled,
        voice_name: voiceName,
        sfx_enabled: sfxEnabled,
        bgm_enabled: bgmEnabled,
        target_duration: targetDuration,
        max_sources: maxSources,
      });
      if (res.status === 'error') {
        setStage('error');
      } else {
        setResult(res);
        setStage('results');
      }
    } catch (err) {
      setStage('error');
    }
  };

  const handleGenerate = async () => {
    if (!keyword.trim()) {
      
      return;
    }

    
    setStage('processing');
    setProgress(0);
    setProgressMsg('Initializing...');
    setResult(null);

    try {
      const res = await mode2Api.generate({
        keyword: keyword.trim(),
        voice_enabled: voiceEnabled,
        voice_name: voiceName,
        sfx_enabled: sfxEnabled,
        bgm_enabled: bgmEnabled,
        target_duration: targetDuration,
        max_sources: maxSources,
      });

      if (res.status === 'error') {
        setStage('error');
        
      } else {
        setResult(res);
        setStage('results');
        
      }
    } catch (err) {
      setStage('error');
      
    }
  };

  const handleReset = () => {
    setStage('input');
    setKeyword('');
    setResult(null);
    setProgress(0);
    inputRef.current?.focus();
  };

  return (
    <div className="relative w-full max-w-2xl mx-auto">
      {/* Back button */}
      {onBack && (
        <button
          onClick={() => {  onBack(); }}
          className="absolute -top-12 left-0 text-gray-400 hover:text-white transition-colors text-sm flex items-center gap-2"
        >
          ← Mode 1
        </button>
      )}

      <AnimatePresence mode="wait">
        {/* ── INPUT STAGE ── */}
        {stage === 'input' && (
          <motion.div
            key="input"
            initial={{ opacity: 0, y: 20 }}
            animate={{ opacity: 1, y: 0 }}
            exit={{ opacity: 0, y: -20 }}
            className="relative"
          >
            {/* Mode 2 Badge */}
            <div className="flex items-center justify-center gap-3 mb-6">
              <div className="px-4 py-1.5 rounded-full bg-gradient-to-r from-purple-500/20 to-pink-500/20 border border-purple-500/30 text-purple-300 text-sm font-medium flex items-center gap-2">
                <Wand2 className="w-4 h-4" />
                Mode 2 — Creative Viral
              </div>
            </div>

            {/* Keyword Input */}
            <div className="relative group">
              <div className="absolute -inset-0.5 bg-gradient-to-r from-purple-500 to-pink-500 rounded-2xl blur opacity-25 group-focus-within:opacity-50 transition-opacity" />
              <div className="relative bg-black/40 backdrop-blur-xl rounded-2xl border border-white/10 p-6">
                <label className="text-gray-400 text-sm mb-3 block">
                  Ketik satu kata kunci — AI cari, edit, dan render semuanya
                </label>
                <div className="flex gap-3">
                  <div className="flex-1 relative">
                    <Search className="absolute left-4 top-1/2 -translate-y-1/2 w-5 h-5 text-gray-500" />
                    <input
                      ref={inputRef}
                      type="text"
                      value={keyword}
                      onChange={(e) => setKeyword(e.target.value)}
                      onKeyDown={(e) => e.key === 'Enter' && handleGenerate()}
                      placeholder="contoh: peter parker, one punch man, game terbaik..."
                      className="w-full bg-white/5 border border-white/10 rounded-xl pl-12 pr-4 py-4 text-white placeholder-gray-500 focus:outline-none focus:border-purple-500/50 transition-colors text-lg"
                    />
                  </div>
                  <button
                    onClick={handleGenerate}
                    disabled={!keyword.trim()}
                    className="px-6 py-4 rounded-xl bg-gradient-to-r from-purple-500 to-pink-500 text-white font-medium disabled:opacity-30 disabled:cursor-not-allowed hover:opacity-90 transition-opacity flex items-center gap-2"
                  >
                    <Sparkles className="w-5 h-5" />
                    Generate
                  </button>
                </div>

                {/* Storyboard planner */}
                <div className="mt-4 flex items-center justify-between">
                  <button
                    onClick={handleStoryboard}
                    disabled={!keyword.trim() || storyboardLoading}
                    className="text-xs text-cyan-300 hover:text-cyan-200 disabled:text-gray-600 flex items-center gap-1.5 transition-colors"
                  >
                    {storyboardLoading ? (
                      <Loader2 className="w-3.5 h-3.5 animate-spin" />
                    ) : (
                      <FileText className="w-3.5 h-3.5" />
                    )}
                    Preview Storyboard (multi-archetype)
                  </button>
                </div>

                {storyboard && storyboard.total_clips > 0 && (
                  <div className="mt-3 space-y-2">
                    <div className="text-[11px] text-gray-400 font-mono uppercase tracking-wider">
                      Storyboard — {storyboard.total_clips} klip
                    </div>
                    {storyboard.storyboard.map((clip) => (
                      <div key={clip.clip_idx} className="flex items-center gap-3 p-3 rounded-lg bg-white/5 border border-white/10">
                        <span className={`w-16 shrink-0 text-[10px] font-mono uppercase ${
                          clip.role === 'hook' ? 'text-amber-400' : clip.role === 'payoff' ? 'text-emerald-400' : 'text-cyan-300'
                        }`}>
                          {clip.role}
                        </span>
                        <span className="flex-1 text-xs text-gray-200 truncate" title={clip.video_title}>
                          {clip.video_title}
                        </span>
                        <span className="text-[10px] text-gray-500 font-mono">{clip.duration}s</span>
                      </div>
                    ))}
                    <button
                      onClick={handleGenerateFromStoryboard}
                      className="w-full mt-2 px-4 py-2.5 rounded-xl bg-gradient-to-r from-cyan-500 to-blue-500 text-white text-sm font-medium flex items-center justify-center gap-2 hover:opacity-90 transition-opacity"
                    >
                      <Sparkles className="w-4 h-4" />
                      Buat dari Storyboard ({storyboard.total_clips} klip)
                    </button>
                  </div>
                )}
              </div>
            </div>

            {/* Advanced Settings */}
            <div className="mt-4">
              <button
                onClick={() => {  setShowAdvanced(!showAdvanced); }}
                className="text-gray-400 hover:text-white text-sm flex items-center gap-2 transition-colors"
              >
                {showAdvanced ? <ChevronUp className="w-4 h-4" /> : <ChevronDown className="w-4 h-4" />}
                Advanced Settings
              </button>

              <AnimatePresence>
                {showAdvanced && (
                  <motion.div
                    initial={{ opacity: 0, height: 0 }}
                    animate={{ opacity: 1, height: 'auto' }}
                    exit={{ opacity: 0, height: 0 }}
                    className="overflow-hidden"
                  >
                    <div className="mt-4 grid grid-cols-2 gap-3 p-4 bg-black/30 rounded-xl border border-white/5">
                      {/* Voice Toggle */}
                      <button
                        onClick={() => {  setVoiceEnabled(!voiceEnabled); }}
                        className={`flex items-center gap-2 p-3 rounded-lg border transition-colors ${voiceEnabled ? 'bg-purple-500/10 border-purple-500/30 text-purple-300' : 'bg-white/5 border-white/10 text-gray-500'}`}
                      >
                        {voiceEnabled ? <Mic className="w-4 h-4" /> : <VolumeX className="w-4 h-4" />}
                        <span className="text-sm">Voice-over</span>
                      </button>

                      {/* SFX Toggle */}
                      <button
                        onClick={() => {  setSfxEnabled(!sfxEnabled); }}
                        className={`flex items-center gap-2 p-3 rounded-lg border transition-colors ${sfxEnabled ? 'bg-purple-500/10 border-purple-500/30 text-purple-300' : 'bg-white/5 border-white/10 text-gray-500'}`}
                      >
                        {sfxEnabled ? <Zap className="w-4 h-4" /> : <ZapOff className="w-4 h-4" />}
                        <span className="text-sm">SFX</span>
                      </button>

                      {/* BGM Toggle */}
                      <button
                        onClick={() => {  setBgmEnabled(!bgmEnabled); }}
                        className={`flex items-center gap-2 p-3 rounded-lg border transition-colors ${bgmEnabled ? 'bg-purple-500/10 border-purple-500/30 text-purple-300' : 'bg-white/5 border-white/10 text-gray-500'}`}
                      >
                        {bgmEnabled ? <Music className="w-4 h-4" /> : <Music className="w-4 h-4" />}
                        <span className="text-sm">Background Music</span>
                      </button>

                      {/* Duration */}
                      <div className="flex items-center gap-2 p-3 rounded-lg border border-white/10 bg-white/5">
                        <Clock className="w-4 h-4 text-gray-500" />
                        <select
                          value={targetDuration}
                          onChange={(e) => setTargetDuration(Number(e.target.value))}
                          className="bg-transparent text-sm text-white focus:outline-none"
                        >
                          <option value={30} className="bg-gray-900">30s</option>
                          <option value={45} className="bg-gray-900">45s</option>
                          <option value={60} className="bg-gray-900">60s</option>
                          <option value={90} className="bg-gray-900">90s</option>
                        </select>
                      </div>

                      {/* Voice Selection */}
                      {voiceEnabled && voices.length > 0 && (
                        <div className="col-span-2 flex items-center gap-2 p-3 rounded-lg border border-white/10 bg-white/5">
                          <Volume2 className="w-4 h-4 text-gray-500" />
                          <select
                            value={voiceName}
                            onChange={(e) => setVoiceName(e.target.value)}
                            className="flex-1 bg-transparent text-sm text-white focus:outline-none"
                          >
                            {voices.map(v => (
                              <option key={v.id} value={v.id} className="bg-gray-900">{v.name}</option>
                            ))}
                          </select>
                        </div>
                      )}

                      {/* Max Sources */}
                      <div className="col-span-2 flex items-center gap-2 p-3 rounded-lg border border-white/10 bg-white/5">
                        <Hash className="w-4 h-4 text-gray-500" />
                        <span className="text-sm text-gray-400">Sources:</span>
                        <input
                          type="range"
                          min={5}
                          max={15}
                          value={maxSources}
                          onChange={(e) => setMaxSources(Number(e.target.value))}
                          className="flex-1 accent-purple-500"
                        />
                        <span className="text-sm text-white">{maxSources} videos</span>
                      </div>
                    </div>
                  </motion.div>
                )}
              </AnimatePresence>
            </div>

            {/* Hint */}
            <p className="text-center text-gray-500 text-sm mt-6">
              AI akan mencari {maxSources} video terkait, mengunduh momen relevan, menulis naskah, dan merender video viral.
            </p>
          </motion.div>
        )}

        {/* ── PROCESSING STAGE ── */}
        {stage === 'processing' && (
          <motion.div
            key="processing"
            initial={{ opacity: 0 }}
            animate={{ opacity: 1 }}
            exit={{ opacity: 0 }}
            className="text-center py-20"
          >
            <motion.div
              animate={{ rotate: 360 }}
              transition={{ duration: 2, repeat: Infinity, ease: 'linear' }}
              className="w-16 h-16 mx-auto mb-6"
            >
              <div className="w-16 h-16 rounded-full border-4 border-purple-500/20 border-t-purple-500" />
            </motion.div>
            <h3 className="text-2xl font-bold text-white mb-2">Creating your video...</h3>
            <p className="text-purple-300 mb-6">AI is working on "{keyword}"</p>
            <div className="max-w-md mx-auto">
              <div className="h-2 bg-white/5 rounded-full overflow-hidden">
                <motion.div
                  className="h-full bg-gradient-to-r from-purple-500 to-pink-500"
                  initial={{ width: '0%' }}
                  animate={{ width: '100%' }}
                  transition={{ duration: 60, ease: 'linear' }}
                />
              </div>
              <p className="text-gray-500 text-sm mt-3">
                Searching YouTube → Analyzing transcripts → Writing narrative → Downloading → Compiling
              </p>
            </div>
          </motion.div>
        )}

        {/* ── RESULTS STAGE ── */}
        {stage === 'results' && result && (
          <motion.div
            key="results"
            initial={{ opacity: 0, y: 20 }}
            animate={{ opacity: 1, y: 0 }}
            exit={{ opacity: 0, y: -20 }}
            className="space-y-6"
          >
            {/* Success Badge */}
            <div className="text-center">
              <div className="inline-flex items-center gap-2 px-4 py-1.5 rounded-full bg-green-500/20 border border-green-500/30 text-green-300 text-sm">
                <Sparkles className="w-4 h-4" /> Video Created!
              </div>
            </div>

            {/* Thumbnail + Video Preview */}
            <div className="relative group rounded-2xl overflow-hidden border border-white/10 max-w-sm mx-auto">
              {result.thumbnail_path && (
                <img
                  src={`/api/download/${result.job_id}/thumbnail`}
                  alt="Thumbnail"
                  className="w-full aspect-[9/16] object-cover"
                />
              )}
              <div className="absolute inset-0 bg-gradient-to-t from-black/60 to-transparent" />
              <div className="absolute bottom-4 left-4 right-4">
                <h3 className="text-white font-bold text-lg mb-1">{result.metadata?.title}</h3>
                <div className="flex gap-2 flex-wrap">
                  {result.metadata?.hashtags?.map((tag, i) => (
                    <span key={i} className="text-xs text-purple-300 bg-purple-500/20 px-2 py-0.5 rounded-full">
                      {tag}
                    </span>
                  ))}
                </div>
              </div>
            </div>

            {/* Stats */}
            <div className="grid grid-cols-3 gap-3 max-w-sm mx-auto">
              <div className="text-center p-3 bg-white/5 rounded-xl border border-white/10">
                <p className="text-2xl font-bold text-purple-300">{result.metadata?.sources_used || 0}</p>
                <p className="text-xs text-gray-500">Sources</p>
              </div>
              <div className="text-center p-3 bg-white/5 rounded-xl border border-white/10">
                <p className="text-2xl font-bold text-pink-300">{result.metadata?.total_duration || 0}s</p>
                <p className="text-xs text-gray-500">Duration</p>
              </div>
              <div className="text-center p-3 bg-white/5 rounded-xl border border-white/10">
                <p className="text-2xl font-bold text-green-300">{result.metadata?.processing_time || 0}s</p>
                <p className="text-xs text-gray-500">Process Time</p>
              </div>
            </div>

            {/* Description */}
            {result.metadata?.description && (
              <div className="p-4 bg-white/5 rounded-xl border border-white/10 max-w-sm mx-auto">
                <div className="flex items-center gap-2 mb-2 text-gray-400 text-sm">
                  <FileText className="w-4 h-4" /> Description
                </div>
                <p className="text-sm text-gray-300">{result.metadata.description}</p>
              </div>
            )}

            {/* Download + Edit Buttons */}
            <div className="flex justify-center gap-3">
              <a
                href={`/api/download/${result.job_id}`}
                className="px-6 py-3 rounded-xl bg-gradient-to-r from-purple-500 to-pink-500 text-white font-medium hover:opacity-90 transition-opacity flex items-center gap-2"
              >
                <Download className="w-5 h-5" /> Download Video
              </a>
              {result.output_path && (
                <button
                  onClick={() => { sound.playClick(); setShowEditor(true); }}
                  className="px-6 py-3 rounded-xl bg-cyan-500/15 border border-cyan-500/40 text-cyan-200 hover:bg-cyan-500/25 transition-colors flex items-center gap-2"
                >
                  <SlidersHorizontal className="w-5 h-5" /> Edit Video
                </button>
              )}
              <button
                onClick={handleReset}
                className="px-6 py-3 rounded-xl bg-white/5 border border-white/10 text-white hover:bg-white/10 transition-colors"
              >
                New Video
              </button>
            </div>
          </motion.div>
        )}

        {/* ── ERROR STAGE ── */}
        {stage === 'error' && (
          <motion.div
            key="error"
            initial={{ opacity: 0 }}
            animate={{ opacity: 1 }}
            exit={{ opacity: 0 }}
            className="text-center py-20"
          >
            <p className="text-red-400 text-lg mb-4">❌ {result?.error || 'Something went wrong'}</p>
            <button
              onClick={handleReset}
              className="px-6 py-3 rounded-xl bg-white/5 border border-white/10 text-white hover:bg-white/10 transition-colors"
            >
              Try Again
            </button>
          </motion.div>
        )}
      </AnimatePresence>

      {/* V9.6: Post-render editor handoff (Creative Mode) */}
      <AnimatePresence>
        {showEditor && result?.output_path && (
          <ClipEditorStudio
            clips={buildEditorClip(result)}
            jobId={result.job_id}
            onClose={() => setShowEditor(false)}
          />
        )}
      </AnimatePresence>
    </div>
  );
};

/** Build a single GeneratedClip from a Mode 2 result for the editor. */
function buildEditorClip(result: Mode2Response): GeneratedClip[] {
  const dur = result.metadata?.total_duration || 0;
  const mm = Math.floor(dur / 60);
  const ss = Math.round(dur % 60).toString().padStart(2, '0');
  return [{
    id: `${result.job_id}-clip-1`,
    title: result.metadata?.title || result.metadata?.keyword || 'Creative Video',
    hookCategory: 'Creative Compilation',
    duration: dur > 0 ? `${mm}:${ss}` : '—',
    viralScore: 75,
    timestampRange: '—',
    subtitleSnippet: result.metadata?.description?.slice(0, 120) || 'Video ready for preview',
    aspectRatio: '9:16',
    videoUrl: buildOutputUrl(result.output_path || null) || '',
    tags: result.metadata?.hashtags?.slice(0, 4) || [],
  }];
}
