import React, { useRef, ReactNode } from 'react';
import { motion, useSpring } from 'motion/react';

interface MagneticProps {
  children: ReactNode;
  className?: string;
  strength?: number; // 0 to 1 (default 0.35)
  radius?: number; // active distance radius (default 90)
  onClick?: (e: React.MouseEvent) => void;
  onMouseEnter?: () => void;
  onMouseLeave?: () => void;
  id?: string;
  'data-cursor-text'?: string;
}

export const MagneticElement: React.FC<MagneticProps> = ({
  children,
  className = '',
  strength = 0.35,
  radius = 90,
  onClick,
  onMouseEnter,
  onMouseLeave,
  id,
  'data-cursor-text': cursorText,
}) => {
  const ref = useRef<HTMLDivElement>(null);
  const cachedRect = useRef<{ left: number; top: number; width: number; height: number } | null>(null);

  // Fast lightweight physics spring
  const springConfig = { damping: 20, stiffness: 350, mass: 0.1 };
  const x = useSpring(0, springConfig);
  const y = useSpring(0, springConfig);

  const handleMouseEnter = () => {
    if (ref.current) {
      const { left, top, width, height } = ref.current.getBoundingClientRect();
      cachedRect.current = { left, top, width, height };
    }
    if (onMouseEnter) onMouseEnter();
  };

  const handleMouseMove = (e: React.MouseEvent<HTMLDivElement>) => {
    if (!cachedRect.current) return;
    const { left, top, width, height } = cachedRect.current;
    const centerX = left + width / 2;
    const centerY = top + height / 2;

    const deltaX = e.clientX - centerX;
    const deltaY = e.clientY - centerY;
    const distance = Math.hypot(deltaX, deltaY);

    if (distance < radius) {
      x.set(deltaX * strength);
      y.set(deltaY * strength);
    } else {
      x.set(0);
      y.set(0);
    }
  };

  const handleMouseLeave = () => {
    cachedRect.current = null;
    x.set(0);
    y.set(0);
    if (onMouseLeave) onMouseLeave();
  };

  return (
    <motion.div
      ref={ref}
      id={id}
      data-cursor-text={cursorText}
      onMouseMove={handleMouseMove}
      onMouseEnter={handleMouseEnter}
      onMouseLeave={handleMouseLeave}
      onClick={onClick}
      style={{ x, y }}
      className={`inline-block will-change-transform ${className}`}
    >
      {children}
    </motion.div>
  );
};
