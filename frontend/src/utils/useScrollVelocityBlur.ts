import React, { useEffect, useRef, type RefObject } from 'react';
import { getLenis } from './lenis';

export interface VelocityTelemetry {
  velocity: number;
  blur: number;
  fps: number;
}

/**
 * Ultra-Lightweight Scroll Velocity Hook (120 FPS Zero-Lag Optimized)
 * Eliminates GPU-taxing CSS blur filters on large containers.
 * Throttles telemetry updates to avoid forcing 120 React re-renders per second.
 */
export function useScrollVelocityBlur(
  targetRef: RefObject<HTMLElement | null>,
  onTelemetryUpdate?: (data: VelocityTelemetry) => void
) {
  const lastScrollY = useRef(typeof window !== 'undefined' ? window.scrollY : 0);
  const lastTime = useRef(typeof performance !== 'undefined' ? performance.now() : 0);
  const lastUpdate = useRef(0);
  const frameCount = useRef(0);
  const lastFpsTime = useRef(typeof performance !== 'undefined' ? performance.now() : 0);
  const currentFps = useRef(120);

  useEffect(() => {
    let animId: number;

    const tick = (now: number) => {
      const dt = Math.max((now - lastTime.current) / 1000, 0.001);
      const scrollY = window.scrollY;
      const dy = Math.abs(scrollY - lastScrollY.current);

      const lenis = getLenis();
      let velocity = dy / dt;
      if (lenis && typeof lenis.velocity === 'number' && Math.abs(lenis.velocity) > 0) {
        velocity = Math.max(velocity, Math.abs(lenis.velocity) * 60);
      }

      lastScrollY.current = scrollY;
      lastTime.current = now;

      // Track display FPS
      frameCount.current++;
      if (now - lastFpsTime.current >= 600) {
        currentFps.current = Math.min(
          120,
          Math.round((frameCount.current * 1000) / (now - lastFpsTime.current))
        );
        frameCount.current = 0;
        lastFpsTime.current = now;
      }

      // Throttle telemetry update to max 8 times per second (avoiding re-render thrashing)
      if (onTelemetryUpdate && now - lastUpdate.current > 120) {
        lastUpdate.current = now;
        onTelemetryUpdate({
          velocity: Math.round(velocity),
          blur: Math.min(Math.round(velocity * 0.003), 4),
          fps: currentFps.current,
        });
      }

      animId = requestAnimationFrame(tick);
    };

    animId = requestAnimationFrame(tick);

    return () => {
      cancelAnimationFrame(animId);
    };
  }, [targetRef, onTelemetryUpdate]);
}
