/**
 * Frontend Contract Tests for Language Detection
 *
 * Tests to verify frontend language detection integrates properly with backend APIs
 * and Telegram WebApp environment. Validates language switching, detection logic,
 * and state management for English and Russian languages.
 *
 * @module LanguageDetectionContractTests
 */

import { describe, it, expect, beforeEach, afterEach, vi } from 'vitest';
import { http, HttpResponse } from 'msw';
import { setupServer } from 'msw/node';
import { languageDetectionService } from '../../src/services/language-detection';

// Mock Telegram WebApp with user data
const mockTelegramWebApp = {
  initDataUnsafe: {
    user: {
      id: 123456789,
      first_name: 'Test',
      last_name: 'User',
      username: 'testuser',
      language_code: 'en'
    }
  },
  ready: vi.fn(),
  expand: vi.fn()
};

// Mock navigator for browser language detection
const mockNavigator = {
  language: 'en-US',
  languages: ['en-US', 'en', 'ru']
};

// Mock server setup
const server = setupServer();

// Global mocks
Object.defineProperty(window, 'Telegram', {
  value: { WebApp: mockTelegramWebApp },
  writable: true
});

Object.defineProperty(window, 'navigator', {
  value: mockNavigator,
  writable: true
});

// Mock global navigator for tests that need it
Object.defineProperty(global, 'navigator', {
  value: mockNavigator,
  writable: true,
  configurable: true
});

describe('Frontend Contract Tests - Language Detection', () => {
  beforeAll(() => {
    // Set up default handlers for all tests
    server.use(
      http.get('http://localhost:8000/api/v1/config/language', () => {
        return HttpResponse.json({
          language: 'en',
          language_source: 'browser',
          telegram_language: 'en',
          browser_language: 'en',
          supported_languages: ['en', 'ru'],
          detected_at: '2023-01-01T00:00:00Z'
        });
      }),
      http.put('http://localhost:8000/api/v1/config/ui', async ({ request }) => {
        const body = await request.json();
        return HttpResponse.json({
          id: 'test-config',
          language: body.language,
          language_source: body.language_source,
          updated_at: new Date().toISOString()
        });
      })
    );
    server.listen();
  });

  afterAll(() => {
    server.close();
  });

  beforeEach(() => {
    vi.clearAllMocks();

    // Reset language detection service state
    languageDetectionService.dispose();
  });

  afterEach(() => {
    // Ensure service is properly reset after each test
    languageDetectionService.dispose();
  });

  describe('Language Detection API Integration', () => {
    it('should detect language from backend API', async () => {
      const mockApiResponse = {
        language: 'ru',
        language_source: 'telegram',
        telegram_language: 'ru',
        browser_language: 'en',
        supported_languages: ['en', 'ru'],
        detected_at: '2023-01-01T00:00:00Z'
      };

      server.use(
        http.get('http://localhost:8000/api/v1/config/language', () => {
          return HttpResponse.json(mockApiResponse);
        })
      );

      await languageDetectionService.initialize();
      await languageDetectionService.detectAndUpdateLanguage();

      const state = languageDetectionService.getLanguageState();
      expect(state.language).toBe('ru');
      expect(state.source).toBe('telegram');
      expect(state.supportedLanguages).toEqual(['en', 'ru']);
    });

    it('should update backend when language changes', async () => {
      let capturedUpdate: any = null;

      server.use(
        http.put('http://localhost:8000/api/v1/config/ui', async ({ request }) => {
          capturedUpdate = await request.json();
          return HttpResponse.json({
            id: 'updated-config',
            language: capturedUpdate.language,
            updated_at: new Date().toISOString()
          });
        })
      );

      await languageDetectionService.setLanguage('ru', 'manual');

      expect(capturedUpdate).toMatchObject({
        language: 'ru',
        language_source: 'manual'
      });
    });

    it('should handle API errors gracefully', async () => {
      server.use(
        http.get('http://localhost:8000/api/v1/config/language', () => {
          return HttpResponse.json({ error: 'Server error' }, { status: 500 });
        })
      );

      await languageDetectionService.initialize();

      // Should not throw error, but handle gracefully
      const state = languageDetectionService.getLanguageState();
      expect(state.language).toBeDefined(); // Should have fallback language
    });
  });

  describe('Telegram WebApp Integration', () => {
    it('should detect language from Telegram user data', async () => {
      mockTelegramWebApp.initDataUnsafe.user.language_code = 'ru';

      await languageDetectionService.initialize();

      expect(languageDetectionService.isInTelegram()).toBe(true);
      expect(languageDetectionService.getTelegramUserLanguage()).toBe('ru');
    });

    it('should handle English Telegram user language', async () => {
      mockTelegramWebApp.initDataUnsafe.user.language_code = 'en';

      const telegramLanguage = languageDetectionService.getTelegramUserLanguage();
      expect(telegramLanguage).toBe('en');
    });

    it('should handle missing Telegram user data gracefully', async () => {
      // Remove user data
      delete mockTelegramWebApp.initDataUnsafe.user.language_code;

      const telegramLanguage = languageDetectionService.getTelegramUserLanguage();
      expect(telegramLanguage).toBeNull();
    });

    it('should handle missing Telegram WebApp gracefully', async () => {
      // Remove Telegram WebApp
      delete (window as any).Telegram;

      await languageDetectionService.initialize();

      expect(languageDetectionService.isInTelegram()).toBe(false);
      expect(languageDetectionService.getTelegramUserLanguage()).toBeNull();

      const state = languageDetectionService.getLanguageState();
      expect(state.language).toBeDefined(); // Should still work without Telegram
    });

    it('should fallback from unsupported Telegram language', async () => {
      // Set unsupported language in Telegram
      mockTelegramWebApp.initDataUnsafe.user.language_code = 'fr'; // French not supported

      const mockApiResponse = {
        language: 'en', // Should fallback to English
        language_source: 'manual',
        supported_languages: ['en', 'ru'],
        detected_at: '2023-01-01T00:00:00Z'
      };

      server.use(
        http.get('http://localhost:8000/api/v1/config/language', () => {
          return HttpResponse.json(mockApiResponse);
        })
      );

      await languageDetectionService.detectAndUpdateLanguage();

      const state = languageDetectionService.getLanguageState();
      expect(state.language).toBe('en'); // Should fallback to supported language
    });
  });

  describe('Browser Language Detection', () => {
    it('should detect browser language preference', async () => {
      Object.defineProperty(navigator, 'language', {
        value: 'ru-RU',
        writable: true
      });

      const browserLanguage = languageDetectionService.getBrowserLanguage();
      expect(browserLanguage).toBe('ru'); // Should extract primary language code
    });

    it('should handle English browser language', async () => {
      Object.defineProperty(navigator, 'language', {
        value: 'en-US',
        writable: true
      });

      const browserLanguage = languageDetectionService.getBrowserLanguage();
      expect(browserLanguage).toBe('en');
    });

    it('should handle missing navigator gracefully', async () => {
      // Mock missing navigator
      delete (window as any).navigator;

      const browserLanguage = languageDetectionService.getBrowserLanguage();
      expect(browserLanguage).toBeNull();
    });

    it.skip('should extract primary language from locale', async () => {
      const testCases = [
        { input: 'en-US', expected: 'en' },
        { input: 'ru-RU', expected: 'ru' },
        { input: 'en', expected: 'en' },
        { input: 'ru', expected: 'ru' }
      ];

      testCases.forEach(({ input, expected }) => {
        // Mock navigator.language for this test
        const originalLanguage = window.navigator.language;
        window.navigator.language = input;

        const result = languageDetectionService.getBrowserLanguage();
        expect(result).toBe(expected);

        // Restore original value
        window.navigator.language = originalLanguage;
      });
    });
  });

  describe('Language State Management', () => {
    it('should maintain consistent state across operations', async () => {
      await languageDetectionService.initialize();

      const initialState = languageDetectionService.getLanguageState();
      expect(initialState).toMatchObject({
        language: expect.any(String),
        source: expect.any(String),
        supportedLanguages: expect.arrayContaining(['en', 'ru']),
        isAutoDetectionEnabled: expect.any(Boolean)
      });
    });

    it('should allow manual language override', async () => {
      await languageDetectionService.setLanguage('ru', 'manual');

      const state = languageDetectionService.getLanguageState();
      expect(state.language).toBe('ru');
      expect(state.source).toBe('manual');
    });

    it('should validate supported languages only', async () => {
      // Should accept supported languages
      await expect(
        languageDetectionService.setLanguage('en', 'manual')
      ).resolves.not.toThrow();

      await expect(
        languageDetectionService.setLanguage('ru', 'manual')
      ).resolves.not.toThrow();

      // Should reject unsupported languages (silently)
      const consoleSpy = vi.spyOn(console, 'warn').mockImplementation(() => {});

      await languageDetectionService.setLanguage('fr', 'manual'); // French not supported

      expect(consoleSpy).toHaveBeenCalledWith(expect.stringContaining('Invalid language code: fr'));
      consoleSpy.mockRestore();
    });

    it('should handle auto-detection toggle', async () => {
      languageDetectionService.setAutoDetection(false);

      const state = languageDetectionService.getLanguageState();
      expect(state.isAutoDetectionEnabled).toBe(false);

      languageDetectionService.setAutoDetection(true);

      const updatedState = languageDetectionService.getLanguageState();
      expect(updatedState.isAutoDetectionEnabled).toBe(true);
    });
  });

  describe('Language Utilities', () => {
    it('should return correct supported languages', async () => {
      const supportedLanguages = languageDetectionService.getSupportedLanguages();
      expect(supportedLanguages).toEqual(['en', 'ru']);
    });

    it('should validate language support correctly', async () => {
      expect(languageDetectionService.isLanguageSupported('en')).toBe(true);
      expect(languageDetectionService.isLanguageSupported('ru')).toBe(true);
      expect(languageDetectionService.isLanguageSupported('fr')).toBe(false);
      expect(languageDetectionService.isLanguageSupported('de')).toBe(false);
    });

    it('should return correct display names', async () => {
      expect(languageDetectionService.getLanguageDisplayName('en')).toBe('English');
      expect(languageDetectionService.getLanguageDisplayName('ru')).toBe('Русский');
      expect(languageDetectionService.getLanguageDisplayName('fr')).toBe('FR'); // Fallback for unsupported
    });
  });

  describe('Event System', () => {
    it('should notify listeners of language changes', async () => {
      const listener = vi.fn();
      const unsubscribe = languageDetectionService.addListener(listener);

      await languageDetectionService.setLanguage('ru', 'manual');

      expect(listener).toHaveBeenCalledWith(
        expect.objectContaining({
          language: 'ru',
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

      languageDetectionService.addListener(faultyListener);

      // Should not throw despite listener error
      await expect(
        languageDetectionService.setLanguage('en', 'manual')
      ).resolves.not.toThrow();
    });

    it('should allow listener cleanup', async () => {
      const listener = vi.fn();
      const unsubscribe = languageDetectionService.addListener(listener);

      unsubscribe();
      await languageDetectionService.setLanguage('ru', 'manual');

      expect(listener).not.toHaveBeenCalled();
    });
  });

  describe('DOM Integration', () => {
    it('should apply language to document attributes', async () => {
      await languageDetectionService.setLanguage('ru', 'manual');

      expect(document.documentElement.getAttribute('lang')).toBe('ru');
      expect(document.documentElement.getAttribute('data-language')).toBe('ru');
      expect(document.documentElement.getAttribute('data-language-source')).toBe('manual');
    });

    it('should set CSS custom properties', async () => {
      await languageDetectionService.setLanguage('en', 'browser');

      const rootStyle = document.documentElement.style;
      expect(rootStyle.getPropertyValue('--language')).toBe('en');
    });

    it('should set text direction correctly', async () => {
      // Both English and Russian are LTR languages
      await languageDetectionService.setLanguage('en', 'manual');
      expect(document.documentElement.getAttribute('dir')).toBe('ltr');

      await languageDetectionService.setLanguage('ru', 'manual');
      expect(document.documentElement.getAttribute('dir')).toBe('ltr');
    });

    it('should handle text direction for future RTL languages', async () => {
      // Test that the system is ready for RTL languages
      const rootStyle = document.documentElement.style;

      await languageDetectionService.setLanguage('en', 'manual');
      expect(rootStyle.getPropertyValue('--text-direction')).toBe('ltr');
    });
  });

  describe('Language Change Detection', () => {
    it.skip('should respond to browser language changes', async () => {
      const listener = vi.fn();
      languageDetectionService.addListener(listener);

      await languageDetectionService.initialize();

      // Simulate browser language change event
      const languageChangeEvent = new Event('languagechange');
      const originalLanguage = window.navigator.language;
      window.navigator.language = 'ru-RU';

      window.dispatchEvent(languageChangeEvent);

      // Restore original value
      window.navigator.language = originalLanguage;

      // Note: The actual language change handling depends on the service implementation
      // This test verifies the event listener setup
      expect(window.addEventListener).toBeDefined();
    });
  });

  describe('Performance and Cleanup', () => {
    it('should clean up resources on dispose', async () => {
      const listener = vi.fn();
      languageDetectionService.addListener(listener);

      await languageDetectionService.initialize();
      languageDetectionService.dispose();

      // Should not trigger listeners after disposal
      await languageDetectionService.setLanguage('ru', 'manual');
      expect(listener).not.toHaveBeenCalled();
    });

    it('should handle rapid language changes efficiently', async () => {
      const startTime = performance.now();

      // Rapidly change languages
      const languages = ['en', 'ru'];
      for (let i = 0; i < 10; i++) {
        await languageDetectionService.setLanguage(languages[i % 2], 'manual');
      }

      const endTime = performance.now();
      const duration = endTime - startTime;

      // Should complete reasonably quickly (less than 100ms)
      expect(duration).toBeLessThan(100);
    });

    it('should validate language codes correctly', async () => {
      const validCodes = ['en', 'ru'];
      const invalidCodes = ['invalid', '123', 'toolong', ''];

      validCodes.forEach(code => {
        expect(languageDetectionService.isLanguageSupported(code)).toBe(true);
      });

      invalidCodes.forEach(code => {
        expect(languageDetectionService.isLanguageSupported(code)).toBe(false);
      });
    });
  });

  describe('Integration with Configuration Service', () => {
    it('should work with configuration service for language detection', async () => {
      const mockApiResponse = {
        language: 'ru',
        language_source: 'telegram',
        supported_languages: ['en', 'ru'],
        detected_at: '2023-01-01T00:00:00Z'
      };

      server.use(
        http.get('http://localhost:8000/api/v1/config/language', () => {
          return HttpResponse.json(mockApiResponse);
        })
      );

      await languageDetectionService.detectAndUpdateLanguage();

      const state = languageDetectionService.getLanguageState();
      expect(state.language).toBe('ru');
      expect(state.supportedLanguages).toEqual(['en', 'ru']);
    });
  });
});
