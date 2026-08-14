/** @type {import('tailwindcss').Config} */
export default {
  content: [
    "./index.html",
    "./src/**/*.{js,jsx,ts,tsx}",
  ],
  theme: {
    extend: {
      colors: {
        spacex: {
          bg:      '#07080B',
          card:    '#0E1017',
          border:  'rgba(255,255,255,0.08)',
          accent:  '#CCFF00',
          cyan:    '#00F0FF',
          purple:  '#A855F7',
          danger:  '#FF4444',
          success: '#00FF88',
        },
      },
      fontFamily: {
        sans: ['Inter', 'Plus Jakarta Sans', 'system-ui', 'sans-serif'],
        mono: ['JetBrains Mono', 'Fira Code', 'monospace'],
      },
      backdropBlur: {
        xs: '2px',
      },
      animation: {
        'pulse-glow': 'pulseGlow 2s cubic-bezier(0.4, 0, 0.6, 1) infinite',
        'glow-lime':  'glowLime 2s ease-in-out infinite alternate',
        'glow-cyan':  'glowCyan 2s ease-in-out infinite alternate',
        'float':      'float 3s ease-in-out infinite',
        'fade-in':    'fadeIn 0.3s ease-out',
        'slide-up':   'slideUp 0.4s ease-out',
      },
      keyframes: {
        pulseGlow: {
          '0%, 100%': {
            opacity: '1',
            boxShadow: '0 0 12px rgba(204,255,0,0.3)',
          },
          '50%': {
            opacity: '0.75',
            boxShadow: '0 0 35px rgba(204,255,0,0.65)',
          },
        },
        glowLime: {
          '0%':   { boxShadow: '0 0 4px rgba(204,255,0,0.3)' },
          '100%': { boxShadow: '0 0 28px rgba(204,255,0,0.7)' },
        },
        glowCyan: {
          '0%':   { boxShadow: '0 0 4px rgba(0,240,255,0.3)' },
          '100%': { boxShadow: '0 0 28px rgba(0,240,255,0.7)' },
        },
        float: {
          '0%, 100%': { transform: 'translateY(0px)' },
          '50%':      { transform: 'translateY(-8px)' },
        },
        fadeIn: {
          '0%':   { opacity: '0' },
          '100%': { opacity: '1' },
        },
        slideUp: {
          '0%':   { opacity: '0', transform: 'translateY(16px)' },
          '100%': { opacity: '1', transform: 'translateY(0)' },
        },
      },
    },
  },
  plugins: [],
}
