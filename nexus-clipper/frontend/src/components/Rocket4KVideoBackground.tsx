import React, { useState, useEffect, useRef } from 'react';
import { motion, AnimatePresence } from 'motion/react';
import { Rocket, Play, Pause, SkipForward, Sparkles, Activity, Layers } from 'lucide-react';
import { sound } from '../utils/soundEffects';

export interface RocketVideoTrack {
  id: string;
  title: string;
  missionName: string;
  stage: string;
  category: string;
  videoUrl: string;
  poster: string;
  telemetry: {
    altitude: string;
    speed: string;
    stageStatus: string;
    thrust: string;
  };
}

export const SPACE_4K_VARIANTS: RocketVideoTrack[] = [
  {
    id: 'starship-ascent',
    title: 'Starship Orbital Ascent (4K)',
    missionName: 'STARSHIP IFT-V MEGAROCKET',
    stage: 'BOOSTER SEPARATION & MECO',
    category: 'SpaceX Launch',
    videoUrl: 'https://assets.mixkit.co/videos/preview/mixkit-stars-in-space-1610-large.mp4',
    poster: 'https://images.unsplash.com/photo-1517976487508-36a54054a7c0?q=80&w=2070&auto=format&fit=crop',
    telemetry: {
      altitude: '148.2 km',
      speed: '17,450 km/h',
      stageStatus: 'STAGE 2 NOMINAL',
      thrust: '16.7M lbf (74 MN)',
    },
  },
  {
    id: 'falcon-heavy-rtls',
    title: 'Falcon Heavy Dual RTLS (4K)',
    missionName: 'FALCON HEAVY SYNCHRONOUS',
    stage: 'GRID FIN SUPER-RETRO BURN',
    category: 'SpaceX Boosters',
    videoUrl: 'https://assets.mixkit.co/videos/preview/mixkit-flying-through-the-stars-in-space-40618-large.mp4',
    poster: 'https://images.unsplash.com/photo-1541185933-ef5d8ed016c2?q=80&w=2070&auto=format&fit=crop',
    telemetry: {
      altitude: '84.6 km',
      speed: '6,280 km/h',
      stageStatus: 'GRID FINS ACTIVE',
      thrust: '5.1M lbf (22.8 MN)',
    },
  },
  {
    id: 'starlink-leo-aurora',
    title: 'Starlink Orbit & Auroral Limb (4K)',
    missionName: 'STARLINK MISSION 550KM LEO',
    stage: 'SOLAR ARRAY DEPLOYMENT',
    category: 'Earth Orbit',
    videoUrl: 'https://assets.mixkit.co/videos/preview/mixkit-satellite-orbiting-the-earth-42861-large.mp4',
    poster: 'https://images.unsplash.com/photo-1451187580459-43490279c0fa?q=80&w=2072&auto=format&fit=crop',
    telemetry: {
      altitude: '542.0 km',
      speed: '27,610 km/h',
      stageStatus: 'LEO STABILIZED',
      thrust: 'ION PROPULSION',
    },
  },
  {
    id: 'deep-space-warp',
    title: 'Interstellar Warp Velocity (4K)',
    missionName: 'DEEP SPACE EXPLORER VECTOR',
    stage: 'RELATIVISTIC CRUISE',
    category: 'Hyperspace',
    videoUrl: 'https://assets.mixkit.co/videos/preview/mixkit-traveling-through-a-star-field-in-space-40619-large.mp4',
    poster: 'https://images.unsplash.com/photo-1446776811953-b23d57bd21aa?q=80&w=2072&auto=format&fit=crop',
    telemetry: {
      altitude: '1,840,000 km',
      speed: '42,100 km/h',
      stageStatus: 'WARP FACTOR 1',
      thrust: 'INERTIAL DRIVE',
    },
  },
  {
    id: 'iss-earth-sunrise',
    title: 'ISS Earth Sunrise Horizon (4K)',
    missionName: 'EXPEDITION 72 ORBITAL LAB',
    stage: 'ORBITAL SUNRISE PASS',
    category: 'Space Station',
    videoUrl: 'https://assets.mixkit.co/videos/preview/mixkit-earth-and-sun-view-from-space-41551-large.mp4',
    poster: 'https://images.unsplash.com/photo-1446776877081-d282a0f896e2?q=80&w=2072&auto=format&fit=crop',
    telemetry: {
      altitude: '418.5 km',
      speed: '27,580 km/h',
      stageStatus: 'CUPOLA OPTICAL NOMINAL',
      thrust: 'MICROGRAVITY',
    },
  },
  {
    id: 'mars-transfer',
    title: 'Starship Mars Transfer Trajectory (4K)',
    missionName: 'MARS COLONIZER FLEET-01',
    stage: 'TRANS-MARTIAN INJECTION',
    category: 'Mars Mission',
    videoUrl: 'https://assets.mixkit.co/videos/preview/mixkit-flying-through-a-starfield-in-space-40620-large.mp4',
    poster: 'https://images.unsplash.com/photo-1614728894747-a83421e2b9c9?q=80&w=2074&auto=format&fit=crop',
    telemetry: {
      altitude: '54,200,000 km',
      speed: '34,200 km/h',
      stageStatus: 'AEROBRAKING ENTRY PREP',
      thrust: 'RAPTOR VACUUM x3',
    },
  },
  {
    id: 'lunar-gateway-artemis',
    title: 'Artemis Lunar Gateway Orbit (4K)',
    missionName: 'ARTEMIS LUNAR RECONNAISSANCE',
    stage: 'NRHO ORBITAL CAPTURE',
    category: 'Lunar Orbit',
    videoUrl: 'https://assets.mixkit.co/videos/preview/mixkit-stars-in-space-1610-large.mp4',
    poster: 'https://images.unsplash.com/photo-1522030299830-16b8d3d049fe?q=80&w=2070&auto=format&fit=crop',
    telemetry: {
      altitude: '384,400 km',
      speed: '3,870 km/h',
      stageStatus: 'SOUTH POLE SCANNING',
      thrust: 'HYDRAZINE RCS',
    },
  },
  {
    id: 'dragon-docking',
    title: 'Crew Dragon Autonomous Docking (4K)',
    missionName: 'SPACEX DRAGON FREEDOM',
    stage: 'PROXIMITY OPS / WAYPOINT 2',
    category: 'Capsule Flight',
    videoUrl: 'https://assets.mixkit.co/videos/preview/mixkit-satellite-orbiting-the-earth-42861-large.mp4',
    poster: 'https://images.unsplash.com/photo-1516849841032-87cbac4d88f7?q=80&w=2070&auto=format&fit=crop',
    telemetry: {
      altitude: '422.1 km',
      speed: '0.12 m/s (REL)',
      stageStatus: 'SOFT CAPTURE RING READY',
      thrust: 'DRACO THRUSTERS',
    },
  },
  {
    id: 'nebula-deep-cosmos',
    title: 'Carina Nebula Supernova Remnant (4K)',
    missionName: 'JWST DEEP COSMOS SURVEY',
    stage: 'INFRARED STELLAR NURSERY',
    category: 'Deep Nebula',
    videoUrl: 'https://assets.mixkit.co/videos/preview/mixkit-traveling-through-a-star-field-in-space-40619-large.mp4',
    poster: 'https://images.unsplash.com/photo-1462331940025-496dfbfc7564?q=80&w=2022&auto=format&fit=crop',
    telemetry: {
      altitude: '7,500 LIGHT YRS',
      speed: '299,792 km/s (c)',
      stageStatus: 'NIRSPEC SPECTROMETRY',
      thrust: 'L2 LAGRANGE HALO',
    },
  },
  {
    id: 'plasma-reentry',
    title: 'Starship Atmospheric Re-entry Plasma (4K)',
    missionName: 'STARSHIP RE-ENTRY DYNAMICS',
    stage: 'HYPERSONIC FLAP STEERING',
    category: 'Atmospheric Entry',
    videoUrl: 'https://assets.mixkit.co/videos/preview/mixkit-flying-through-the-stars-in-space-40618-large.mp4',
    poster: 'https://images.unsplash.com/photo-1541185933-ef5d8ed016c2?q=80&w=2070&auto=format&fit=crop',
    telemetry: {
      altitude: '62.4 km',
      speed: '26,400 km/h (MACH 22)',
      stageStatus: 'HEAT SHIELD 1400°C',
      thrust: 'BELLY-FLOP GLIDE',
    },
  },
];

interface Rocket4KVideoBackgroundProps {
  opacity?: number;
  autoPlayIntervalMs?: number; // 15000ms for smooth performance
  currentIndex?: number;
  onIndexChange?: (index: number) => void;
}

export const Rocket4KVideoBackground: React.FC<Rocket4KVideoBackgroundProps> = ({
  opacity = 0.85,
  autoPlayIntervalMs = 15000,
  currentIndex: externalIndex,
  onIndexChange,
}) => {
  const [internalIndex, setInternalIndex] = useState(0);
  const isControlled = externalIndex !== undefined;
  const currentIndex = isControlled ? externalIndex : internalIndex;

  const [isAutoCycle, setIsAutoCycle] = useState(true);
  const videoRef = useRef<HTMLVideoElement | null>(null);
  const currentTrack = SPACE_4K_VARIANTS[currentIndex % SPACE_4K_VARIANTS.length];

  // Auto-Cycle fast 5 seconds as requested
  useEffect(() => {
    if (!isAutoCycle) return;
    const interval = setInterval(() => {
      const nextIndex = (currentIndex + 1) % SPACE_4K_VARIANTS.length;
      if (onIndexChange) {
        onIndexChange(nextIndex);
      } else {
        setInternalIndex(nextIndex);
      }
    }, autoPlayIntervalMs);

    return () => clearInterval(interval);
  }, [isAutoCycle, currentIndex, autoPlayIntervalMs, onIndexChange]);

  // Video reload when index changes with instant fallback
  useEffect(() => {
    if (videoRef.current) {
      videoRef.current.load();
      const playPromise = videoRef.current.play();
      if (playPromise !== undefined) {
        playPromise.catch(() => {
          // Autoplay silent fallback
        });
      }
    }
  }, [currentIndex]);

  return (
    <div className="fixed inset-0 w-full h-full overflow-hidden pointer-events-none z-0 select-none bg-black">
      {/* 1. Dynamic 4K Video Background with 5s Smooth Crossfade Transition */}
      <div 
        className="absolute inset-0 w-full h-full transition-opacity duration-1000 will-change-transform"
        style={{ opacity }}
      >
        <video
          ref={videoRef}
          key={currentTrack.id}
          autoPlay
          loop
          muted
          playsInline
          className="absolute inset-0 w-full h-full object-cover scale-105 filter brightness-110 contrast-110 will-change-transform transition-all duration-700"
          poster={currentTrack.poster}
        >
          <source src={currentTrack.videoUrl} type="video/mp4" />
        </video>

        {/* High-Impact Rocket Atmosphere Overlays */}
        <div className="absolute inset-0 bg-gradient-to-t from-black via-black/35 to-black/75 pointer-events-none" />
        <div className="absolute inset-0 bg-[radial-gradient(ellipse_at_center,transparent_0%,rgba(0,0,0,0.85)_100%)] pointer-events-none" />
        <div className="absolute inset-0 bg-tech-grid opacity-15 pointer-events-none" />
      </div>

      {/* 2. SpaceX Rocket Thruster Flame Glow Flare at bottom */}
      <div className="absolute bottom-0 left-1/2 -translate-x-1/2 w-[600px] sm:w-[900px] h-[300px] pointer-events-none opacity-30">
        <div 
          className="w-full h-full animate-pulse"
          style={{
            background: 'radial-gradient(ellipse at bottom, rgba(249, 115, 22, 0.45) 0%, rgba(234, 88, 12, 0.2) 30%, rgba(34, 211, 238, 0.12) 55%, transparent 75%)',
          }}
        />
      </div>
    </div>
  );
};
