/**
 * Test setup file for vitest
 * Configures testing environment and global test utilities
 */

import '@testing-library/jest-dom';
import { vi } from 'vitest';

// Mock window.matchMedia for tests
Object.defineProperty(window, 'matchMedia', {
  writable: true,
  value: vi.fn().mockImplementation(query => ({
    matches: false,
    media: query,
    onchange: null,
    addListener: vi.fn(), // deprecated
    removeListener: vi.fn(), // deprecated
    addEventListener: vi.fn(),
    removeEventListener: vi.fn(),
    dispatchEvent: vi.fn(),
  })),
});

// Mock window.CSS.supports for safe area tests
Object.defineProperty(window, 'CSS', {
  writable: true,
  value: {
    supports: vi.fn().mockReturnValue(true),
  },
});

// Mock ResizeObserver
global.ResizeObserver = vi.fn().mockImplementation(() => ({
  observe: vi.fn(),
  unobserve: vi.fn(),
  disconnect: vi.fn(),
}));

// Mock IntersectionObserver
global.IntersectionObserver = vi.fn().mockImplementation(() => ({
  observe: vi.fn(),
  unobserve: vi.fn(),
  disconnect: vi.fn(),
}));

// Mock Telegram WebApp
Object.defineProperty(window, 'Telegram', {
  writable: true,
  value: {
    WebApp: {
      ready: vi.fn(),
      expand: vi.fn(),
      initDataUnsafe: {
        user: {
          id: 123,
          first_name: 'Test',
          username: 'test_user'
        }
      },
      initData: 'test_init_data',
      themeParams: {
        bg_color: '#ffffff',
        text_color: '#000000'
      },
      colorScheme: 'light'
    }
  }
});

// Mock navigator.language
Object.defineProperty(navigator, 'language', {
  writable: true,
  value: 'en-US',
});

// Suppress console.error in tests unless needed
const originalError = console.error;
beforeAll(() => {
  console.error = (...args: any[]) => {
    if (
      typeof args[0] === 'string' &&
      args[0].includes('Warning:')
    ) {
      return;
    }
    originalError.call(console, ...args);
  };
});

afterAll(() => {
  console.error = originalError;
});
