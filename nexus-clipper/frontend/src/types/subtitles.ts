export type SubtitleAnimationStyle = 
  | 'word-by-word' 
  | 'line-by-line' 
  | 'bounce-zoom' 
  | 'typewriter-glitch' 
  | 'kinetic-slide' 
  | 'pulse-glow'
  | 'flip-rotate'
  | 'fade-drift';

export type SubtitleVisualPreset = 
  | 'hormozi' 
  | 'mrbeast' 
  | 'minimal-aesthetic' 
  | 'gamer-comic' 
  | 'neon-cyberpunk' 
  | 'ali-abdaal'
  | 'iman-gadzhi'
  | 'anime-impact';

export type SubtitlePosition = 'bottom' | 'center' | 'top';
export type SubtitleFontSize = 'compact' | 'normal' | 'large' | 'huge';
export type SubtitleFontFamily = 'sans' | 'display' | 'mono' | 'serif';
export type SubtitleGlowStyle = 'subtle' | 'intense' | 'outline-clean';

export interface SubtitleWord {
  text: string;
  emoji?: string;
  highlight?: boolean;
  colorType?: 'normal' | 'rage' | 'win' | 'combo' | 'cyan' | 'magenta' | 'yellow' | 'green' | 'gold';
}

export interface SubtitleScriptLine {
  lineText: string;
  words: SubtitleWord[];
  speaker?: string;
  hookScore?: number;
}

export interface SubtitleConfig {
  animationStyle: SubtitleAnimationStyle;
  visualPreset: SubtitleVisualPreset;
  position: SubtitlePosition;
  fontSize: SubtitleFontSize;
  fontFamily: SubtitleFontFamily;
  glowStyle: SubtitleGlowStyle;
  showEmojis: boolean;
  highlightColor: string;
  name: string;
  appliedAt?: number;
}
