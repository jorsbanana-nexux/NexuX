import tailwindcss from '@tailwindcss/vite';
import react from '@vitejs/plugin-react';
import path from 'path';
import { defineConfig } from 'vite';

export default defineConfig(() => {
  return {
    plugins: [react(), tailwindcss()],
    resolve: {
      alias: {
        '@': path.resolve(__dirname, '.'),
      },
    },
    server: {
      port: 3000,
      host: '0.0.0.0',
    },
    preview: {
      port: 12001,
      host: '0.0.0.0',
      allowedHosts: [
        'work-1-jlvvraxqkzmdaiiu.prod-runtime.all-hands.dev',
        'work-2-jlvvraxqkzmdaiiu.prod-runtime.all-hands.dev',
        'localhost',
        '127.0.0.1',
      ],
    },
    build: {
      chunkSizeWarningLimit: 700,
      rollupOptions: {
        output: {
          manualChunks: {
            'react-vendor': ['react', 'react-dom'],
            'animation-vendor': ['motion', 'gsap', 'lenis'],
            'icons': ['lucide-react'],
          },
        },
      },
    },
  };
});
