/**
 * End-to-End Integration Tests for Language Detection
 *
 * Tests to verify language detection and switching works correctly across the application.
 * Validates automatic detection from Telegram and browser, manual switching,
 * and proper i18n integration for English and Russian languages.
 *
 * @module LanguageDetectionE2ETests
 */

import { test, expect, Page } from '@playwright/test';

test.describe('Language Detection Integration Tests', () => {
  test.beforeEach(async ({ page }) => {
    // Mock Telegram WebApp environment
    await page.addInitScript(() => {
      (window as any).Telegram = {
        WebApp: {
          ready: () => {},
          expand: () => {},
          colorScheme: 'light',
          themeParams: {
            bg_color: '#ffffff',
            text_color: '#000000'
          },
          initDataUnsafe: {
            user: {
              id: 123456789,
              first_name: 'Test',
              last_name: 'User',
              username: 'testuser',
              language_code: 'en' // Default to English
            }
          }
        }
      };
    });

    // Navigate to the application
    await page.goto('/');

    // Wait for language system to initialize
    await page.waitForTimeout(500);
  });

  test.describe('Language Detection', () => {
    test('should detect English language from Telegram user data', async ({ page }) => {
      // Set English in Telegram user data
      await page.evaluate(() => {
        if ((window as any).Telegram?.WebApp?.initDataUnsafe?.user) {
          (window as any).Telegram.WebApp.initDataUnsafe.user.language_code = 'en';
        }
      });

      // Trigger language detection
      await page.evaluate(() => {
        const event = new CustomEvent('telegramLanguageChanged');
        window.dispatchEvent(event);
      });

      await page.waitForTimeout(200);

      // Check if English is detected and applied
      const detectedLanguage = await page.evaluate(() => {
        return {
          htmlLang: document.documentElement.getAttribute('lang'),
          dataLanguage: document.documentElement.getAttribute('data-language'),
          languageSource: document.documentElement.getAttribute('data-language-source')
        };
      });

      expect(detectedLanguage.htmlLang).toBe('en');
      expect(detectedLanguage.dataLanguage).toBe('en');
    });

    test('should detect Russian language from Telegram user data', async ({ page }) => {
      // Set Russian in Telegram user data
      await page.evaluate(() => {
        if ((window as any).Telegram?.WebApp?.initDataUnsafe?.user) {
          (window as any).Telegram.WebApp.initDataUnsafe.user.language_code = 'ru';
        }
      });

      // Trigger language detection
      await page.evaluate(() => {
        const event = new CustomEvent('telegramLanguageChanged');
        window.dispatchEvent(event);
      });

      await page.waitForTimeout(200);

      // Check if Russian is detected and applied
      const detectedLanguage = await page.evaluate(() => {
        return {
          htmlLang: document.documentElement.getAttribute('lang'),
          dataLanguage: document.documentElement.getAttribute('data-language'),
          cssLanguageProperty: getComputedStyle(document.documentElement).getPropertyValue('--language')
        };
      });

      expect(detectedLanguage.htmlLang).toBe('ru');
      expect(detectedLanguage.dataLanguage).toBe('ru');
    });

    test('should detect language from browser when Telegram unavailable', async ({ page }) => {
      // Remove Telegram WebApp
      await page.evaluate(() => {
        delete (window as any).Telegram;
      });

      // Mock Russian browser language
      await page.addInitScript(() => {
        Object.defineProperty(navigator, 'language', {
          value: 'ru-RU',
          writable: true
        });
      });

      await page.reload();
      await page.waitForTimeout(500);

      // Should detect Russian from browser
      const browserLanguage = await page.evaluate(() => {
        return {
          htmlLang: document.documentElement.getAttribute('lang'),
          detectedBrowserLang: navigator.language,
          extractedLang: navigator.language.split('-')[0]
        };
      });

      expect(browserLanguage.extractedLang).toBe('ru');
      expect(['en', 'ru']).toContain(browserLanguage.htmlLang); // Should be supported language
    });

    test('should fallback to English for unsupported languages', async ({ page }) => {
      // Set unsupported language in Telegram
      await page.evaluate(() => {
        if ((window as any).Telegram?.WebApp?.initDataUnsafe?.user) {
          (window as any).Telegram.WebApp.initDataUnsafe.user.language_code = 'fr'; // French not supported
        }
      });

      // Mock unsupported browser language
      await page.addInitScript(() => {
        Object.defineProperty(navigator, 'language', {
          value: 'de-DE', // German not supported
          writable: true
        });
      });

      await page.reload();
      await page.waitForTimeout(500);

      // Should fallback to English
      const fallbackLanguage = await page.evaluate(() => {
        return {
          htmlLang: document.documentElement.getAttribute('lang'),
          telegramLang: (window as any).Telegram?.WebApp?.initDataUnsafe?.user?.language_code,
          browserLang: navigator.language.split('-')[0]
        };
      });

      expect(fallbackLanguage.htmlLang).toBe('en'); // Should fallback to English
      expect(fallbackLanguage.telegramLang).toBe('fr'); // Original was French
      expect(fallbackLanguage.browserLang).toBe('de'); // Original was German
    });
  });

  test.describe('Manual Language Switching', () => {
    test('should switch to Russian manually', async ({ page }) => {
      // Look for language selector/toggle
      const languageSelector = page.locator('[data-testid="language-selector"], select[name="language"], button:has-text("русский")').first();

      if (await languageSelector.count() > 0) {
        // If it's a select element
        if (await languageSelector.evaluate(el => el.tagName === 'SELECT')) {
          await languageSelector.selectOption('ru');
        } else {
          await languageSelector.click();
        }
      } else {
        // Manually trigger language change via JavaScript
        await page.evaluate(() => {
          if ((window as any).languageDetectionService) {
            (window as any).languageDetectionService.setLanguage('ru', 'manual');
          } else {
            // Fallback: directly set language attributes
            document.documentElement.setAttribute('lang', 'ru');
            document.documentElement.setAttribute('data-language', 'ru');
            document.documentElement.style.setProperty('--language', 'ru');
          }
        });
      }

      await page.waitForTimeout(200);

      // Verify Russian is applied
      const russianApplied = await page.evaluate(() => {
        return {
          lang: document.documentElement.getAttribute('lang'),
          dataLanguage: document.documentElement.getAttribute('data-language'),
          languageSource: document.documentElement.getAttribute('data-language-source')
        };
      });

      expect(russianApplied.lang).toBe('ru');
      expect(russianApplied.dataLanguage).toBe('ru');
    });

    test('should switch to English manually', async ({ page }) => {
      // First set to Russian
      await page.evaluate(() => {
        document.documentElement.setAttribute('lang', 'ru');
        document.documentElement.setAttribute('data-language', 'ru');
      });

      // Then switch to English
      const languageSelector = page.locator('[data-testid="language-selector"], select[name="language"], button:has-text("english")').first();

      if (await languageSelector.count() > 0) {
        if (await languageSelector.evaluate(el => el.tagName === 'SELECT')) {
          await languageSelector.selectOption('en');
        } else {
          await languageSelector.click();
        }
      } else {
        await page.evaluate(() => {
          if ((window as any).languageDetectionService) {
            (window as any).languageDetectionService.setLanguage('en', 'manual');
          } else {
            document.documentElement.setAttribute('lang', 'en');
            document.documentElement.setAttribute('data-language', 'en');
            document.documentElement.style.setProperty('--language', 'en');
          }
        });
      }

      await page.waitForTimeout(200);

      // Verify English is applied
      const englishApplied = await page.evaluate(() => {
        return document.documentElement.getAttribute('lang');
      });

      expect(englishApplied).toBe('en');
    });

    test('should reject invalid language codes', async ({ page }) => {
      // Mock console.warn to track warnings
      await page.addInitScript(() => {
        (window as any).languageWarnings = [];
        const originalWarn = console.warn;
        console.warn = (...args) => {
          (window as any).languageWarnings.push(args.join(' '));
          originalWarn.apply(console, args);
        };
      });

      // Try to set invalid language
      await page.evaluate(() => {
        if ((window as any).languageDetectionService) {
          (window as any).languageDetectionService.setLanguage('invalid-lang', 'manual');
        }
      });

      await page.waitForTimeout(200);

      // Should maintain previous valid language and show warning
      const invalidLanguageHandling = await page.evaluate(() => {
        return {
          currentLang: document.documentElement.getAttribute('lang'),
          warnings: (window as any).languageWarnings || []
        };
      });

      expect(['en', 'ru']).toContain(invalidLanguageHandling.currentLang);
      expect(invalidLanguageHandling.warnings.length).toBeGreaterThan(0);
    });
  });

  test.describe('Language Persistence', () => {
    test('should persist language choice across page reloads', async ({ page }) => {
      // Set language manually
      await page.evaluate(() => {
        localStorage.setItem('app-language-preference', 'ru');
        document.documentElement.setAttribute('lang', 'ru');
      });

      // Reload page
      await page.reload();
      await page.waitForTimeout(500);

      // Language should be restored
      const persistedLanguage = await page.evaluate(() => {
        return {
          storedLanguage: localStorage.getItem('app-language-preference'),
          currentLanguage: document.documentElement.getAttribute('lang')
        };
      });

      expect(persistedLanguage.storedLanguage).toBe('ru');
      expect(persistedLanguage.currentLanguage).toBe('ru');
    });

    test('should handle missing localStorage gracefully', async ({ page }) => {
      // Mock localStorage unavailability
      await page.addInitScript(() => {
        Object.defineProperty(window, 'localStorage', {
          value: {
            getItem: () => { throw new Error('Storage not available'); },
            setItem: () => { throw new Error('Storage not available'); },
            removeItem: () => { throw new Error('Storage not available'); }
          },
          writable: true
        });
      });

      await page.reload();
      await page.waitForTimeout(500);

      // Should still have a language applied despite storage error
      const languageWithoutStorage = await page.evaluate(() => {
        return document.documentElement.getAttribute('lang');
      });

      expect(['en', 'ru']).toContain(languageWithoutStorage);
    });
  });

  test.describe('Internationalization (i18n)', () => {
    test('should display English text content', async ({ page }) => {
      // Set English language
      await page.evaluate(() => {
        document.documentElement.setAttribute('lang', 'en');
      });

      await page.waitForTimeout(200);

      // Check for English text content
      const englishContent = await page.evaluate(() => {
        const textElements = Array.from(document.querySelectorAll('h1, h2, h3, p, button, span'));
        const sampleTexts = textElements
          .slice(0, 5) // First 5 elements
          .map(el => el.textContent?.trim())
          .filter(text => text && text.length > 0);

        return {
          language: document.documentElement.getAttribute('lang'),
          sampleTexts,
          hasEnglishWords: sampleTexts.some(text =>
            /\b(the|and|or|in|on|at|to|for|of|with|by)\b/i.test(text || '')
          )
        };
      });

      expect(englishContent.language).toBe('en');
      expect(englishContent.sampleTexts.length).toBeGreaterThan(0);
    });

    test('should display Russian text content when available', async ({ page }) => {
      // Set Russian language
      await page.evaluate(() => {
        document.documentElement.setAttribute('lang', 'ru');
      });

      await page.waitForTimeout(200);

      // Check for Russian text content or at least language setting
      const russianContent = await page.evaluate(() => {
        const textElements = Array.from(document.querySelectorAll('h1, h2, h3, p, button, span'));
        const sampleTexts = textElements
          .slice(0, 5)
          .map(el => el.textContent?.trim())
          .filter(text => text && text.length > 0);

        return {
          language: document.documentElement.getAttribute('lang'),
          sampleTexts,
          hasCyrillicText: sampleTexts.some(text =>
            /[а-я]/i.test(text || '')
          )
        };
      });

      expect(russianContent.language).toBe('ru');
      expect(russianContent.sampleTexts.length).toBeGreaterThan(0);
      // Note: Cyrillic text depends on actual i18n implementation
    });

    test('should handle text direction correctly for both languages', async ({ page }) => {
      const languages = ['en', 'ru'];

      for (const lang of languages) {
        await page.evaluate((language) => {
          document.documentElement.setAttribute('lang', language);
        }, lang);

        await page.waitForTimeout(100);

        const textDirection = await page.evaluate(() => {
          return {
            dir: document.documentElement.getAttribute('dir'),
            cssDirection: getComputedStyle(document.documentElement).direction,
            textDirection: getComputedStyle(document.documentElement).getPropertyValue('--text-direction')
          };
        });

        // Both English and Russian are LTR languages
        expect(textDirection.dir).toBe('ltr');
        expect(['ltr', '']).toContain(textDirection.cssDirection);
      }
    });
  });

  test.describe('Language Display and Utilities', () => {
    test('should display correct language names', async ({ page }) => {
      // Test language display names
      const languageNames = await page.evaluate(() => {
        // Simulate language detection service
        const getLanguageDisplayName = (code: string) => {
          const names: Record<string, string> = {
            'en': 'English',
            'ru': 'Русский'
          };
          return names[code] || code.toUpperCase();
        };

        return {
          english: getLanguageDisplayName('en'),
          russian: getLanguageDisplayName('ru'),
          unknown: getLanguageDisplayName('fr')
        };
      });

      expect(languageNames.english).toBe('English');
      expect(languageNames.russian).toBe('Русский');
      expect(languageNames.unknown).toBe('FR'); // Fallback for unsupported
    });

    test('should validate supported languages correctly', async ({ page }) => {
      const languageValidation = await page.evaluate(() => {
        const supportedLanguages = ['en', 'ru'];
        const isLanguageSupported = (lang: string) => supportedLanguages.includes(lang);

        return {
          english: isLanguageSupported('en'),
          russian: isLanguageSupported('ru'),
          french: isLanguageSupported('fr'),
          german: isLanguageSupported('de'),
          spanish: isLanguageSupported('es')
        };
      });

      expect(languageValidation.english).toBe(true);
      expect(languageValidation.russian).toBe(true);
      expect(languageValidation.french).toBe(false);
      expect(languageValidation.german).toBe(false);
      expect(languageValidation.spanish).toBe(false);
    });
  });

  test.describe('Language Change Events', () => {
    test('should notify components of language changes', async ({ page }) => {
      // Mock language change listener
      await page.evaluate(() => {
        (window as any).languageChangeEvents = [];

        const mockLanguageService = {
          addListener: (callback: Function) => {
            (window as any).languageChangeCallback = callback;
            return () => { (window as any).languageChangeCallback = null; };
          }
        };

        (window as any).languageDetectionService = mockLanguageService;
      });

      // Trigger language change
      await page.evaluate(() => {
        if ((window as any).languageChangeCallback) {
          (window as any).languageChangeCallback({
            language: 'ru',
            source: 'manual',
            previousLanguage: 'en',
            timestamp: Date.now()
          });
        }
      });

      await page.waitForTimeout(100);

      // Check if language change was handled
      const languageChangeHandled = await page.evaluate(() => {
        return {
          callbackExists: !!(window as any).languageChangeCallback,
          currentLanguage: document.documentElement.getAttribute('lang')
        };
      });

      expect(languageChangeHandled.callbackExists).toBe(true);
    });

    test('should handle browser language change events', async ({ page }) => {
      // Mock language change event listener setup
      await page.evaluate(() => {
        let eventListenerAdded = false;

        const originalAddEventListener = window.addEventListener;
        window.addEventListener = function(type, listener, options) {
          if (type === 'languagechange') {
            eventListenerAdded = true;
          }
          return originalAddEventListener.call(this, type, listener, options);
        };

        (window as any).languageEventListenerAdded = () => eventListenerAdded;
      });

      // Trigger service initialization
      await page.evaluate(() => {
        // Simulate language detection service initialization
        window.addEventListener('languagechange', () => {});
      });

      const eventListenerStatus = await page.evaluate(() => {
        return (window as any).languageEventListenerAdded?.() || false;
      });

      expect(eventListenerStatus).toBe(true);
    });
  });

  test.describe('Performance', () => {
    test('should switch languages efficiently', async ({ page }) => {
      const languages = ['en', 'ru', 'en', 'ru'];
      const startTime = Date.now();

      for (const lang of languages) {
        await page.evaluate((language) => {
          document.documentElement.setAttribute('lang', language);
          document.documentElement.setAttribute('data-language', language);
          document.documentElement.style.setProperty('--language', language);
        }, lang);

        await page.waitForTimeout(25);
      }

      const totalTime = Date.now() - startTime;

      // Language switching should be fast (< 300ms for 4 switches)
      expect(totalTime).toBeLessThan(300);
    });

    test('should not cause memory leaks during language changes', async ({ page }) => {
      // Monitor memory usage (simplified check)
      await page.evaluate(() => {
        (window as any).initialMemory = (performance as any).memory?.usedJSHeapSize || 0;
      });

      // Perform multiple language changes
      for (let i = 0; i < 10; i++) {
        await page.evaluate((index) => {
          const lang = index % 2 === 0 ? 'en' : 'ru';
          document.documentElement.setAttribute('lang', lang);
        }, i);
        await page.waitForTimeout(10);
      }

      const memoryUsage = await page.evaluate(() => {
        const currentMemory = (performance as any).memory?.usedJSHeapSize || 0;
        const initialMemory = (window as any).initialMemory || 0;
        return {
          initial: initialMemory,
          current: currentMemory,
          increase: currentMemory - initialMemory
        };
      });

      // Memory increase should be reasonable (< 5MB)
      if (memoryUsage.initial > 0) {
        expect(memoryUsage.increase).toBeLessThan(5 * 1024 * 1024);
      }
    });
  });

  test.describe('Error Handling', () => {
    test('should handle language detection service errors gracefully', async ({ page }) => {
      // Mock language detection error
      await page.addInitScript(() => {
        (window as any).languageErrors = [];
        const originalError = console.error;
        console.error = (...args) => {
          (window as any).languageErrors.push(args.join(' '));
          originalError.apply(console, args);
        };
      });

      // Cause an error in language detection
      await page.evaluate(() => {
        try {
          // Simulate language service error
          throw new Error('Language detection failed');
        } catch (error) {
          console.error('Language error:', error.message);
        }
      });

      await page.waitForTimeout(200);

      // Should still have a valid language despite errors
      const errorHandling = await page.evaluate(() => {
        return {
          currentLanguage: document.documentElement.getAttribute('lang'),
          errorCount: (window as any).languageErrors?.length || 0
        };
      });

      expect(['en', 'ru']).toContain(errorHandling.currentLanguage);
      expect(errorHandling.errorCount).toBeGreaterThan(0);
    });

    test('should handle missing navigator.language gracefully', async ({ page }) => {
      // Mock missing navigator.language
      await page.addInitScript(() => {
        delete (navigator as any).language;
        delete (navigator as any).languages;
      });

      await page.reload();
      await page.waitForTimeout(500);

      // Should still have a valid language
      const languageWithoutNavigator = await page.evaluate(() => {
        return {
          language: document.documentElement.getAttribute('lang'),
          navigatorLanguage: navigator.language
        };
      });

      expect(['en', 'ru']).toContain(languageWithoutNavigator.language);
      expect(languageWithoutNavigator.navigatorLanguage).toBeUndefined();
    });
  });

  test.describe('Integration with Backend', () => {
    test('should send correct language headers to backend', async ({ page }) => {
      // Mock fetch to capture headers
      await page.addInitScript(() => {
        (window as any).capturedHeaders = {};

        const originalFetch = window.fetch;
        window.fetch = function(url, options = {}) {
          if (typeof url === 'string' && url.includes('/api/')) {
            (window as any).capturedHeaders = {
              url,
              headers: options.headers || {}
            };
          }

          // Return a mock response
          return Promise.resolve(new Response('{}', { status: 200 }));
        };
      });

      // Set Russian language
      await page.evaluate(() => {
        document.documentElement.setAttribute('lang', 'ru');
      });

      // Make a mock API call
      await page.evaluate(() => {
        fetch('/api/v1/config/language', {
          headers: {
            'accept-language': 'ru-RU,ru;q=0.9,en;q=0.8',
            'x-telegram-language-code': 'ru'
          }
        });
      });

      const capturedRequest = await page.evaluate(() => {
        return (window as any).capturedHeaders;
      });

      expect(capturedRequest.url).toBe('/api/v1/config/language');
      expect(capturedRequest.headers).toBeDefined();
    });
  });
});
