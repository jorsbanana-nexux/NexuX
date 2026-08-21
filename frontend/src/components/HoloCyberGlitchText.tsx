import React from 'react';

interface HoloCyberGlitchTextProps {
  text: string;
  className?: string;
  as?: 'h1' | 'h2' | 'h3' | 'span' | 'div';
}

export const HoloCyberGlitchText: React.FC<HoloCyberGlitchTextProps> = ({
  text,
  className = '',
  as: Component = 'span',
}) => {
  return (
    <Component className={`relative inline-block select-none group ${className}`}>
      {/* 1. Base Crisp Text Layer */}
      <span className="relative z-10 block text-white">
        {text}
      </span>

      {/* 2. Holographic Scanline Overlay Pattern */}
      <span
        aria-hidden="true"
        className="absolute inset-0 z-20 pointer-events-none opacity-30 mix-blend-overlay bg-[linear-gradient(rgba(34,211,238,0.25)_50%,transparent_50%)] bg-[length:100%_4px]"
      />

      {/* 3. Cybernetic Chromatic Aberration: Cyan Layer (GPU Composited) */}
      <span
        aria-hidden="true"
        className="absolute inset-0 z-0 pointer-events-none text-cyan-400 font-inherit select-none opacity-0 group-hover:opacity-80 group-hover:-translate-x-0.5 transition-all duration-150"
        style={{
          textShadow: '0 0 12px rgba(34, 211, 238, 0.8)',
        }}
      >
        {text}
      </span>

      {/* 4. Cybernetic Chromatic Aberration: Magenta Layer (GPU Composited) */}
      <span
        aria-hidden="true"
        className="absolute inset-0 z-0 pointer-events-none text-fuchsia-500 font-inherit select-none opacity-0 group-hover:opacity-80 group-hover:translate-x-0.5 transition-all duration-150"
        style={{
          textShadow: '0 0 12px rgba(217, 70, 239, 0.8)',
        }}
      >
        {text}
      </span>

      {/* 5. Hologram Glow Halo Shimmer */}
      <span
        aria-hidden="true"
        className="absolute -inset-1 z-0 pointer-events-none opacity-20 blur-md bg-gradient-to-r from-cyan-500/20 via-blue-500/20 to-purple-500/20 group-hover:opacity-50 transition-opacity duration-300 rounded-lg"
      />
    </Component>
  );
};
