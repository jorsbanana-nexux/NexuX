import React, { useState, useEffect } from 'react';
import { motion, AnimatePresence } from 'motion/react';
import { Menu, X, ArrowUpRight, Cpu, Sparkles } from 'lucide-react';
import { sound } from '../utils/soundEffects';
import { MagneticElement } from './MagneticElement';

interface NavbarProps {
  onOpenTryModal?: () => void;
}

export const Navbar: React.FC<NavbarProps> = ({ onOpenTryModal }) => {
  const [isScrolled, setIsScrolled] = useState(false);
  const [mobileMenuOpen, setMobileMenuOpen] = useState(false);

  useEffect(() => {
    let ticking = false;
    const handleScroll = () => {
      if (!ticking) {
        window.requestAnimationFrame(() => {
          setIsScrolled(window.scrollY > 20);
          ticking = false;
        });
        ticking = true;
      }
    };

    window.addEventListener('scroll', handleScroll, { passive: true });
    return () => window.removeEventListener('scroll', handleScroll);
  }, []);

  return (
    <>
      <header
        id="navbar"
        className={`fixed top-0 left-0 right-0 z-50 transition-all duration-300 ${
          isScrolled
            ? 'hud-glass-panel py-3.5'
            : 'bg-transparent py-5 sm:py-6 border-b border-transparent'
        }`}
      >
        <div className="max-w-7xl mx-auto px-6 sm:px-10 flex items-center justify-between">
          {/* Minimalist Logo with Magnetic Hover & Japanese brand typography */}
          <MagneticElement strength={0.3} radius={70}>
            <a
              href="#"
              id="nav-logo"
              onMouseEnter={() => sound.playHover()}
              onClick={() => sound.playClick()}
              className="group flex items-center gap-3 active:scale-98 transition-transform"
              data-cursor-text="NEXUX"
            >
              <div className="w-8 h-8 rounded-lg bg-stone-900 border border-white/20 text-white flex items-center justify-center font-black text-sm group-hover:border-cyan-400 group-hover:bg-cyan-950/40 group-hover:text-cyan-300 transition-all shadow-[0_0_15px_rgba(255,255,255,0.05)] group-hover:shadow-[0_0_20px_rgba(34,211,238,0.4)]">
                <Cpu className="w-4 h-4" />
              </div>
              <div className="flex items-baseline gap-2">
                <span className="font-display tracking-[0.25em] font-extrabold text-lg text-white group-hover:text-glow-cyan transition-all">
                  NEXU<span className="text-cyan-400">X</span>
                </span>
                <span className="font-jp text-[10px] font-medium tracking-widest text-stone-400">
                  ネクサス
                </span>
              </div>
            </a>
          </MagneticElement>

          {/* Desktop Navigation Links with Magnetic Hover */}
          <nav className="hidden md:flex items-center gap-7 text-xs uppercase tracking-[0.2em] font-mono text-stone-400">
            <MagneticElement strength={0.4} radius={50}>
              <a
                href="#workspace-console"
                onMouseEnter={() => sound.playHover()}
                onClick={() => sound.playClick()}
                className="hover:text-cyan-300 transition-colors py-1 px-2.5 rounded-lg hover:bg-white/5"
              >
                Cockpit
              </a>
            </MagneticElement>
            <MagneticElement strength={0.4} radius={50}>
              <a
                href="#subtitle-engine"
                onMouseEnter={() => sound.playHover()}
                onClick={() => sound.playClick()}
                className="hover:text-cyan-300 transition-colors py-1 px-2.5 rounded-lg hover:bg-white/5"
              >
                Subtitles
              </a>
            </MagneticElement>
            <MagneticElement strength={0.4} radius={50}>
              <a
                href="#capabilities"
                onMouseEnter={() => sound.playHover()}
                onClick={() => sound.playClick()}
                className="hover:text-cyan-300 transition-colors py-1 px-2.5 rounded-lg hover:bg-white/5"
              >
                Architecture
              </a>
            </MagneticElement>
          </nav>

          {/* Right Action: Launch Studio with Magnetic Pull & Neon Glow */}
          <div className="hidden sm:flex items-center gap-4">
            <MagneticElement strength={0.35} radius={75}>
              <button
                id="try-now-btn"
                onClick={() => {
                  sound.playClick();
                  if (onOpenTryModal) onOpenTryModal();
                }}
                onMouseEnter={() => sound.playHover()}
                data-cursor-text="LAUNCH"
                className="px-5 py-2 rounded-full border border-cyan-400/40 hover:border-cyan-300 bg-cyan-950/30 hover:bg-cyan-900/40 text-cyan-200 hover:text-white font-mono text-xs font-semibold uppercase tracking-[0.2em] flex items-center gap-2 transition-all active:scale-95 shadow-[0_0_15px_rgba(34,211,238,0.15)] hover:shadow-[0_0_25px_rgba(34,211,238,0.4)]"
              >
                <Sparkles className="w-3 h-3 text-cyan-400" />
                <span>Launch Studio</span>
                <ArrowUpRight className="w-3.5 h-3.5 text-cyan-400" />
              </button>
            </MagneticElement>
          </div>

          {/* Mobile Hamburger Button */}
          <button
            id="mobile-menu-toggle"
            onClick={() => {
              sound.playClick();
              setMobileMenuOpen(!mobileMenuOpen);
            }}
            className="md:hidden p-2 text-stone-400 hover:text-white focus:outline-none"
            aria-label="Toggle menu"
          >
            {mobileMenuOpen ? <X className="w-6 h-6" /> : <Menu className="w-6 h-6" />}
          </button>
        </div>
      </header>

      {/* Mobile Drawer Menu */}
      <AnimatePresence>
        {mobileMenuOpen && (
          <motion.div
            initial={{ opacity: 0, y: -10 }}
            animate={{ opacity: 1, y: 0 }}
            exit={{ opacity: 0, y: -10 }}
            transition={{ duration: 0.2 }}
            className="fixed inset-0 z-40 bg-black/95 backdrop-blur-2xl pt-24 px-6 md:hidden flex flex-col justify-between pb-10"
          >
            <div className="space-y-4 text-center">
              <a
                href="#workspace-console"
                onClick={() => {
                  sound.playClick();
                  setMobileMenuOpen(false);
                }}
                className="block text-base uppercase tracking-widest font-mono text-stone-300 hover:text-cyan-300 py-3 border-b border-white/10"
              >
                AI Cockpit
              </a>
              <a
                href="#subtitle-engine"
                onClick={() => {
                  sound.playClick();
                  setMobileMenuOpen(false);
                }}
                className="block text-base uppercase tracking-widest font-mono text-stone-300 hover:text-cyan-300 py-3 border-b border-white/10"
              >
                Subtitle Engine
              </a>
              <a
                href="#capabilities"
                onClick={() => {
                  sound.playClick();
                  setMobileMenuOpen(false);
                }}
                className="block text-base uppercase tracking-widest font-mono text-stone-300 hover:text-cyan-300 py-3 border-b border-white/10"
              >
                Architecture
              </a>
            </div>

            <div className="w-full">
              <button
                onClick={() => {
                  sound.playClick();
                  setMobileMenuOpen(false);
                  if (onOpenTryModal) onOpenTryModal();
                }}
                className="w-full py-3.5 rounded-full bg-white text-black font-mono font-bold uppercase tracking-widest text-xs flex items-center justify-center gap-2 shadow-[0_0_25px_rgba(255,255,255,0.4)]"
              >
                <Sparkles className="w-4 h-4 text-black" />
                <span>Launch Studio (スタジオ起動)</span>
              </button>
            </div>
          </motion.div>
        )}
      </AnimatePresence>
    </>
  );
};
