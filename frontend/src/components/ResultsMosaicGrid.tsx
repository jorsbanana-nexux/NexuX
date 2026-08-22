import React, { useState } from 'react';
import { motion, AnimatePresence } from 'motion/react';
import { 
  RotateCcw, 
  Download, 
  CheckCircle2, 
  Sparkles,
  FileArchive,
  Wand2,
  Clapperboard,
} from 'lucide-react';
import { VideoResultCard, GeneratedClip } from './VideoResultCard';
import { nexuxApi } from '../api/nexuxApi';

interface ResultsMosaicProps {
  clips: GeneratedClip[];
  onReset: () => void;
  onPreviewClip: (clip: GeneratedClip) => void;
  onPersonalize?: () => void;
  onOpenTimelineEditor?: () => void;
}

export const ResultsMosaicGrid: React.FC<ResultsMosaicProps> = ({ clips, onReset, onPreviewClip, onPersonalize, onOpenTimelineEditor }) => {
  const [downloadToast, setDownloadToast] = useState(false);

  const handleDownloadAll = async () => {
    
    
    setDownloadToast(true);
    // Download each clip individually (no ZIP endpoint in canonical API)
    for (const clip of clips) {
      if (clip.videoUrl) {
        const link = document.createElement('a');
        link.href = clip.videoUrl;
        link.download = `${clip.id}.mp4`;
        link.click();
      }
    }
    setTimeout(() => {
      setDownloadToast(false);
    }, 3500);
  };

  return (
    <motion.div
      initial={{ opacity: 0 }}
      animate={{ opacity: 1 }}
      exit={{ opacity: 0 }}
      className="space-y-6 sm:space-y-8 py-2 sm:py-4"
    >
      {/* Mosaic Header Bar */}
      <div className="flex flex-col md:flex-row md:items-center justify-between gap-4 p-4 sm:p-6 rounded-2xl bg-black/60 border border-white/10 backdrop-blur-xl">
        <div className="space-y-1">
          <div className="flex items-center gap-2 flex-wrap">
            <span className="inline-flex items-center gap-1.5 px-2.5 py-0.5 rounded-full bg-emerald-500/20 border border-emerald-500/40 text-emerald-300 font-mono text-[11px] sm:text-xs font-semibold">
              <CheckCircle2 className="w-3.5 h-3.5" />
              AI CLIPPING COMPLETE
            </span>
            <span className="text-stone-400 font-mono text-[11px] sm:text-xs">
              • {clips.length} clip{clips.length !== 1 ? 's' : ''} ready
            </span>
          </div>
          <h3 className="text-lg sm:text-2xl font-bold font-display text-white">
            Vertical 9:16 Clip Results
          </h3>
        </div>

        {/* Global Action controls */}
        <div className="flex items-center gap-2.5 sm:gap-3 flex-wrap">
          <button
            onClick={() => {
              
              onReset();
            }}
            onMouseEnter={() => void 0}
            className="inline-flex items-center gap-2 px-3.5 sm:px-4 py-2 sm:py-2.5 rounded-xl bg-white/5 hover:bg-white/10 text-stone-300 hover:text-white border border-white/10 text-xs font-mono transition-colors active:scale-95"
          >
            <RotateCcw className="w-3.5 h-3.5" />
            <span>Generate Another</span>
          </button>

          {onOpenTimelineEditor && (
            <button
              onClick={() => {
                
                onOpenTimelineEditor();
              }}
              onMouseEnter={() => void 0}
              className="inline-flex items-center gap-2 px-4 sm:px-5 py-2 sm:py-2.5 rounded-xl bg-gradient-to-r from-violet-500/20 to-blue-500/20 hover:from-violet-500/30 hover:to-blue-500/30 text-violet-300 border border-violet-500/40 text-xs font-mono font-bold transition-colors active:scale-95 shadow-[0_0_15px_rgba(34,211,238,0.15)]"
            >
              <Clapperboard className="w-3.5 h-3.5" />
              <span>Open Timeline Editor</span>
            </button>
          )}

          {onPersonalize && (
            <button
              onClick={() => {
                
                onPersonalize();
              }}
              onMouseEnter={() => void 0}
              className="inline-flex items-center gap-2 px-4 sm:px-5 py-2 sm:py-2.5 rounded-xl bg-white/5 hover:bg-white/10 text-stone-300 border border-white/10 text-xs font-mono font-bold transition-colors active:scale-95"
            >
              <Wand2 className="w-3.5 h-3.5" />
              <span>Quick Personalize</span>
            </button>
          )}

          <button
            onClick={handleDownloadAll}
            onMouseEnter={() => void 0}
            className="inline-flex items-center gap-2 px-4 sm:px-5 py-2 sm:py-2.5 rounded-xl bg-white text-black hover:bg-stone-100 font-mono text-xs font-bold uppercase tracking-wider transition-all shadow-[0_0_20px_rgba(255,255,255,0.4)] active:scale-95"
          >
            <Download className="w-3.5 h-3.5" />
            <span>Download All</span>
          </button>
        </div>
      </div>

      {/* Download Toast Notification */}
      <AnimatePresence>
        {downloadToast && (
          <motion.div
            initial={{ opacity: 0, y: -10 }}
            animate={{ opacity: 1, y: 0 }}
            exit={{ opacity: 0, y: -10 }}
            className="p-3.5 rounded-xl bg-emerald-950/80 border border-emerald-500/50 text-emerald-300 font-mono text-xs flex items-center justify-between shadow-[0_0_20px_rgba(16,185,129,0.3)] backdrop-blur-md"
          >
            <div className="flex items-center gap-2">
              <FileArchive className="w-4 h-4 text-emerald-400" />
              <span>Downloading {clips.length} clip{clips.length !== 1 ? 's' : ''} in 9:16 with kinetic subtitles...</span>
            </div>
          </motion.div>
        )}
      </AnimatePresence>

      {/* Dynamic Grid */}
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6 sm:gap-8">
        {clips.map((clip, index) => (
          <VideoResultCard
            key={clip.id}
            clip={clip}
            index={index}
            onPreview={onPreviewClip}
          />
        ))}
      </div>
    </motion.div>
  );
};
