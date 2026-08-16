import React, { useState } from 'react';
import { 
  Sparkles, 
  Film, 
  Scissors, 
  Play, 
  Download, 
  Check, 
  Flame, 
  Clock, 
  RefreshCw,
  TrendingUp
} from 'lucide-react';
import { sound } from '../utils/soundEffects';

interface ClipData {
  id: string;
  title: string;
  timestamp: string;
  duration: string;
  viralityScore: number;
  tags: string[];
  aspect: string;
  previewImage: string;
}

const SAMPLE_CLIPS: ClipData[] = [
  {
    id: 'clip-1',
    title: 'The Multi-Planetary Breakthrough Explained',
    timestamp: '14:22 - 15:08',
    duration: '0:46s',
    viralityScore: 98,
    tags: ['#SpaceX', '#FutureTech', '#Shorts'],
    aspect: '9:16 Vertical',
    previewImage: 'https://images.unsplash.com/photo-1517976487502-869fe8ef23ea?q=80&w=800&auto=format&fit=crop',
  },
  {
    id: 'clip-2',
    title: 'Why Classical Computing Hits a Hard Wall',
    timestamp: '28:05 - 28:58',
    duration: '0:53s',
    viralityScore: 94,
    tags: ['#QuantumAI', '#Silicon', '#TechTrend'],
    aspect: '9:16 Vertical',
    previewImage: 'https://images.unsplash.com/photo-1635070041078-e363dbe005cb?q=80&w=800&auto=format&fit=crop',
  },
  {
    id: 'clip-3',
    title: 'Autonomous AI Training Framework',
    timestamp: '42:10 - 42:48',
    duration: '0:38s',
    viralityScore: 96,
    tags: ['#AIResearch', '#DeepLearning', '#Code'],
    aspect: '9:16 Vertical',
    previewImage: 'https://images.unsplash.com/photo-1618005182384-a83a8bd57fbe?q=80&w=800&auto=format&fit=crop',
  },
];

export const RepurposeDemo: React.FC = () => {
  const [videoUrl, setVideoUrl] = useState('https://youtube.com/watch?v=starship-flight-test-orbital');
  const [isProcessing, setIsProcessing] = useState(false);
  const [selectedClip, setSelectedClip] = useState<ClipData>(SAMPLE_CLIPS[0]);
  const [copiedClipId, setCopiedClipId] = useState<string | null>(null);

  const handleSimulateRepurpose = () => {
    sound.playClick();
    setIsProcessing(true);
    setTimeout(() => {
      setIsProcessing(false);
    }, 1000);
  };

  const handleCopy = (id: string) => {
    sound.playClick();
    setCopiedClipId(id);
    setTimeout(() => setCopiedClipId(null), 2000);
  };

  return (
    <section id="engine" className="relative py-24 px-6 sm:px-10 max-w-6xl mx-auto z-10">
      {/* Minimal Header */}
      <div className="text-center max-w-2xl mx-auto space-y-3 mb-12">
        <div className="inline-flex items-center gap-2 px-3 py-1 rounded-full border border-white/10 bg-white/5 text-stone-400 font-mono text-[11px] uppercase tracking-widest">
          <Sparkles className="w-3.5 h-3.5 text-cyan-400" />
          <span>Stage 01 • Neural Pipeline (ニューラルパイプライン)</span>
        </div>
        <h2 className="text-3xl sm:text-5xl font-display font-bold text-white tracking-tight">
          From Long Stream to Viral Shorts
        </h2>
        <p className="text-stone-400 text-sm sm:text-base leading-relaxed">
          NexuX isolates the most engaging highlights, reframes to 9:16, and attaches kinetic subtitles automatically.
        </p>
      </div>

      {/* Engine Console */}
      <div className="bg-stone-950 border border-white/10 rounded-2xl p-6 sm:p-8 spacex-glow-border space-y-8">
        {/* Input Bar */}
        <div className="flex flex-col sm:flex-row items-center gap-3 bg-black p-2 rounded-xl border border-white/10">
          <div className="flex items-center gap-2 px-3 text-stone-400 w-full sm:w-auto">
            <Film className="w-4 h-4 text-cyan-400 shrink-0" />
            <span className="text-xs font-mono text-stone-400 shrink-0">SOURCE:</span>
          </div>
          <input
            type="text"
            value={videoUrl}
            onChange={(e) => setVideoUrl(e.target.value)}
            placeholder="Paste YouTube or video recording URL..."
            className="w-full bg-transparent text-xs sm:text-sm font-mono text-white placeholder-stone-600 focus:outline-none px-2 py-2"
          />
          <button
            onClick={handleSimulateRepurpose}
            disabled={isProcessing}
            data-cursor-text="SLICE"
            className="w-full sm:w-auto shrink-0 px-6 py-2.5 rounded-lg bg-white hover:bg-stone-200 text-black font-mono text-xs font-bold uppercase tracking-wider transition-all flex items-center justify-center gap-2 active:scale-95 disabled:opacity-60"
          >
            {isProcessing ? (
              <>
                <RefreshCw className="w-3.5 h-3.5 animate-spin text-black" />
                <span>Processing...</span>
              </>
            ) : (
              <>
                <Scissors className="w-3.5 h-3.5 text-black" />
                <span>Extract Clips</span>
              </>
            )}
          </button>
        </div>

        {/* 3 Extracted Clips */}
        <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
          {SAMPLE_CLIPS.map((clip) => {
            const isSelected = selectedClip.id === clip.id;
            return (
              <div
                key={clip.id}
                onClick={() => {
                  sound.playClick();
                  setSelectedClip(clip);
                }}
                className={`group rounded-xl border bg-black overflow-hidden transition-all duration-200 cursor-pointer ${
                  isSelected
                    ? 'border-cyan-400/80 shadow-[0_0_20px_rgba(6,182,212,0.2)]'
                    : 'border-white/10 hover:border-white/30'
                }`}
              >
                {/* Thumbnail Container */}
                <div className="relative aspect-[9/12] w-full overflow-hidden bg-stone-900">
                  <img
                    src={clip.previewImage}
                    alt={clip.title}
                    className="w-full h-full object-cover group-hover:scale-105 transition-transform duration-300 opacity-80 group-hover:opacity-100"
                  />
                  <div className="absolute inset-0 bg-gradient-to-t from-black via-black/30 to-transparent" />

                  {/* Virality Score Badge */}
                  <div className="absolute top-3 left-3 px-2.5 py-1 rounded-md bg-black/80 border border-white/20 flex items-center gap-1.5 text-xs font-mono font-bold text-amber-300">
                    <Flame className="w-3.5 h-3.5 fill-amber-400 text-amber-400" />
                    <span>{clip.viralityScore}/100</span>
                  </div>

                  {/* Duration */}
                  <div className="absolute top-3 right-3 px-2 py-1 rounded bg-black/80 border border-white/10 text-[10px] font-mono text-stone-300">
                    {clip.duration}
                  </div>

                  {/* Caption preview */}
                  <div className="absolute bottom-3 inset-x-3 text-center">
                    <div className="inline-block bg-yellow-400 text-black px-2 py-0.5 rounded font-black text-xs uppercase tracking-tight">
                      "THE MOMENT EVERYTHING CHANGED"
                    </div>
                  </div>

                  {/* Hover Play Button */}
                  <div className="absolute inset-0 flex items-center justify-center opacity-0 group-hover:opacity-100 transition-opacity bg-black/40">
                    <div className="w-10 h-10 rounded-full bg-white text-black flex items-center justify-center">
                      <Play className="w-4 h-4 fill-current ml-0.5" />
                    </div>
                  </div>
                </div>

                {/* Details */}
                <div className="p-4 space-y-3">
                  <div className="flex items-center justify-between text-[11px] font-mono text-stone-400">
                    <span className="flex items-center gap-1">
                      <Clock className="w-3 h-3 text-cyan-400" /> {clip.timestamp}
                    </span>
                    <span className="text-cyan-300 font-semibold">{clip.aspect}</span>
                  </div>

                  <h4 className="font-semibold text-sm text-white line-clamp-1 group-hover:text-cyan-300 transition-colors">
                    {clip.title}
                  </h4>

                  <div className="flex flex-wrap gap-1.5">
                    {clip.tags.map((tag, idx) => (
                      <span
                        key={idx}
                        className="text-[10px] font-mono px-2 py-0.5 rounded bg-white/5 border border-white/10 text-stone-400"
                      >
                        {tag}
                      </span>
                    ))}
                  </div>

                  <div className="pt-2 flex items-center justify-between border-t border-white/10">
                    <button
                      onClick={(e) => {
                        e.stopPropagation();
                        handleCopy(clip.id);
                      }}
                      className="text-xs font-mono text-stone-400 hover:text-white flex items-center gap-1 transition-colors"
                    >
                      {copiedClipId === clip.id ? (
                        <>
                          <Check className="w-3.5 h-3.5 text-emerald-400" />
                          <span className="text-emerald-400">Exported</span>
                        </>
                      ) : (
                        <>
                          <Download className="w-3.5 h-3.5" />
                          <span>Export 4K</span>
                        </>
                      )}
                    </button>

                    <span className="text-[11px] font-mono text-emerald-400 flex items-center gap-1">
                      <TrendingUp className="w-3 h-3" /> Viral Hook
                    </span>
                  </div>
                </div>
              </div>
            );
          })}
        </div>
      </div>
    </section>
  );
};
