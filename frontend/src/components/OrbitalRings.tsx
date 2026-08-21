import React from 'react';
import { motion } from 'motion/react';

interface OrbitalRingsProps {
  size?: number;
  className?: string;
  showSatellites?: boolean;
  pulseCenter?: boolean;
}

export const OrbitalRings: React.FC<OrbitalRingsProps> = ({
  size = 180,
  className = '',
  showSatellites = true,
  pulseCenter = true,
}) => {
  return (
    <div
      className={`relative flex items-center justify-center pointer-events-none select-none ${className}`}
      style={{ width: size, height: size }}
    >
      {/* Outer Ring 1 - Slow Clockwise Rotation */}
      <motion.div
        animate={{ rotate: 360 }}
        transition={{ duration: 32, repeat: Infinity, ease: 'linear' }}
        className="absolute inset-0 rounded-full border border-dashed border-cyan-500/25"
      >
        {showSatellites && (
          <div className="absolute -top-1 left-1/2 -translate-x-1/2 w-2 h-2 rounded-full bg-cyan-400 shadow-[0_0_10px_#22d3ee]" />
        )}
      </motion.div>

      {/* Middle Ring 2 - Counter-Clockwise Rotation */}
      <motion.div
        animate={{ rotate: -360 }}
        transition={{ duration: 22, repeat: Infinity, ease: 'linear' }}
        className="absolute inset-[15%] rounded-full border border-white/15"
      >
        {showSatellites && (
          <>
            <div className="absolute top-1/2 -right-1 -translate-y-1/2 w-1.5 h-1.5 rounded-full bg-purple-400 shadow-[0_0_8px_#c084fc]" />
            <div className="absolute top-1/2 -left-1 -translate-y-1/2 w-1 h-1 rounded-full bg-amber-400 shadow-[0_0_6px_#f59e0b]" />
          </>
        )}
      </motion.div>

      {/* Inner Ring 3 - Fast Orbit */}
      <motion.div
        animate={{ rotate: 360 }}
        transition={{ duration: 12, repeat: Infinity, ease: 'linear' }}
        className="absolute inset-[32%] rounded-full border border-cyan-400/20"
      >
        {showSatellites && (
          <div className="absolute -bottom-1 left-1/2 -translate-x-1/2 w-1.5 h-1.5 rounded-full bg-cyan-300 shadow-[0_0_8px_#67e8f9]" />
        )}
      </motion.div>

      {/* Central Pulsing Core */}
      {pulseCenter && (
        <div className="relative z-10 flex items-center justify-center">
          <motion.div
            animate={{ scale: [1, 1.3, 1], opacity: [0.4, 0.9, 0.4] }}
            transition={{ duration: 2.5, repeat: Infinity, ease: 'easeInOut' }}
            className="w-4 h-4 rounded-full bg-cyan-400/30 blur-[2px]"
          />
          <div className="absolute w-2 h-2 rounded-full bg-white shadow-[0_0_8px_#ffffff]" />
        </div>
      )}
    </div>
  );
};
