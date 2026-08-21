import React, { useEffect, useState, useRef } from 'react';

export const CustomCursor: React.FC = () => {
  const [isSupported, setIsSupported] = useState(false);
  const [hoverText, setHoverText] = useState<string | null>(null);
  const [isHovered, setIsHovered] = useState(false);
  const [isClicked, setIsClicked] = useState(false);

  const dotRef = useRef<HTMLDivElement>(null);
  const ringRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    // Disable on touch devices
    if (
      'ontouchstart' in window ||
      navigator.maxTouchPoints > 0 ||
      window.matchMedia('(pointer: coarse)').matches
    ) {
      setIsSupported(false);
      return;
    }

    setIsSupported(true);

    let mouseX = -100;
    let mouseY = -100;
    let ringX = -100;
    let ringY = -100;
    let isVisible = false;
    let rafId: number;

    const onMouseMove = (e: MouseEvent) => {
      mouseX = e.clientX;
      mouseY = e.clientY;

      if (!isVisible) {
        isVisible = true;
        if (dotRef.current) dotRef.current.style.opacity = '1';
        if (ringRef.current) ringRef.current.style.opacity = '1';
      }

      // Direct instant GPU transform for the center dot (0ms latency)
      if (dotRef.current) {
        dotRef.current.style.transform = `translate3d(${mouseX}px, ${mouseY}px, 0)`;
      }
    };

    // Event delegation on mouseover/mouseout: ZERO DOM query on mousemove!
    const onMouseOver = (e: MouseEvent) => {
      const target = e.target as HTMLElement | null;
      if (!target) return;

      const interactive = target.closest(
        'button, a, input, textarea, select, [role="button"], [data-cursor="pointer"], .cursor-pointer'
      );
      if (interactive) {
        setIsHovered(true);
        const text = interactive.getAttribute('data-cursor-text');
        setHoverText(text);
      }
    };

    const onMouseOut = (e: MouseEvent) => {
      const target = e.target as HTMLElement | null;
      if (!target) return;

      const interactive = target.closest(
        'button, a, input, textarea, select, [role="button"], [data-cursor="pointer"], .cursor-pointer'
      );
      if (interactive) {
        setIsHovered(false);
        setHoverText(null);
      }
    };

    const onMouseDown = () => setIsClicked(true);
    const onMouseUp = () => setIsClicked(false);

    const onMouseLeave = () => {
      isVisible = false;
      if (dotRef.current) dotRef.current.style.opacity = '0';
      if (ringRef.current) ringRef.current.style.opacity = '0';
    };

    const onMouseEnter = () => {
      isVisible = true;
      if (dotRef.current) dotRef.current.style.opacity = '1';
      if (ringRef.current) ringRef.current.style.opacity = '1';
    };

    // Smooth 120 FPS inertial loop for trailing ring using direct transform3d
    const loop = () => {
      if (isVisible) {
        // Fast lerp factor: 0.22 (smooth trailing without drag lag)
        ringX += (mouseX - ringX) * 0.22;
        ringY += (mouseY - ringY) * 0.22;

        if (ringRef.current) {
          ringRef.current.style.transform = `translate3d(${ringX}px, ${ringY}px, 0)`;
        }
      }
      rafId = requestAnimationFrame(loop);
    };

    window.addEventListener('mousemove', onMouseMove, { passive: true });
    document.addEventListener('mouseover', onMouseOver, { passive: true });
    document.addEventListener('mouseout', onMouseOut, { passive: true });
    window.addEventListener('mousedown', onMouseDown, { passive: true });
    window.addEventListener('mouseup', onMouseUp, { passive: true });
    document.addEventListener('mouseleave', onMouseLeave);
    document.addEventListener('mouseenter', onMouseEnter);

    rafId = requestAnimationFrame(loop);

    return () => {
      cancelAnimationFrame(rafId);
      window.removeEventListener('mousemove', onMouseMove);
      document.removeEventListener('mouseover', onMouseOver);
      document.removeEventListener('mouseout', onMouseOut);
      window.removeEventListener('mousedown', onMouseDown);
      window.removeEventListener('mouseup', onMouseUp);
      document.removeEventListener('mouseleave', onMouseLeave);
      document.removeEventListener('mouseenter', onMouseEnter);
    };
  }, []);

  if (!isSupported) return null;

  return (
    <div className="pointer-events-none fixed inset-0 z-[9999] overflow-hidden hidden sm:block">
      {/* 1. Outer Smooth Trailing Ring (Direct Transform3D) */}
      <div
        ref={ringRef}
        className={`fixed top-0 left-0 -translate-x-1/2 -translate-y-1/2 rounded-full pointer-events-none transition-[width,height,border-color,background-color,box-shadow] duration-200 ease-out flex items-center justify-center will-change-transform ${
          isHovered
            ? 'w-12 h-12 border border-cyan-400 bg-cyan-400/10 shadow-[0_0_15px_rgba(34,211,238,0.4)]'
            : isClicked
            ? 'w-6 h-6 border border-white/60 bg-white/10 shadow-[0_0_8px_rgba(255,255,255,0.3)]'
            : 'w-8 h-8 border border-white/40 bg-white/5 shadow-[0_0_6px_rgba(255,255,255,0.15)]'
        }`}
        style={{
          opacity: 0,
          left: 0,
          top: 0,
        }}
      >
        {hoverText && (
          <span className="text-[8px] uppercase tracking-widest font-mono font-bold text-cyan-300 text-center px-1 select-none">
            {hoverText}
          </span>
        )}
      </div>

      {/* 2. Inner Precise Cursor Core Dot (Direct 0ms Latency Transform3D) */}
      <div
        ref={dotRef}
        className={`fixed top-0 left-0 -translate-x-1/2 -translate-y-1/2 rounded-full pointer-events-none transition-transform duration-100 ease-out will-change-transform ${
          isHovered
            ? 'w-1.5 h-1.5 bg-cyan-300 shadow-[0_0_10px_#22d3ee] scale-125'
            : isClicked
            ? 'w-1 h-1 bg-white shadow-[0_0_6px_#fff] scale-75'
            : 'w-1 h-1 bg-white shadow-[0_0_6px_#22d3ee]'
        }`}
        style={{
          opacity: 0,
          left: 0,
          top: 0,
        }}
      />
    </div>
  );
};
