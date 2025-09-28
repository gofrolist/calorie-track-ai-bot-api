import { defineConfig } from 'vite';
import react from '@vitejs/plugin-react';

export default defineConfig({
  plugins: [react()],
  server: {
    port: 5173
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
