/**
 * NexuX V9.5 — Mode Selector Component
 * 
 * Clean dual-mode selection UI:
 * Mode 1 (Podcast): YouTube URL → viral clips
 * Mode 2 (Creative): Keyword → AI compilation
 */
import React, { useState } from 'react';
import { motion, AnimatePresence } from 'motion/react';
import { Mic, Sparkles, Link as LinkIcon, Search, ArrowRight } from 'lucide-react';

export type NexuXMode = 'podcast' | 'creative';

interface ModeSelectorProps {
  onSelectMode: (mode: NexuXMode) => void;
}

export const ModeSelector: React.FC<ModeSelectorProps> = ({ onSelectMode }) => {
  const [hoveredMode, setHoveredMode] = useState<NexuXMode | null>(null);

  const modes = [
    {
      id: 'podcast' as NexuXMode,
      name: 'Podcast Mode',
      icon: Mic,
      color: 'from-blue-500 to-cyan-500',
      borderColor: 'border-blue-500/40',
      glowColor: 'shadow-blue-500/20',
      description: 'Ambil video YouTube panjang → potong jadi klip viral pendek',
      features: ['Topic segmentation', 'Punchline extraction', 'Hook detection (8 types)', 'Opus Killer scoring'],
      requiresUrl: true,
    },
    {
      id: 'creative' as NexuXMode,
      name: 'AI Creative Mode',
      icon: Sparkles,
      color: 'from-purple-500 to-pink-500',
      borderColor: 'border-purple-500/40',
      glowColor: 'shadow-purple-500/20',
      description: 'Ketik keyword → AI cari, edit, dan compile jadi video viral',
      features: ['Keyword expansion', 'Multi-source search', 'LLM narrative', 'TTS + SFX + auto titles'],
      requiresUrl: false,
    },
  ];

  return (
    <div className="w-full max-w-4xl mx-auto">
      <div className="text-center mb-8">
        <h2 className="text-3xl font-bold text-white mb-2">
          Pilih Mode
        </h2>
        <p className="text-gray-400 text-sm">
          Dua cara untuk bikin konten viral — pilih yang sesuai kebutuhanmu
        </p>
      </div>

      <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
        {modes.map((mode) => {
          const Icon = mode.icon;
          const isHovered = hoveredMode === mode.id;
          
          return (
            <motion.button
              key={mode.id}
              onClick={() => onSelectMode(mode.id)}
              onHoverStart={() => setHoveredMode(mode.id)}
              onHoverEnd={() => setHoveredMode(null)}
              whileHover={{ scale: 1.02, y: -4 }}
              whileTap={{ scale: 0.98 }}
              className={`relative group rounded-2xl border ${mode.borderColor} bg-black/40 backdrop-blur-xl p-8 text-left transition-all duration-300 ${isHovered ? `shadow-2xl ${mode.glowColor}` : ''}`}
            >
              {/* Gradient glow on hover */}
              <div className={`absolute -inset-0.5 bg-gradient-to-r ${mode.color} rounded-2xl blur opacity-0 group-hover:opacity-20 transition-opacity duration-300`} />
              
              <div className="relative">
                {/* Icon */}
                <div className={`inline-flex items-center justify-center w-14 h-14 rounded-xl bg-gradient-to-r ${mode.color} mb-4`}>
                  <Icon className="w-7 h-7 text-white" />
                </div>

                {/* Name */}
                <h3 className="text-xl font-bold text-white mb-2">
                  {mode.name}
                </h3>

                {/* Description */}
                <p className="text-gray-400 text-sm mb-4 leading-relaxed">
                  {mode.description}
                </p>

                {/* Features */}
                <div className="space-y-1.5 mb-6">
                  {mode.features.map((feature, i) => (
                    <div key={i} className="flex items-center gap-2 text-xs text-gray-500">
                      <div className={`w-1 h-1 rounded-full bg-gradient-to-r ${mode.color}`} />
                      {feature}
                    </div>
                  ))}
                </div>

                {/* CTA */}
                <div className={`flex items-center gap-2 text-sm font-medium bg-gradient-to-r ${mode.color} bg-clip-text text-transparent`}>
                  Mulai {mode.name.replace(' Mode', '')}
                  <ArrowRight className="w-4 h-4 text-current" />
                </div>
              </div>
            </motion.button>
          );
        })}
      </div>

      {/* VS indicator */}
      <div className="flex items-center justify-center mt-6">
        <div className="text-xs text-gray-600 font-mono">
          100% LOCAL • ZERO CLOUD COST • BEATS OPUS CLIP
        </div>
      </div>
    </div>
  );
};
