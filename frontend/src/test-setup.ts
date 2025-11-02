/**
 * Test setup file for vitest
 * Configures testing environment and global test utilities
 */

import '@testing-library/jest-dom';
import { vi } from 'vitest';

// Mock localStorage for MSW and other tests
const localStorageMock = (() => {
  let store: Record<string, string> = {};

  return {
    getItem: (key: string) => store[key] || null,
    setItem: (key: string, value: string) => {
      store[key] = value.toString();
    },
    removeItem: (key: string) => {
      delete store[key];
    },
    clear: () => {
      store = {};
    },
    get length() {
      return Object.keys(store).length;
    },
    key: (index: number) => {
      const keys = Object.keys(store);
      return keys[index] || null;
    }
  };
})();

Object.defineProperty(global, 'localStorage', {
  value: localStorageMock,
  writable: true,
  configurable: true,
});

Object.defineProperty(window, 'localStorage', {
  value: localStorageMock,
  writable: true,
  configurable: true,
});

// Mock window.matchMedia for tests
const mockMatchMedia = vi.fn().mockImplementation(query => ({
  matches: false,
  media: query,
  onchange: null,
  addListener: vi.fn(), // deprecated
  removeListener: vi.fn(), // deprecated
  addEventListener: vi.fn(),
  removeEventListener: vi.fn(),
  dispatchEvent: vi.fn(),
}));

// Use Object.defineProperty with configurable: true for proper cleanup
Object.defineProperty(window, 'matchMedia', {
  value: mockMatchMedia,
  writable: true,
  configurable: true,
});

// Make matchMedia mockable for individual tests
(window.matchMedia as any).mockImplementation = mockMatchMedia;

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

// Mock Telegram WebApp with configurable properties
const mockTelegramWebApp = {
  ready: vi.fn(),
  expand: vi.fn(),
  initDataUnsafe: {
    user: {
      id: 123,
      first_name: 'Test',
      username: 'test_user',
      language_code: 'ru'
    }
  },
  initData: 'test_init_data',
  themeParams: {
    bg_color: '#ffffff',
    text_color: '#000000'
  },
  colorScheme: 'light'
};

Object.defineProperty(window, 'Telegram', {
  writable: true,
  configurable: true,
  value: {
    WebApp: mockTelegramWebApp
  }
});

// Mock navigator with configurable properties
const mockNavigator = {
  language: 'en-US',
  languages: ['en-US', 'en'],
};

// Use Object.defineProperty with configurable: true for proper cleanup
Object.defineProperty(globalThis, 'navigator', {
  value: mockNavigator,
  writable: true,
  configurable: true,
});

// Also define on window for tests that access window.navigator
Object.defineProperty(window, 'navigator', {
  value: mockNavigator,
  writable: true,
  configurable: true,
});

// Suppress console.error in tests unless needed
const originalError = console.error;
beforeAll(() => {
  console.error = (...args: any[]) => {
    const message = args[0];
    if (typeof message === 'string' && (
      message.includes('Warning:') ||
      message.includes('Theme change listener error') ||
      message.includes('Failed to detect language') ||
      message.includes('Error in language change listener')
    )) {
      return; // Suppress expected test errors
    }
    originalError.call(console, ...args);
  };
});

afterAll(() => {
  console.error = originalError;
});
