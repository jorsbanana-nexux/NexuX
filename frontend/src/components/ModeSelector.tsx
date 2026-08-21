import React, { useEffect, useState } from 'react';
import { motion } from 'motion/react';
import { Mic, Sparkles, ArrowRight, Loader2 } from 'lucide-react';
import { v2Api, type NexuXMode, type V2ModeInfo } from '../api/v2Api';
import { sound } from '../utils/soundEffects';

interface ModeSelectorProps {
  onSelect: (mode: NexuXMode) => void;
}

// Offline fallback mirrors engine/mode_router.py so the UI still renders
// when the backend is unreachable; live data replaces it once fetched.
const FALLBACK_MODES: V2ModeInfo[] = [
  {
    mode: 'podcast',
    name: 'Podcast Mode',
    description:
      'Ambil video YouTube panjang (podcast, wawancara, talk show) → potong jadi klip viral pendek. 100% lokal, zero biaya cloud.',
    icon: '🎙️',
    color: 'from-blue-500 to-cyan-500',
    requires_url: true,
    requires_keyword: false,
    features: [
      'Podcast topic segmentation',
      'Punchline extraction',
      'Heat & conflict detection',
      'Hook detection (9 archetypes)',
      'Opus Killer scoring (8 dimensions)',
      'Face tracking + auto reframe',
    ],
  },
  {
    mode: 'creative',
    name: 'AI Creative Mode',
    description:
      'Satu keyword → AI mencari momen terbaik dari banyak video, menulis narasi, dan mengompilasi satu video viral dengan TTS + SFX.',
    icon: '✨',
    color: 'from-purple-500 to-pink-500',
    requires_url: false,
    requires_keyword: true,
    features: [
      'Keyword expansion (15+ terms)',
      'Multi-source moment search',
      'LLM narrative generation',
      'TTS voice-over (ID + EN)',
      'Auto titles + hashtags',
    ],
  },
];

const MODE_ICONS: Record<string, React.ReactNode> = {
  podcast: <Mic className="w-7 h-7" />,
  creative: <Sparkles className="w-7 h-7" />,
};

export const ModeSelector: React.FC<ModeSelectorProps> = ({ onSelect }) => {
  const [modes, setModes] = useState<V2ModeInfo[]>(FALLBACK_MODES);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    v2Api
      .modes()
      .then((res) => {
        if (Array.isArray(res) && res.length > 0) setModes(res);
      })
      .catch(() => {
        // Backend offline → fallback catalog stays visible.
      })
      .finally(() => setLoading(false));
  }, []);

  const handleSelect = (mode: NexuXMode) => {
    sound.playClick();
    onSelect(mode);
  };

  return (
    <div className="grid grid-cols-1 md:grid-cols-2 gap-6 w-full max-w-5xl mx-auto">
      {modes.map((mode, idx) => (
        <motion.button
          key={mode.mode}
          type="button"
          initial={{ opacity: 0, y: 24 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ delay: idx * 0.12, duration: 0.5, ease: 'easeOut' }}
          whileHover={{ y: -4 }}
          whileTap={{ scale: 0.98 }}
          onClick={() => handleSelect(mode.mode as NexuXMode)}
          className="group relative text-left rounded-2xl border border-white/10 bg-white/[0.03] backdrop-blur-xl p-8 overflow-hidden transition-colors hover:border-cyan-400/40 focus:outline-none focus-visible:ring-2 focus-visible:ring-cyan-400/60"
        >
          {/* Gradient glow on hover */}
          <div
            className={`absolute inset-0 opacity-0 group-hover:opacity-10 transition-opacity duration-500 bg-gradient-to-br ${mode.color}`}
          />

          <div className="relative z-10">
            <div
              className={`inline-flex items-center justify-center w-14 h-14 rounded-xl bg-gradient-to-br ${mode.color} text-white mb-5 shadow-lg`}
            >
              {MODE_ICONS[mode.mode] ?? <span className="text-2xl">{mode.icon}</span>}
            </div>

            <h3 className="text-xl font-bold text-white mb-2 flex items-center gap-2">
              {mode.name}
              <ArrowRight className="w-4 h-4 text-cyan-400 opacity-0 -translate-x-1 group-hover:opacity-100 group-hover:translate-x-0 transition-all" />
            </h3>

            <p className="text-sm text-stone-400 leading-relaxed mb-5">
              {mode.description}
            </p>

            <ul className="space-y-1.5">
              {mode.features.slice(0, 4).map((feature) => (
                <li
                  key={feature}
                  className="text-xs text-stone-500 flex items-center gap-2"
                >
                  <span className="w-1 h-1 rounded-full bg-cyan-400/70 shrink-0" />
                  {feature}
                </li>
              ))}
            </ul>
          </div>
        </motion.button>
      ))}

      {loading && (
        <div className="col-span-full flex justify-center py-2">
          <Loader2 className="w-4 h-4 text-stone-600 animate-spin" />
        </div>
      )}
    </div>
  );
};
