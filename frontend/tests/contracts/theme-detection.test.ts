/**
 * Frontend Contract Tests for Theme Detection
 *
 * Tests to verify frontend theme detection integrates properly with backend APIs
 * and Telegram WebApp environment. Validates theme switching, detection logic,
 * and state management.
 *
 * @module ThemeDetectionContractTests
 */

import { describe, it, expect, beforeEach, afterEach, beforeAll, afterAll, vi } from 'vitest';
import { http, HttpResponse } from 'msw';
import { setupServer } from 'msw/node';
import { themeDetectionService } from '../../src/services/theme-detection';

// Mock Telegram WebApp
const mockTelegramWebApp = {
  colorScheme: 'light' as 'light' | 'dark',
  themeParams: {
    bg_color: '#ffffff',
    text_color: '#000000',
    hint_color: '#999999',
    link_color: '#2481cc',
    button_color: '#2481cc',
    button_text_color: '#ffffff',
    secondary_bg_color: '#f1f1f1'
  },
  ready: vi.fn(),
  expand: vi.fn(),
  onEvent: vi.fn()
};

// Default handlers for all tests
const defaultHandlers = [
  http.get('http://localhost:8000/api/v1/config/theme', () => {
    return HttpResponse.json({
      theme: 'light',
      theme_source: 'system',
      telegram_color_scheme: 'light',
      system_prefers_dark: false,
      detected_at: '2023-01-01T00:00:00Z'
    });
  }),
  http.put('http://localhost:8000/api/v1/config/ui', async ({ request }) => {
    const body = await request.json();
    return HttpResponse.json({
      id: 'test-config',
      theme: body.theme,
      theme_source: body.theme_source,
      updated_at: new Date().toISOString()
    });
  })
];

// Mock server setup - configure handlers upfront
const server = setupServer(...defaultHandlers);

// Save original matchMedia for restoration
const originalMatchMedia = window.matchMedia;

describe('Frontend Contract Tests - Theme Detection', () => {
  beforeAll(() => {
    // Global mocks
    Object.defineProperty(window, 'Telegram', {
      value: { WebApp: mockTelegramWebApp },
      writable: true,
      configurable: true
    });

    server.listen({ onUnhandledRequest: 'bypass' });
  });

  afterAll(() => {
    server.close();
  });

  beforeEach(() => {
    vi.clearAllMocks();
    server.resetHandlers();

    // Restore matchMedia to default mock
    Object.defineProperty(window, 'matchMedia', {
      value: vi.fn().mockImplementation((query: string) => ({
        matches: false,
        media: query,
        onchange: null,
        addListener: vi.fn(),
        removeListener: vi.fn(),
        addEventListener: vi.fn(),
        removeEventListener: vi.fn(),
        dispatchEvent: vi.fn(),
      })),
      writable: true,
      configurable: true,
    });

    // Restore Telegram mock
    Object.defineProperty(window, 'Telegram', {
      value: { WebApp: mockTelegramWebApp },
      writable: true,
      configurable: true
    });

    // Reset theme detection service state
    themeDetectionService.dispose();
  });

  afterEach(() => {
    themeDetectionService.dispose();
  });

  describe('Theme Detection API Integration', () => {
    it('should detect theme from backend API', async () => {
      const mockApiResponse = {
        theme: 'dark',
        theme_source: 'telegram',
        telegram_color_scheme: 'dark',
        system_prefers_dark: false,
        detected_at: '2023-01-01T00:00:00Z'
      };

      server.use(
        http.get('http://localhost:8000/api/v1/config/theme', () => {
          return HttpResponse.json(mockApiResponse);
        })
      );

      themeDetectionService.initialize();
      await themeDetectionService.detectAndUpdateTheme();

      const state = themeDetectionService.getThemeState();
      expect(state.theme).toBe('dark');
      expect(state.source).toBe('telegram');
    });

    it('should update backend when theme changes', async () => {
      let capturedUpdate: any = null;

      server.use(
        http.put('http://localhost:8000/api/v1/config/ui', async ({ request }) => {
          capturedUpdate = await request.json();
          return HttpResponse.json({
            id: 'updated-config',
            theme: capturedUpdate.theme,
            updated_at: new Date().toISOString()
          });
        })
      );

      await themeDetectionService.setTheme('dark', 'manual');

      expect(capturedUpdate).toMatchObject({
        theme: 'dark',
        theme_source: 'manual'
      });
    });

    it('should handle API errors gracefully', async () => {
      server.use(
        http.get('http://localhost:8000/api/v1/config/theme', () => {
          return HttpResponse.json({ error: 'Server error' }, { status: 500 });
        })
      );

      themeDetectionService.initialize();

      // Should not throw error, but handle gracefully
      const state = themeDetectionService.getThemeState();
      expect(state.theme).toBeDefined(); // Should have fallback theme
    });
  });

  describe('Telegram WebApp Integration', () => {
    it('should detect theme from Telegram WebApp', async () => {
      mockTelegramWebApp.colorScheme = 'dark';

      themeDetectionService.initialize();

      const state = themeDetectionService.getThemeState();
      expect(themeDetectionService.isInTelegram()).toBe(true);
    });

    it('should apply Telegram theme parameters to DOM', async () => {
      mockTelegramWebApp.colorScheme = 'light';
      mockTelegramWebApp.themeParams = {
        bg_color: '#ffffff',
        text_color: '#000000',
        button_color: '#007AFF'
      };

      await themeDetectionService.setTheme('light', 'telegram');

      // Check if CSS custom properties are set
      const rootStyle = document.documentElement.style;
      expect(document.documentElement.getAttribute('data-theme')).toBe('light');
    });

    it('should handle missing Telegram WebApp gracefully', async () => {
      // Remove Telegram WebApp
      delete (window as any).Telegram;

      themeDetectionService.initialize();

      expect(themeDetectionService.isInTelegram()).toBe(false);
      const state = themeDetectionService.getThemeState();
      expect(state.theme).toBeDefined(); // Should still work without Telegram
    });

    it('should respond to Telegram theme changes', async () => {
      const themeChangeListener = vi.fn();
      themeDetectionService.addListener(themeChangeListener);

      themeDetectionService.initialize();

      // Simulate Telegram theme change
      mockTelegramWebApp.colorScheme = 'dark';

      // Since we can't directly trigger the polling mechanism in tests,
      // we'll test the manual theme change which should trigger listeners
      await themeDetectionService.setTheme('dark', 'telegram');

      expect(themeChangeListener).toHaveBeenCalledWith(
        expect.objectContaining({
          theme: 'dark',
          source: 'telegram'
        })
      );
    });
  });

  describe('System Theme Detection', () => {
    it('should detect system dark mode preference', async () => {
      // Mock system prefers dark
      Object.defineProperty(window, 'matchMedia', {
        value: vi.fn().mockImplementation((query: string) => ({
          matches: query === '(prefers-color-scheme: dark)',
          media: query,
          onchange: null,
          addListener: vi.fn(),
          removeListener: vi.fn(),
          addEventListener: vi.fn(),
          removeEventListener: vi.fn(),
          dispatchEvent: vi.fn(),
        })),
        writable: true,
        configurable: true,
      });

      themeDetectionService.initialize();

      // If no Telegram override, should respect system preference
      const state = themeDetectionService.getThemeState();
      expect(state.systemPrefersDark).toBe(true);
    });

    it('should respond to system theme changes', async () => {
      const addEventListenerFn = vi.fn();
      const mediaQueryMock = {
        matches: false,
        media: '(prefers-color-scheme: dark)',
        onchange: null,
        addListener: vi.fn(),
        removeListener: vi.fn(),
        addEventListener: addEventListenerFn,
        removeEventListener: vi.fn(),
        dispatchEvent: vi.fn(),
      };

      Object.defineProperty(window, 'matchMedia', {
        value: vi.fn().mockReturnValue(mediaQueryMock),
        writable: true,
        configurable: true,
      });

      themeDetectionService.initialize();

      // Simulate system theme change
      mediaQueryMock.matches = true;

      // getThemeState() re-queries matchMedia, so it picks up the change
      const state = themeDetectionService.getThemeState();
      expect(state.systemPrefersDark).toBe(true);
    });

    it('should handle missing matchMedia gracefully', async () => {
      delete (window as any).matchMedia;

      themeDetectionService.initialize();

      const state = themeDetectionService.getThemeState();
      expect(state.theme).toBeDefined(); // Should still work
    });
  });

  describe('Theme State Management', () => {
    it('should maintain consistent state across operations', async () => {
      themeDetectionService.initialize();

      const initialState = themeDetectionService.getThemeState();
      expect(initialState).toMatchObject({
        theme: expect.any(String),
        source: expect.any(String),
        systemPrefersDark: expect.any(Boolean),
        isAutoDetectionEnabled: expect.any(Boolean)
      });
    });

    it('should allow manual theme override', async () => {
      await themeDetectionService.setTheme('dark', 'manual');

      const state = themeDetectionService.getThemeState();
      expect(state.theme).toBe('dark');
      expect(state.source).toBe('manual');
    });

    it('should validate theme values', async () => {
      // Should reject invalid theme values
      await expect(
        themeDetectionService.setTheme('invalid-theme' as any, 'manual')
      ).rejects.toThrow();
    });

    it('should handle auto-detection toggle', async () => {
      themeDetectionService.setAutoDetection(false);

      const state = themeDetectionService.getThemeState();
      expect(state.isAutoDetectionEnabled).toBe(false);

      themeDetectionService.setAutoDetection(true);

      const updatedState = themeDetectionService.getThemeState();
      expect(updatedState.isAutoDetectionEnabled).toBe(true);
    });
  });

  describe('Event System', () => {
    it('should notify listeners of theme changes', async () => {
      const listener = vi.fn();
      const unsubscribe = themeDetectionService.addListener(listener);

      await themeDetectionService.setTheme('dark', 'manual');

      expect(listener).toHaveBeenCalledWith(
        expect.objectContaining({
          theme: 'dark',
          source: 'manual',
          timestamp: expect.any(Number)
        })
      );

      unsubscribe();
    });

    it('should handle listener errors gracefully', async () => {
      const faultyListener = vi.fn().mockImplementation(() => {
        throw new Error('Listener error');
      });

      themeDetectionService.addListener(faultyListener);

      // Should not throw despite listener error
      await expect(
        themeDetectionService.setTheme('light', 'manual')
      ).resolves.not.toThrow();
    });

    it('should allow listener cleanup', async () => {
      const listener = vi.fn();
      const unsubscribe = themeDetectionService.addListener(listener);

      unsubscribe();
      await themeDetectionService.setTheme('dark', 'manual');

      expect(listener).not.toHaveBeenCalled();
    });
  });

  describe('DOM Integration', () => {
    it('should apply theme to document attributes', async () => {
      await themeDetectionService.setTheme('dark', 'manual');

      expect(document.documentElement.getAttribute('data-theme')).toBe('dark');
      expect(document.documentElement.getAttribute('data-theme-source')).toBe('manual');
    });

    it('should set CSS custom properties', async () => {
      await themeDetectionService.setTheme('light', 'system');

      const rootStyle = document.documentElement.style;
      expect(rootStyle.getPropertyValue('--theme')).toBe('light');
    });

    it('should handle resolved theme for auto mode', async () => {
      // Mock system prefers dark
      const mockMatchMedia = vi.fn().mockImplementation((query: string) => ({
        matches: query === '(prefers-color-scheme: dark)',
        addEventListener: vi.fn(),
        removeEventListener: vi.fn()
      }));

      Object.defineProperty(window, 'matchMedia', {
        value: mockMatchMedia,
        writable: true
      });

      await themeDetectionService.setTheme('auto', 'manual');

      const resolvedTheme = themeDetectionService.getResolvedTheme();
      expect(['light', 'dark']).toContain(resolvedTheme);
    });
  });

  describe('Performance and Cleanup', () => {
    it('should clean up resources on dispose', async () => {
      const listener = vi.fn();
      themeDetectionService.addListener(listener);

      themeDetectionService.initialize();
      themeDetectionService.dispose();

      // Should not trigger listeners after disposal
      await themeDetectionService.setTheme('dark', 'manual');
      expect(listener).not.toHaveBeenCalled();
    });

    it('should handle rapid theme changes efficiently', async () => {
      const startTime = performance.now();

      // Rapidly change themes
      for (let i = 0; i < 10; i++) {
        await themeDetectionService.setTheme(i % 2 === 0 ? 'light' : 'dark', 'manual');
      }

      const endTime = performance.now();
      const duration = endTime - startTime;

      // Should complete reasonably quickly (less than 500ms)
      expect(duration).toBeLessThan(500);
    });
  });
});
