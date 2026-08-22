import React from 'react';
import { motion, AnimatePresence } from 'motion/react';
import { 
  SubtitleConfig, 
  SubtitleScriptLine, 
  SubtitleWord, 
  SubtitleAnimationStyle, 
  SubtitleVisualPreset 
} from '../types/subtitles';

interface LiveSubtitleRendererProps {
  currentLine: SubtitleScriptLine;
  wordIndex: number;
  lineIndex: number;
  config: SubtitleConfig;
  className?: string;
}

export const LiveSubtitleRenderer: React.FC<LiveSubtitleRendererProps> = ({
  currentLine,
  wordIndex,
  lineIndex,
  config,
  className = '',
}) => {
  const {
    animationStyle,
    visualPreset,
    fontSize,
    fontFamily,
    glowStyle,
    highlightColor,
    showEmojis,
    position,
  } = config;

  // Font size calculation with enhanced readability
  const getFontSizeClass = () => {
    switch (fontSize) {
      case 'compact':
        return 'text-sm sm:text-base font-bold';
      case 'normal':
        return 'text-base sm:text-lg font-extrabold';
      case 'huge':
        return 'text-2xl sm:text-4xl font-black';
      case 'large':
      default:
        return 'text-lg sm:text-2xl font-black';
    }
  };

  // Font family calculation
  const getFontFamilyClass = () => {
    switch (fontFamily) {
      case 'display':
        return 'font-display font-black tracking-tight uppercase';
      case 'mono':
        return 'font-mono font-bold tracking-normal uppercase';
      case 'serif':
        return 'font-serif font-bold italic tracking-wide';
      case 'sans':
      default:
        return 'font-sans font-extrabold tracking-tight uppercase';
    }
  };

  // Glow filter calculation
  const getGlowStyle = (active: boolean, color: string) => {
    if (!active) return undefined;
    if (glowStyle === 'subtle') {
      return { filter: `drop-shadow(0 0 10px ${color}80)` };
    }
    if (glowStyle === 'outline-clean') {
      return { filter: `drop-shadow(0 2px 4px rgba(0,0,0,0.9))` };
    }
    // intense
    return { filter: `drop-shadow(0 0 20px ${color}) drop-shadow(0 4px 10px rgba(0,0,0,0.8))` };
  };

  // Animation variants per animationStyle
  const getWordAnimation = (isActive: boolean, idx: number) => {
    if (!isActive) {
      return {
        scale: 1,
        y: 0,
        x: 0,
        rotateX: 0,
        rotate: 0,
        opacity: idx < wordIndex ? 0.95 : 0.65,
        filter: 'blur(0px)',
      };
    }

    switch (animationStyle) {
      case 'bounce-zoom':
        return {
          scale: [0.8, 1.4, 1.15],
          y: [12, -8, 0],
          rotate: [0, -4, 4, 0],
          opacity: 1,
        };
      case 'typewriter-glitch':
        return {
          scale: [1, 1.25, 1.15],
          x: [-4, 4, -2, 0],
          opacity: [0.2, 1, 0.8, 1],
        };
      case 'kinetic-slide':
        return {
          y: [20, -3, 0],
          scale: [0.9, 1.2, 1.12],
          opacity: [0, 1],
        };
      case 'pulse-glow':
        return {
          scale: [1, 1.25, 1.15],
          opacity: 1,
        };
      case 'flip-rotate':
        return {
          rotateX: [90, -15, 0],
          scale: [0.85, 1.25, 1.15],
          opacity: [0, 1],
        };
      case 'fade-drift':
        return {
          y: [10, 0],
          filter: ['blur(4px)', 'blur(0px)'],
          scale: 1.15,
          opacity: 1,
        };
      case 'word-by-word':
      default:
        return {
          scale: 1.18,
          y: -2,
          opacity: 1,
        };
    }
  };

  // Transition settings per animation style
  const getTransition = () => {
    switch (animationStyle) {
      case 'bounce-zoom':
        return { duration: 0.22, ease: [0.34, 1.56, 0.64, 1] as [number, number, number, number] };
      case 'typewriter-glitch':
        return { duration: 0.15, ease: 'linear' };
      case 'kinetic-slide':
        return { duration: 0.2, ease: 'easeOut' };
      case 'pulse-glow':
        return { duration: 0.25, ease: 'easeInOut' };
      case 'flip-rotate':
        return { duration: 0.25, ease: 'easeOut' };
      case 'fade-drift':
        return { duration: 0.28, ease: 'easeOut' };
      case 'word-by-word':
      default:
        return { duration: 0.16, ease: 'easeOut' };
    }
  };

  // Render Line-by-Line Mode
  if (animationStyle === 'line-by-line') {
    return (
      <div className={`w-full flex items-center justify-center ${className}`}>
        <motion.div
          key={`line-${lineIndex}-${visualPreset}`}
          initial={{ opacity: 0, y: 14, scale: 0.94 }}
          animate={{ opacity: 1, y: 0, scale: 1 }}
          exit={{ opacity: 0, y: -14, scale: 0.94 }}
          transition={{ duration: 0.22, ease: 'easeOut' }}
          className={`text-center px-4 py-2 rounded-2xl max-w-full ${getFontSizeClass()} ${getFontFamilyClass()}`}
        >
          {/* Preset Styles in Line-by-Line Mode */}
          {visualPreset === 'hormozi' && (
            <div 
              style={{ backgroundColor: highlightColor, color: '#000000', ...getGlowStyle(true, highlightColor) }}
              className="inline-block px-4 py-2 rounded-xl font-black shadow-2xl leading-tight border border-yellow-200"
            >
              {currentLine.lineText} {showEmojis && '⚡'}
            </div>
          )}

          {visualPreset === 'mrbeast' && (
            <div 
              style={{ ...getGlowStyle(true, highlightColor) }}
              className="inline-block px-4 py-2 rounded-xl bg-gradient-to-r from-violet-400 via-amber-300 to-rose-400 text-black font-black -rotate-2 border-2 border-black shadow-2xl leading-tight"
            >
              {currentLine.lineText} {showEmojis && '🔥'}
            </div>
          )}

          {visualPreset === 'minimal-aesthetic' && (
            <div className="inline-block px-5 py-2.5 rounded-2xl bg-black/80 backdrop-blur-xl border border-white/30 text-white font-medium shadow-2xl leading-tight">
              <span className="text-violet-300 font-bold">{currentLine.lineText}</span>
            </div>
          )}

          {visualPreset === 'gamer-comic' && (
            <div 
              style={{ ...getGlowStyle(true, '#ef4444') }}
              className="inline-block px-4 py-2 rounded-xl bg-gradient-to-r from-red-600 via-amber-500 to-emerald-500 text-white font-black border-2 border-white shadow-2xl leading-tight"
            >
              {currentLine.lineText} {showEmojis && '🏆'}
            </div>
          )}

          {visualPreset === 'neon-cyberpunk' && (
            <div 
              style={{ ...getGlowStyle(true, '#06b6d4') }}
              className="inline-block px-4 py-2 rounded-xl bg-black/90 border border-violet-400 text-violet-300 font-mono font-bold shadow-2xl leading-tight tracking-wider"
            >
              [ {currentLine.lineText} ]
            </div>
          )}

          {visualPreset === 'ali-abdaal' && (
            <div 
              style={{ backgroundColor: highlightColor, color: '#000000', ...getGlowStyle(true, highlightColor) }}
              className="inline-block px-4 py-2 rounded-lg font-bold shadow-xl leading-tight"
            >
              {currentLine.lineText}
            </div>
          )}

          {visualPreset === 'iman-gadzhi' && (
            <div 
              style={{ ...getGlowStyle(true, '#fef08a') }}
              className="inline-block px-5 py-2.5 rounded-2xl bg-black/75 backdrop-blur-md border border-yellow-200/40 text-yellow-200 font-serif italic font-bold shadow-2xl leading-tight"
            >
              "{currentLine.lineText}"
            </div>
          )}

          {visualPreset === 'anime-impact' && (
            <div 
              style={{ ...getGlowStyle(true, '#f97316') }}
              className="inline-block px-4 py-2 rounded-xl bg-gradient-to-r from-orange-500 to-amber-400 text-black font-black border border-white/60 shadow-2xl leading-tight"
            >
              {currentLine.lineText} {showEmojis && '💥'}
            </div>
          )}
        </motion.div>
      </div>
    );
  }

  // Render Word-by-Word Interactive Motion Modes
  return (
    <div className={`w-full flex items-center justify-center ${className}`}>
      <motion.div
        key={`phrase-${lineIndex}-${visualPreset}-${animationStyle}`}
        initial={{ opacity: 0, scale: 0.97 }}
        animate={{ opacity: 1, scale: 1 }}
        exit={{ opacity: 0, scale: 0.97 }}
        transition={{ duration: 0.15 }}
        className={`inline-flex flex-wrap items-center justify-center gap-x-2 gap-y-2.5 text-center select-none ${getFontSizeClass()} ${getFontFamilyClass()} ${
          visualPreset === 'mrbeast' ? '-rotate-1' : ''
        }`}
      >
        {currentLine.words.map((w: SubtitleWord, idx: number) => {
          const isActive = idx === wordIndex;
          const isPast = idx < wordIndex;

          return (
            <motion.div
              key={`${w.text}-${idx}`}
              animate={getWordAnimation(isActive, idx)}
              transition={getTransition() as any}
              className="relative inline-flex flex-col items-center justify-center will-change-transform"
              style={{ perspective: 800 }}
            >
              {/* Floating 3D Emoji on top of active or past keywords */}
              {showEmojis && w.emoji && (isActive || (isPast && w.highlight)) && (
                <motion.span
                  initial={{ scale: 0, y: 10 }}
                  animate={{ scale: isActive ? [1, 1.35, 1.15] : 1, y: 0 }}
                  transition={{ duration: 0.2 }}
                  className="absolute -top-7 text-2xl filter drop-shadow-[0_4px_8px_rgba(0,0,0,0.9)] z-20 pointer-events-none"
                >
                  {w.emoji}
                </motion.span>
              )}

              {/* VISUAL PRESET 1: ALEX HORMOZI ($100M Leads) */}
              {visualPreset === 'hormozi' && (
                <span
                  style={
                    isActive
                      ? {
                          backgroundColor: highlightColor,
                          color: '#000000',
                          ...getGlowStyle(true, highlightColor),
                        }
                      : {
                          color: isPast ? '#ffffff' : '#f5f5f4',
                          textShadow: '0 2px 8px rgba(0,0,0,0.95), 0 0 2px #000000',
                        }
                  }
                  className={`px-2.5 py-1 rounded-xl transition-all duration-150 font-black leading-none ${
                    isActive
                      ? 'shadow-2xl border border-yellow-200 z-10'
                      : 'border border-transparent'
                  }`}
                >
                  {w.text}
                </span>
              )}

              {/* VISUAL PRESET 2: MRBEAST HYPER-RETENTION */}
              {visualPreset === 'mrbeast' && (
                <span
                  style={
                    isActive
                      ? {
                          backgroundColor: highlightColor,
                          color: '#000000',
                          ...getGlowStyle(true, highlightColor),
                        }
                      : {
                          color: '#ffffff',
                          textShadow: '0 2px 10px rgba(0,0,0,0.95), 0 0 3px #000000',
                        }
                  }
                  className={`px-2.5 py-1 rounded-xl font-black leading-none transition-all duration-150 ${
                    isActive
                      ? 'border-2 border-black shadow-2xl z-10 scale-105'
                      : ''
                  }`}
                >
                  {w.text}
                </span>
              )}

              {/* VISUAL PRESET 3: MINIMALIST AESTHETIC */}
              {visualPreset === 'minimal-aesthetic' && (
                <span
                  style={
                    isActive
                      ? {
                          color: highlightColor,
                          ...getGlowStyle(true, highlightColor),
                        }
                      : {
                          color: isPast ? '#ffffff' : '#a8a29e',
                        }
                  }
                  className={`px-2 py-0.5 rounded-lg transition-all duration-200 font-medium ${
                    isActive
                      ? 'font-bold underline underline-offset-4 decoration-2 decoration-violet-400 bg-black/60 backdrop-blur-md px-2.5 border border-white/20'
                      : 'bg-black/30 backdrop-blur-sm'
                  }`}
                >
                  {w.text}
                </span>
              )}

              {/* VISUAL PRESET 4: GAMER / COMIC BOOK */}
              {visualPreset === 'gamer-comic' && (() => {
                let dynamicColor = '#ffffff';
                let dynamicBg = 'transparent';

                if (isActive) {
                  if (w.colorType === 'rage') {
                    dynamicColor = '#fee2e2';
                    dynamicBg = '#ef4444';
                  } else if (w.colorType === 'win') {
                    dynamicColor = '#000000';
                    dynamicBg = '#10b981';
                  } else if (w.colorType === 'cyan') {
                    dynamicColor = '#000000';
                    dynamicBg = '#06b6d4';
                  } else {
                    dynamicColor = '#000000';
                    dynamicBg = highlightColor;
                  }
                }

                return (
                  <span
                    style={
                      isActive
                        ? {
                            backgroundColor: dynamicBg,
                            color: dynamicColor,
                            ...getGlowStyle(true, dynamicBg),
                          }
                        : {
                            color: '#ffffff',
                            textShadow: '0 2px 8px rgba(0,0,0,0.95), 0 0 3px #000000',
                          }
                    }
                    className={`px-2.5 py-1 rounded-lg font-black leading-none transition-all duration-150 ${
                      isActive ? 'border-2 border-white shadow-2xl z-10' : ''
                    }`}
                  >
                    {w.text}
                  </span>
                );
              })()}

              {/* VISUAL PRESET 5: NEON CYBERPUNK 2077 */}
              {visualPreset === 'neon-cyberpunk' && (
                <span
                  style={
                    isActive
                      ? {
                          color: '#f0abfc',
                          backgroundColor: 'rgba(0,0,0,0.85)',
                          borderColor: '#06b6d4',
                          ...getGlowStyle(true, '#e879f9'),
                        }
                      : {
                          color: isPast ? '#67e8f9' : '#78716c',
                        }
                  }
                  className={`px-2 py-0.5 rounded-md font-mono font-bold leading-none border transition-all duration-150 ${
                    isActive ? 'border-violet-400 scale-105 z-10' : 'border-white/10 bg-black/40'
                  }`}
                >
                  {isActive ? `[${w.text}]` : w.text}
                </span>
              )}

              {/* VISUAL PRESET 6: ALI ABDAAL NOTION HIGHLIGHTER */}
              {visualPreset === 'ali-abdaal' && (
                <span
                  style={
                    isActive
                      ? {
                          backgroundColor: highlightColor,
                          color: '#000000',
                          ...getGlowStyle(true, highlightColor),
                        }
                      : {
                          color: '#ffffff',
                          textShadow: '0 2px 6px rgba(0,0,0,0.9)',
                        }
                  }
                  className={`px-2 py-0.5 rounded-md font-bold leading-none transition-all duration-150 ${
                    isActive ? 'shadow-xl z-10' : ''
                  }`}
                >
                  {w.text}
                </span>
              )}

              {/* VISUAL PRESET 7: IMAN GADZHI LUXURY EDITORIAL */}
              {visualPreset === 'iman-gadzhi' && (
                <span
                  style={
                    isActive
                      ? {
                          color: '#fef08a',
                          backgroundColor: 'rgba(0,0,0,0.75)',
                          ...getGlowStyle(true, '#fef08a'),
                        }
                      : {
                          color: isPast ? '#ffffff' : '#d6d3d1',
                          textShadow: '0 2px 6px rgba(0,0,0,0.9)',
                        }
                  }
                  className={`px-2.5 py-0.5 rounded-xl font-serif italic font-bold leading-none transition-all duration-200 ${
                    isActive ? 'border border-yellow-200/50 shadow-2xl z-10' : ''
                  }`}
                >
                  {w.text}
                </span>
              )}

              {/* VISUAL PRESET 8: ANIME SPEED IMPACT */}
              {visualPreset === 'anime-impact' && (
                <span
                  style={
                    isActive
                      ? {
                          background: 'linear-gradient(135deg, #f97316, #fbbf24)',
                          color: '#000000',
                          ...getGlowStyle(true, '#f97316'),
                        }
                      : {
                          color: '#ffffff',
                          textShadow: '0 2px 8px rgba(0,0,0,0.95), 0 0 3px #000000',
                        }
                  }
                  className={`px-2.5 py-1 rounded-xl font-black leading-none transition-all duration-150 ${
                    isActive ? 'border border-white shadow-2xl z-10' : ''
                  }`}
                >
                  {w.text}
                </span>
              )}
            </motion.div>
          );
        })}
      </motion.div>
    </div>
  );
};
