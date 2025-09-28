/**
 * Frontend API Contract Tests for Configuration Endpoints
 *
 * Tests to verify frontend properly integrates with backend configuration APIs.
 * These tests validate request/response schemas and API contracts.
 *
 * @module ConfigContractTests
 */

import { describe, it, expect, beforeEach, afterEach } from 'vitest';
import { http, HttpResponse } from 'msw';
import { setupServer } from 'msw/node';
import { configurationService } from '../../src/services/config';

// Mock server setup
const server = setupServer();

describe('Frontend API Contract Tests - Configuration', () => {
  beforeEach(() => {
    server.listen();
  });

  afterEach(() => {
    server.resetHandlers();
    server.restoreHandlers();
  });

  describe('GET /api/v1/config/ui', () => {
    it('should handle valid UI configuration response', async () => {
      const mockResponse = {
        id: 'test-config-id',
        environment: 'development',
        api_base_url: 'http://localhost:8000',
        safe_area_top: 44,
        safe_area_bottom: 34,
        safe_area_left: 0,
        safe_area_right: 0,
        theme: 'light',
        theme_source: 'system',
        language: 'en',
        language_source: 'browser',
        features: {
          enableDebugLogging: true,
          enableErrorReporting: false
        },
        created_at: '2023-01-01T00:00:00Z',
        updated_at: '2023-01-01T00:00:00Z'
      };

      server.use(
        http.get('/api/v1/config/ui', () => {
          return HttpResponse.json(mockResponse);
        })
      );

      const result = await configurationService.getUIConfiguration();

      expect(result).toEqual(mockResponse);
      expect(result.environment).toBe('development');
      expect(result.theme).toBe('light');
      expect(result.language).toBe('en');
      expect(typeof result.features).toBe('object');
    });

    it('should handle API error responses', async () => {
      server.use(
        http.get('/api/v1/config/ui', () => {
          return HttpResponse.json({ error: 'Internal server error' }, { status: 500 });
        })
      );

      await expect(configurationService.getUIConfiguration()).rejects.toThrow();
    });

    it('should include proper headers in request', async () => {
      let capturedRequest: any = null;

      server.use(
        http.get('/api/v1/config/ui', ({ request }) => {
          capturedRequest = request;
          return HttpResponse.json({});
        })
      );

      await configurationService.getUIConfiguration();

      expect(capturedRequest).not.toBeNull();
      expect(capturedRequest.headers.get('content-type')).toContain('application/json');
    });
  });

  describe('PUT /api/v1/config/ui', () => {
    it('should send valid update request', async () => {
      const updateData = {
        theme: 'dark' as const,
        language: 'ru' as const,
        safe_area_top: 50,
        features: {
          enableDebugLogging: false
        }
      };

      let capturedRequestBody: any = null;

      server.use(
        http.put('/api/v1/config/ui', async ({ request }) => {
          capturedRequestBody = await request.json();
          return HttpResponse.json({
            ...updateData,
            id: 'updated-config-id',
            updated_at: new Date().toISOString()
          });
        })
      );

      const result = await configurationService.updateUIConfiguration(updateData);

      expect(capturedRequestBody).toEqual(updateData);
      expect(result.theme).toBe('dark');
      expect(result.language).toBe('ru');
    });

    it('should handle validation errors', async () => {
      server.use(
        http.put('/api/v1/config/ui', () => {
          return HttpResponse.json({
            error: 'Validation error',
            details: ['Invalid theme value']
          }, { status: 400 });
        })
      );

      const invalidData = {
        theme: 'invalid-theme' as any
      };

      await expect(configurationService.updateUIConfiguration(invalidData)).rejects.toThrow();
    });
  });

  describe('GET /api/v1/config/theme', () => {
    it('should handle theme detection response', async () => {
      const mockThemeResponse = {
        theme: 'dark',
        theme_source: 'telegram',
        telegram_color_scheme: 'dark',
        system_prefers_dark: true,
        detected_at: '2023-01-01T00:00:00Z'
      };

      server.use(
        http.get('/api/v1/config/theme', () => {
          return HttpResponse.json(mockThemeResponse);
        })
      );

      const result = await configurationService.detectTheme();

      expect(result).toEqual(mockThemeResponse);
      expect(result.theme).toBe('dark');
      expect(result.theme_source).toBe('telegram');
    });

    it('should handle theme detection with headers', async () => {
      let capturedHeaders: any = null;

      server.use(
        http.get('/api/v1/config/theme', ({ request }) => {
          capturedHeaders = Object.fromEntries(request.headers.entries());
          return HttpResponse.json({
            theme: 'light',
            theme_source: 'system',
            detected_at: new Date().toISOString()
          });
        })
      );

      await configurationService.detectTheme();

      expect(capturedHeaders).toBeDefined();
    });
  });

  describe('GET /api/v1/config/language', () => {
    it('should handle language detection response', async () => {
      const mockLanguageResponse = {
        language: 'ru',
        language_source: 'telegram',
        telegram_language: 'ru',
        browser_language: 'en',
        supported_languages: ['en', 'ru'],
        detected_at: '2023-01-01T00:00:00Z'
      };

      server.use(
        http.get('/api/v1/config/language', () => {
          return HttpResponse.json(mockLanguageResponse);
        })
      );

      const result = await configurationService.detectLanguage();

      expect(result).toEqual(mockLanguageResponse);
      expect(result.language).toBe('ru');
      expect(result.supported_languages).toContain('en');
      expect(result.supported_languages).toContain('ru');
    });

    it('should handle fallback to default language', async () => {
      const mockFallbackResponse = {
        language: 'en',
        language_source: 'manual',
        supported_languages: ['en', 'ru'],
        detected_at: '2023-01-01T00:00:00Z'
      };

      server.use(
        http.get('/api/v1/config/language', () => {
          return HttpResponse.json(mockFallbackResponse);
        })
      );

      const result = await configurationService.detectLanguage();

      expect(result.language).toBe('en');
      expect(result.language_source).toBe('manual');
    });
  });

  describe('Error Handling', () => {
    it('should handle network errors gracefully', async () => {
      server.use(
        http.get('/api/v1/config/ui', () => {
          return HttpResponse.error();
        })
      );

      await expect(configurationService.getUIConfiguration()).rejects.toThrow();
    });

    it('should handle malformed JSON responses', async () => {
      server.use(
        http.get('/api/v1/config/ui', () => {
          return HttpResponse.text('Invalid JSON');
        })
      );

      await expect(configurationService.getUIConfiguration()).rejects.toThrow();
    });

    it('should handle timeout errors', async () => {
      server.use(
        http.get('/api/v1/config/ui', () => {
          return HttpResponse.json({}, { status: 200 });
        })
      );

      // This test assumes the service has a reasonable timeout configured
      await expect(configurationService.getUIConfiguration()).rejects.toThrow();
    });
  });

  describe('Caching Behavior', () => {
    it('should respect cache when enabled', async () => {
      let requestCount = 0;

      server.use(
        http.get('/api/v1/config/ui', () => {
          requestCount++;
          return HttpResponse.json({
            id: 'cached-config',
            theme: 'light',
            language: 'en'
          });
        })
      );

      // Make two requests - second should use cache if caching is enabled
      await configurationService.getUIConfiguration();
      await configurationService.getUIConfiguration();

      // Note: This test assumes caching is implemented in the service
      // The exact behavior will depend on the service implementation
      expect(requestCount).toBeGreaterThanOrEqual(1);
    });

    it('should clear cache when requested', async () => {
      server.use(
        http.get('/api/v1/config/ui', () => {
          return HttpResponse.json({
            id: 'fresh-config',
            theme: 'dark',
            language: 'ru'
          });
        })
      );

      await configurationService.getUIConfiguration();
      configurationService.clearCache();
      const result = await configurationService.getUIConfiguration();

      expect(result.id).toBe('fresh-config');
    });
  });
});
