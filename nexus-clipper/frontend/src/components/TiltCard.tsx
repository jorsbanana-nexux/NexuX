import React, { useRef, useState, ReactNode } from 'react';
import { motion, useSpring } from 'motion/react';

interface TiltCardProps {
  children: ReactNode;
  className?: string;
  maxTilt?: number; // max degrees of tilt (default: 8)
  glareOpacity?: number; // max glare reflection opacity (default: 0.2)
  scaleOnHover?: number; // default: 1.015
  onClick?: (e: React.MouseEvent) => void;
  id?: string;
  'data-cursor-text'?: string;
}

export const TiltCard: React.FC<TiltCardProps> = ({
  children,
  className = '',
  maxTilt = 8,
  glareOpacity = 0.2,
  scaleOnHover = 1.015,
  onClick,
  id,
  'data-cursor-text': cursorText,
}) => {
  const cardRef = useRef<HTMLDivElement>(null);
  const glareRef = useRef<HTMLDivElement>(null);
  const [isHovered, setIsHovered] = useState(false);
  const cachedRect = useRef<{ left: number; top: number; width: number; height: number } | null>(null);

  // Smooth lightweight spring physics
  const springConfig = { damping: 25, stiffness: 350, mass: 0.1 };
  const rotateX = useSpring(0, springConfig);
  const rotateY = useSpring(0, springConfig);
  const scale = useSpring(1, springConfig);

  const handleMouseEnter = () => {
    if (cardRef.current) {
      const { left, top, width, height } = cardRef.current.getBoundingClientRect();
      cachedRect.current = { left, top, width, height };
    }
    setIsHovered(true);
    scale.set(scaleOnHover);
  };

  const handleMouseMove = (e: React.MouseEvent<HTMLDivElement>) => {
    if (!cachedRect.current) return;
    const { left, top, width, height } = cachedRect.current;

    const xPct = (e.clientX - left) / width - 0.5;
    const yPct = (e.clientY - top) / height - 0.5;

    rotateX.set(-yPct * maxTilt * 2);
    rotateY.set(xPct * maxTilt * 2);

    if (glareRef.current) {
      const gx = ((e.clientX - left) / width) * 100;
      const gy = ((e.clientY - top) / height) * 100;
      glareRef.current.style.background = `radial-gradient(circle 280px at ${gx.toFixed(1)}% ${gy.toFixed(1)}%, rgba(255, 255, 255, 0.25), rgba(34, 211, 238, 0.08) 40%, transparent 70%)`;
    }
  };

  const handleMouseLeave = () => {
    cachedRect.current = null;
    setIsHovered(false);
    rotateX.set(0);
    rotateY.set(0);
    scale.set(1);
  };

  return (
    <div
      style={{ perspective: 1000 }}
      className="inline-block w-full h-full"
    >
      <motion.div
        ref={cardRef}
        id={id}
        data-cursor-text={cursorText}
        onClick={onClick}
        onMouseMove={handleMouseMove}
        onMouseEnter={handleMouseEnter}
        onMouseLeave={handleMouseLeave}
        style={{
          rotateX,
          rotateY,
          scale,
          transformStyle: 'preserve-3d',
        }}
        className={`relative overflow-hidden transition-shadow duration-200 will-change-transform ${className}`}
      >
        {children}

        {/* High-Performance Direct DOM Specular Glare */}
        <div
          ref={glareRef}
          className="absolute inset-0 pointer-events-none transition-opacity duration-150 z-30"
          style={{
            opacity: isHovered ? glareOpacity : 0,
          }}
        />
      </motion.div>
    </div>
  );
};
