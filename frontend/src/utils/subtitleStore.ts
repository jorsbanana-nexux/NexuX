import { SubtitleConfig } from '../types/subtitles';

export const DEFAULT_SUBTITLE_CONFIG: SubtitleConfig = {
  animationStyle: 'word-by-word',
  visualPreset: 'hormozi',
  position: 'bottom',
  fontSize: 'large',
  fontFamily: 'sans',
  glowStyle: 'intense',
  showEmojis: true,
  highlightColor: '#facc15',
  name: 'Alex Hormozi Viral ($100M Leads)',
  appliedAt: Date.now(),
};

type Listener = (config: SubtitleConfig) => void;
let currentConfig: SubtitleConfig = { ...DEFAULT_SUBTITLE_CONFIG };
const listeners = new Set<Listener>();

export const subtitleStore = {
  get: (): SubtitleConfig => currentConfig,
  set: (newConfig: Partial<SubtitleConfig>) => {
    currentConfig = { ...currentConfig, ...newConfig, appliedAt: Date.now() };
    listeners.forEach((listener) => listener(currentConfig));
  },
  subscribe: (listener: Listener) => {
    listeners.add(listener);
    return () => {
      listeners.delete(listener);
    };
  },
};
