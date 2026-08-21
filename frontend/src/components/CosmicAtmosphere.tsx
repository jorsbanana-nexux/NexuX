import React, { useEffect, useRef } from 'react';
import { CosmicThemeMode } from './AudioCosmicControls';

interface CosmicAtmosphereProps {
  theme?: CosmicThemeMode;
  enableParticles?: boolean;
}

export const CosmicAtmosphere: React.FC<CosmicAtmosphereProps> = ({
  theme = 'nebula',
  enableParticles = true,
}) => {
  const canvasRef = useRef<HTMLCanvasElement | null>(null);
  const scrollYRef = useRef(0);

  useEffect(() => {
    const handleScroll = () => {
      scrollYRef.current = window.scrollY;
    };
    window.addEventListener('scroll', handleScroll, { passive: true });
    return () => {
      window.removeEventListener('scroll', handleScroll);
    };
  }, []);

  // 120 FPS High-Performance Canvas Starfield (Zero-Lag Optimized)
  useEffect(() => {
    if (!enableParticles) return;

    const canvas = canvasRef.current;
    if (!canvas) return;

    const ctx = canvas.getContext('2d', { alpha: true });
    if (!ctx) return;

    let animationFrameId: number;
    let width = (canvas.width = window.innerWidth);
    let height = (canvas.height = window.innerHeight);

    const handleResize = () => {
      if (!canvas) return;
      width = canvas.width = window.innerWidth;
      height = canvas.height = window.innerHeight;
    };

    window.addEventListener('resize', handleResize, { passive: true });

    // Lightweight particle count: 45 stars for ultra-smooth 120 FPS
    const totalParticles = theme === 'deep-space' ? 35 : 55;
    
    interface Particle {
      x: number;
      baseY: number;
      size: number;
      speedX: number;
      speedY: number;
      parallaxFactor: number;
      color: string;
      baseAlpha: number;
      twinkleSpeed: number;
      twinkleOffset: number;
    }

    const activeColors = theme === 'deep-space' 
      ? ['#ffffff', '#cbd5e1', '#38bdf8'] 
      : ['#ffffff', '#22d3ee', '#c084fc', '#38bdf8'];

    const particles: Particle[] = [];
    for (let i = 0; i < totalParticles; i++) {
      const size = Math.random() < 0.7 ? Math.random() * 1.0 + 0.5 : Math.random() * 1.6 + 0.8;
      const baseAlpha = Math.random() * 0.45 + 0.25;
      const parallaxFactor = Math.random() * 0.12 + 0.03;
      const randomY = Math.random() * height;

      particles.push({
        x: Math.random() * width,
        baseY: randomY,
        size,
        speedX: (Math.random() - 0.5) * 0.1,
        speedY: (Math.random() - 0.5) * 0.1,
        parallaxFactor,
        color: activeColors[Math.floor(Math.random() * activeColors.length)],
        baseAlpha,
        twinkleSpeed: Math.random() * 0.02 + 0.01,
        twinkleOffset: Math.random() * Math.PI * 2,
      });
    }

    let time = 0;
    const render = () => {
      time += 1;
      ctx.clearRect(0, 0, width, height);

      const currentScrollY = scrollYRef.current;

      for (let i = 0; i < particles.length; i++) {
        const p = particles[i];

        p.x += p.speedX;
        p.baseY += p.speedY;

        if (p.x < 0) p.x = width;
        if (p.x > width) p.x = 0;
        if (p.baseY < 0) p.baseY = height;
        if (p.baseY > height) p.baseY = 0;

        const parallaxY = (p.baseY - currentScrollY * p.parallaxFactor) % height;
        const actualY = parallaxY < 0 ? parallaxY + height : parallaxY;

        const twinkle = Math.sin(time * p.twinkleSpeed + p.twinkleOffset);
        const dynamicAlpha = Math.max(0.1, Math.min(1, p.baseAlpha + twinkle * 0.2));

        ctx.fillStyle = p.color;
        ctx.globalAlpha = dynamicAlpha;
        ctx.fillRect(p.x, actualY, p.size, p.size);
      }

      ctx.globalAlpha = 1;
      animationFrameId = requestAnimationFrame(render);
    };

    render();

    return () => {
      window.removeEventListener('resize', handleResize);
      cancelAnimationFrame(animationFrameId);
    };
  }, [enableParticles, theme]);

  return (
    <div className="fixed inset-0 pointer-events-none z-0 overflow-hidden select-none">
      {/* 1. Hardware-Accelerated Ambient Nebula Gradients (Zero Heavy Dynamic Blur) */}
      {theme === 'nebula' && (
        <div className="absolute inset-0 pointer-events-none opacity-50">
          <div 
            className="absolute -top-40 -left-40 w-[600px] h-[600px] rounded-full pointer-events-none"
            style={{
              background: 'radial-gradient(circle, rgba(79, 70, 229, 0.18) 0%, rgba(147, 51, 234, 0.08) 45%, transparent 70%)',
              transform: 'translate3d(0, 0, 0)',
            }}
          />
          <div 
            className="absolute top-1/3 -right-40 w-[700px] h-[700px] rounded-full pointer-events-none"
            style={{
              background: 'radial-gradient(circle, rgba(6, 182, 212, 0.15) 0%, rgba(59, 130, 246, 0.06) 50%, transparent 70%)',
              transform: 'translate3d(0, 0, 0)',
            }}
          />
          <div 
            className="absolute bottom-10 left-1/4 w-[600px] h-[600px] rounded-full pointer-events-none"
            style={{
              background: 'radial-gradient(circle, rgba(168, 85, 247, 0.12) 0%, rgba(236, 72, 153, 0.05) 45%, transparent 70%)',
              transform: 'translate3d(0, 0, 0)',
            }}
          />
        </div>
      )}

      {/* 2. Deep Space Mode High-Contrast OLED Void */}
      {theme === 'deep-space' && (
        <div className="absolute inset-0 bg-black pointer-events-none" />
      )}

      {/* 3. Parallax Starfield Canvas */}
      <canvas
        ref={canvasRef}
        className="absolute inset-0 w-full h-full pointer-events-none"
      />
    </div>
  );
};
