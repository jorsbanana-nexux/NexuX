import React, { useEffect, useRef } from 'react';
import { motion, AnimatePresence } from 'motion/react';
import { sound } from '../utils/soundEffects';

interface WarpSpeedTransitionProps {
  isActive: boolean;
  onComplete?: () => void;
  durationMs?: number;
  label?: string;
}

interface WarpStar {
  x: number;
  y: number;
  z: number;
  prevZ: number;
  color: string;
}

export const WarpSpeedTransition: React.FC<WarpSpeedTransitionProps> = ({
  isActive,
  onComplete,
  durationMs = 1200,
  label = 'WARP DRIVE ENGAGED // 躍進モード',
}) => {
  const canvasRef = useRef<HTMLCanvasElement | null>(null);

  useEffect(() => {
    if (!isActive) return;

    sound.playWarpSpeed();

    const canvas = canvasRef.current;
    if (!canvas) return;

    const ctx = canvas.getContext('2d', { alpha: true });
    if (!ctx) return;

    let animId: number;
    let width = (canvas.width = window.innerWidth);
    let height = (canvas.height = window.innerHeight);

    const starCount = 350;
    const colors = ['#ffffff', '#22d3ee', '#67e8f9', '#a855f7', '#38bdf8'];
    const stars: WarpStar[] = [];

    const initStar = (star: WarpStar) => {
      star.x = (Math.random() - 0.5) * width * 2;
      star.y = (Math.random() - 0.5) * height * 2;
      star.z = Math.random() * width + 200;
      star.prevZ = star.z;
      star.color = colors[Math.floor(Math.random() * colors.length)];
    };

    for (let i = 0; i < starCount; i++) {
      const star: WarpStar = { x: 0, y: 0, z: 0, prevZ: 0, color: '#fff' };
      initStar(star);
      stars.push(star);
    }

    const cx = width / 2;
    const cy = height / 2;
    let speed = 25;
    const startTime = performance.now();

    const render = (time: number) => {
      const elapsed = time - startTime;
      const progress = Math.min(elapsed / durationMs, 1);

      // Accelerate then decelerate
      if (progress < 0.6) {
        speed += 3.5;
      } else {
        speed = Math.max(speed - 4, 15);
      }

      // Fill with slight alpha for trailing motion blur streak
      ctx.fillStyle = 'rgba(0, 0, 0, 0.28)';
      ctx.fillRect(0, 0, width, height);

      for (let i = 0; i < stars.length; i++) {
        const star = stars[i];
        star.prevZ = star.z;
        star.z -= speed;

        if (star.z <= 0) {
          initStar(star);
          star.prevZ = star.z;
        }

        const k = 250 / star.z;
        const px = star.x * k + cx;
        const py = star.y * k + cy;

        const prevK = 250 / star.prevZ;
        const prevPx = star.x * prevK + cx;
        const prevPy = star.y * prevK + cy;

        if (px >= 0 && px <= width && py >= 0 && py <= height) {
          ctx.beginPath();
          ctx.moveTo(prevPx, prevPy);
          ctx.lineTo(px, py);
          ctx.strokeStyle = star.color;
          ctx.lineWidth = Math.min(Math.max((1 - star.z / width) * 3.5, 0.8), 4);
          ctx.stroke();
        }
      }

      if (progress < 1) {
        animId = requestAnimationFrame(render);
      } else {
        if (onComplete) onComplete();
      }
    };

    animId = requestAnimationFrame(render);

    return () => {
      cancelAnimationFrame(animId);
    };
  }, [isActive, durationMs, onComplete]);

  return (
    <AnimatePresence>
      {isActive && (
        <motion.div
          initial={{ opacity: 0 }}
          animate={{ opacity: 1 }}
          exit={{ opacity: 0 }}
          transition={{ duration: 0.25 }}
          className="fixed inset-0 z-[99999] bg-black flex flex-col items-center justify-center pointer-events-none select-none"
        >
          <canvas
            ref={canvasRef}
            className="absolute inset-0 w-full h-full"
          />

          {/* Central Warp Telemetry HUD */}
          <motion.div
            initial={{ scale: 0.8, opacity: 0 }}
            animate={{ scale: 1, opacity: 1 }}
            exit={{ scale: 1.2, opacity: 0 }}
            transition={{ duration: 0.3 }}
            className="relative z-10 text-center space-y-3 px-6 py-4 rounded-2xl bg-black/80 border border-cyan-400/40 backdrop-blur-xl shadow-[0_0_50px_rgba(34,211,238,0.5)]"
          >
            <div className="flex items-center justify-center gap-2 text-cyan-300 font-mono text-xs tracking-widest uppercase">
              <span className="w-2 h-2 rounded-full bg-cyan-400 animate-ping" />
              <span>{label}</span>
            </div>
            <div className="text-xl sm:text-3xl font-display font-extrabold text-white tracking-wider">
              HYPERSPACE JUMP // LIGHTSPEED
            </div>
            <div className="w-48 mx-auto h-1 bg-white/10 rounded-full overflow-hidden">
              <motion.div
                initial={{ width: '0%' }}
                animate={{ width: '100%' }}
                transition={{ duration: durationMs / 1000, ease: 'linear' }}
                className="h-full bg-gradient-to-r from-cyan-400 via-white to-purple-400 shadow-[0_0_10px_#22d3ee]"
              />
            </div>
          </motion.div>
        </motion.div>
      )}
    </AnimatePresence>
  );
};
