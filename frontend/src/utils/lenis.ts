import Lenis from 'lenis';
import gsap from 'gsap';
import { ScrollTrigger } from 'gsap/ScrollTrigger';

gsap.registerPlugin(ScrollTrigger);

let lenisInstance: Lenis | null = null;

export function initLenis(): Lenis {
  if (typeof window === 'undefined') {
    return null as unknown as Lenis;
  }

  if (lenisInstance) {
    return lenisInstance;
  }

  const lenis = new Lenis({
    duration: 0.8,
    easing: (t: number) => 1 - Math.pow(1 - t, 3), // Lightweight cubic-out easing
    orientation: 'vertical',
    gestureOrientation: 'vertical',
    smoothWheel: true,
    wheelMultiplier: 1.15,
    touchMultiplier: 1.6,
    infinite: false,
  });

  lenisInstance = lenis;

  // Synchronize Lenis with GSAP ScrollTrigger
  lenis.on('scroll', (e) => {
    ScrollTrigger.update();
  });

  // Connect GSAP ticker to Lenis requestAnimationFrame
  const tickerHandler = (time: number) => {
    lenis.raf(time * 1000);
  };
  gsap.ticker.add(tickerHandler);
  gsap.ticker.lagSmoothing(0);

  return lenis;
}

export function getLenis(): Lenis | null {
  return lenisInstance;
}

export function destroyLenis(): void {
  if (lenisInstance) {
    lenisInstance.destroy();
    lenisInstance = null;
  }
}
