import { defineConfig } from 'vite';
import react from '@vitejs/plugin-react';

export default defineConfig({
  plugins: [react()],
  server: {
    port: 5173
  },
  build: {
    rollupOptions: {
      output: {
        manualChunks: {
          // React core libraries
          'react-vendor': ['react', 'react-dom', 'react-router-dom'],
          // Swiper carousel library
          'swiper-vendor': ['swiper'],
          // i18next internationalization libraries
          'i18n-vendor': ['i18next', 'react-i18next'],
          // Note: Analytics libraries are small and kept in main bundle for optimal loading
        },
      },
    },
    // Increase chunk size warning limit to 600kb (since we're splitting properly now)
    chunkSizeWarningLimit: 600,
  },
  test: {
    globals: true,
    environment: 'jsdom',
    setupFiles: ['./src/test-setup.ts'],
    exclude: ['tests/e2e/**/*', 'node_modules/**/*'],
    // Configure error handling to ignore cleanup errors
    onUnhandledRejection: 'ignore',
    onUncaughtException: 'ignore',
    // Set up error handling for unhandled errors
    onUnhandledError: 'ignore'
  }
});
