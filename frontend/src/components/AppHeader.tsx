/**
 * NexuX V9.7 — AppHeader
 * Clean, SpaceX-style fixed header. One accent color, generous whitespace,
 * zero decoration. Contains: brand, primary nav, Settings entry (top-right).
 */
import React from 'react';
import { Settings, Zap } from 'lucide-react';

interface AppHeaderProps {
  currentView: 'studio' | 'compare' | 'settings';
  onNavigate: (view: 'studio' | 'compare' | 'settings') => void;
  healthOk: boolean | null;
}

const NAV_ITEMS: { id: 'studio' | 'compare'; label: string }[] = [
  { id: 'studio', label: 'Studio' },
  { id: 'compare', label: 'Compare' },
];

export function AppHeader({ currentView, onNavigate, healthOk }: AppHeaderProps) {
  return (
    <header className="fixed top-0 left-0 right-0 z-50 bg-[#0a0a0b]/90 backdrop-blur-md border-b border-white/[0.08]">
      <div className="max-w-7xl mx-auto px-4 sm:px-6 h-16 flex items-center justify-between">
        {/* Brand */}
        <button
          onClick={() => onNavigate('studio')}
          className="flex items-center gap-2.5 group"
          aria-label="NexuX home"
        >
          <div className="w-8 h-8 rounded-lg bg-violet-600 flex items-center justify-center">
            <Zap className="w-4 h-4 text-white" strokeWidth={2.5} />
          </div>
          <span className="font-display font-bold text-lg tracking-tight text-white">
            NexuX
          </span>
          <span className="hidden sm:inline-flex items-center px-2 py-0.5 rounded-full border border-white/10 text-[10px] font-medium text-zinc-400 uppercase tracking-widest">
            v9.7
          </span>
        </button>

        {/* Primary navigation */}
        <nav className="flex items-center gap-1" aria-label="Primary">
          {NAV_ITEMS.map((item) => (
            <button
              key={item.id}
              onClick={() => onNavigate(item.id)}
              className={`px-3 sm:px-4 py-2 rounded-lg text-sm font-medium transition-colors ${
                currentView === item.id
                  ? 'text-white bg-white/[0.06]'
                  : 'text-zinc-400 hover:text-white hover:bg-white/[0.04]'
              }`}
              aria-current={currentView === item.id ? 'page' : undefined}
            >
              {item.label}
            </button>
          ))}

          {/* Health dot */}
          {healthOk !== null && (
            <span
              className="hidden md:flex items-center gap-1.5 ml-2 mr-1 text-xs text-zinc-500"
              title={healthOk ? 'Backend connected' : 'Backend unreachable'}
            >
              <span
                className={`w-1.5 h-1.5 rounded-full ${
                  healthOk ? 'bg-emerald-400' : 'bg-red-400'
                }`}
              />
              {healthOk ? 'Online' : 'Offline'}
            </span>
          )}

          {/* Settings — top right, as specified */}
          <button
            onClick={() => onNavigate('settings')}
            className={`ml-1 p-2 rounded-lg transition-colors ${
              currentView === 'settings'
                ? 'text-white bg-white/[0.06]'
                : 'text-zinc-400 hover:text-white hover:bg-white/[0.04]'
            }`}
            aria-label="Settings"
            title="Settings"
          >
            <Settings className="w-[18px] h-[18px]" />
          </button>
        </nav>
      </div>
    </header>
  );
}

export default AppHeader;
