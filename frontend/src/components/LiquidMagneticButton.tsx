import React, { useRef, useState } from 'react';
import { motion, useSpring } from 'motion/react';
import { sound } from '../utils/soundEffects';

interface LiquidMagneticButtonProps {
  children: React.ReactNode;
  onClick?: (e: React.MouseEvent<HTMLButtonElement>) => void;
  className?: string;
  variant?: 'primary' | 'secondary' | 'glass';
  dataCursorText?: string;
  id?: string;
}

export const LiquidMagneticButton: React.FC<LiquidMagneticButtonProps> = ({
  children,
  onClick,
  className = '',
  variant = 'primary',
  dataCursorText,
  id,
}) => {
  const btnRef = useRef<HTMLButtonElement>(null);
  const [isHovered, setIsHovered] = useState(false);
  const [isPressed, setIsPressed] = useState(false);
  const cachedRect = useRef<{ left: number; top: number; width: number; height: number } | null>(null);

  // Fast GPU Spring Config
  const springConfig = { damping: 20, stiffness: 350, mass: 0.1 };
  const smoothX = useSpring(0, springConfig);
  const smoothY = useSpring(0, springConfig);

  const handleMouseEnter = () => {
    if (btnRef.current) {
      const { left, top, width, height } = btnRef.current.getBoundingClientRect();
      cachedRect.current = { left, top, width, height };
    }
    setIsHovered(true);
    sound.playHover();
  };

  const handleMouseMove = (e: React.MouseEvent<HTMLButtonElement>) => {
    if (!cachedRect.current) return;
    const { left, top, width, height } = cachedRect.current;
    const centerX = left + width / 2;
    const centerY = top + height / 2;

    const deltaX = (e.clientX - centerX) * 0.3;
    const deltaY = (e.clientY - centerY) * 0.3;

    smoothX.set(deltaX);
    smoothY.set(deltaY);
  };

  const handleMouseLeave = () => {
    cachedRect.current = null;
    setIsHovered(false);
    smoothX.set(0);
    smoothY.set(0);
  };

  const handleClick = (e: React.MouseEvent<HTMLButtonElement>) => {
    sound.playClick();
    setIsPressed(true);
    setTimeout(() => setIsPressed(false), 150);
    if (onClick) onClick(e);
  };

  // Variants styling
  const variantStyles = {
    primary: 'bg-white text-black font-bold shadow-[0_0_25px_rgba(255,255,255,0.35)] hover:shadow-[0_0_35px_rgba(34,211,238,0.6)] border border-transparent',
    secondary: 'bg-cyan-400 text-black font-bold shadow-[0_0_25px_rgba(34,211,238,0.4)] hover:shadow-[0_0_35px_rgba(34,211,238,0.7)] border border-transparent',
    glass: 'bg-black/60 text-white border border-white/25 hover:border-cyan-400/80 backdrop-blur-md shadow-[0_0_20px_rgba(0,0,0,0.6)] hover:shadow-[0_0_25px_rgba(34,211,238,0.25)]',
  };

  return (
    <div className="relative inline-block select-none">
      {/* Outer Magnetic Spring Wrapper */}
      <motion.div
        style={{
          x: smoothX,
          y: smoothY,
          scale: isPressed ? 0.94 : isHovered ? 1.03 : 1,
        }}
        className="relative will-change-transform"
      >
        {/* Subtle Ambient Plasma Halo Glow on Hover (Zero SVG Filters) */}
        <div
          className={`absolute -inset-1 rounded-full opacity-0 pointer-events-none transition-opacity duration-300 ${
            isHovered ? 'opacity-70' : 'opacity-0'
          } ${
            variant === 'primary'
              ? 'bg-gradient-to-r from-cyan-400/30 via-white/20 to-purple-400/30 blur-md'
              : 'bg-gradient-to-r from-cyan-500/40 via-blue-500/30 to-purple-500/40 blur-md'
          }`}
        />

        {/* The Liquid Magnetic Button Core */}
        <button
          ref={btnRef}
          id={id}
          onClick={handleClick}
          onMouseMove={handleMouseMove}
          onMouseEnter={handleMouseEnter}
          onMouseLeave={handleMouseLeave}
          data-cursor-text={dataCursorText}
          className={`relative z-10 rounded-full px-8 py-4 text-xs font-mono tracking-[0.2em] uppercase transition-all duration-200 flex items-center justify-center gap-3 active:scale-95 ${variantStyles[variant]} ${className}`}
        >
          {/* Ambient Plasma Shimmer */}
          <span className="absolute inset-0 rounded-full bg-gradient-to-r from-transparent via-cyan-400/15 to-transparent opacity-0 hover:opacity-100 transition-opacity duration-300 pointer-events-none" />
          
          <span className="relative z-10 flex items-center gap-2.5">
            {children}
          </span>
        </button>
      </motion.div>
    </div>
  );
};
