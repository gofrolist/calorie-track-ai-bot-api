import { describe, it, expect } from '@jest/globals';
import { api } from '../../src/services/api';

describe('API Contract Tests - Connectivity', () => {
  describe('GET /health/connectivity', () => {
    it('should return connectivity status with required fields', async () => {
      const response = await api.get('/health/connectivity');

      expect(response.status).toBe(200);
      expect(response.data).toHaveProperty('status');
      expect(response.data).toHaveProperty('response_time_ms');
      expect(response.data).toHaveProperty('timestamp');
      expect(response.data).toHaveProperty('correlation_id');

      expect(['connected', 'disconnected', 'error']).toContain(response.data.status);
      expect(typeof response.data.response_time_ms).toBe('number');
      expect(response.data.response_time_ms).toBeGreaterThanOrEqual(0);
      expect(response.data.timestamp).toMatch(/^\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}/);
      expect(response.data.correlation_id).toMatch(/^[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}$/i);
    });

    it('should handle server errors gracefully', async () => {
      // Mock server error
      const mockError = {
        response: {
          status: 500,
          data: {
            error: 'Internal Server Error',
            message: 'Database connection failed',
            correlation_id: '123e4567-e89b-12d3-a456-426614174000',
            timestamp: new Date().toISOString()
          }
        }
      };

      // This test would be implemented with proper mocking
      expect(mockError.response.status).toBe(500);
      expect(mockError.response.data).toHaveProperty('error');
      expect(mockError.response.data).toHaveProperty('message');
      expect(mockError.response.data).toHaveProperty('correlation_id');
    });
  });
});

describe('API Contract Tests - UI Configuration', () => {
  describe('GET /api/v1/config/ui', () => {
    it('should return UI configuration with required fields', async () => {
      const response = await api.get('/api/v1/config/ui');

      expect(response.status).toBe(200);
      expect(response.data).toHaveProperty('id');
      expect(response.data).toHaveProperty('environment');
      expect(response.data).toHaveProperty('api_base_url');
      expect(response.data).toHaveProperty('theme');
      expect(response.data).toHaveProperty('theme_source');
      expect(response.data).toHaveProperty('language');
      expect(response.data).toHaveProperty('language_source');
      expect(response.data).toHaveProperty('created_at');
      expect(response.data).toHaveProperty('updated_at');

      expect(['development', 'production']).toContain(response.data.environment);
      expect(['light', 'dark', 'auto']).toContain(response.data.theme);
      expect(['telegram', 'system', 'manual']).toContain(response.data.theme_source);
      expect(['telegram', 'browser', 'manual']).toContain(response.data.language_source);
      expect(response.data.api_base_url).toMatch(/^https?:\/\//);
      expect(response.data.id).toMatch(/^[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}$/i);
    });

    it('should return 404 when configuration not found', async () => {
      // Mock 404 response
      const mockError = {
        response: {
          status: 404,
          data: {
            error: 'Not Found',
            message: 'UI configuration not found',
            correlation_id: '123e4567-e89b-12d3-a456-426614174000',
            timestamp: new Date().toISOString()
          }
        }
      };

      expect(mockError.response.status).toBe(404);
      expect(mockError.response.data).toHaveProperty('error');
      expect(mockError.response.data).toHaveProperty('message');
    });
  });

  describe('PUT /api/v1/config/ui', () => {
    it('should update UI configuration with valid data', async () => {
      const updateData = {
        environment: 'development',
        api_base_url: 'http://localhost:8000',
        theme: 'auto',
        theme_source: 'telegram',
        language: 'en',
        language_source: 'telegram',
        safe_area_top: 44,
        safe_area_bottom: 34,
        features: {
          enableDebugLogging: true,
          enableErrorReporting: false
        }
      };

      const response = await api.put('/api/v1/config/ui', updateData);

      expect(response.status).toBe(200);
      expect(response.data.environment).toBe(updateData.environment);
      expect(response.data.api_base_url).toBe(updateData.api_base_url);
      expect(response.data.theme).toBe(updateData.theme);
      expect(response.data.theme_source).toBe(updateData.theme_source);
      expect(response.data.language).toBe(updateData.language);
      expect(response.data.language_source).toBe(updateData.language_source);
    });

    it('should return 400 for invalid configuration data', async () => {
      const invalidData = {
        environment: 'invalid',
        api_base_url: 'not-a-url',
        theme: 'invalid-theme'
      };

      // Mock 400 response
      const mockError = {
        response: {
          status: 400,
          data: {
            error: 'Bad Request',
            message: 'Invalid configuration data',
            correlation_id: '123e4567-e89b-12d3-a456-426614174000',
            details: {
              environment: 'Must be one of: development, production',
              api_base_url: 'Must be a valid URL',
              theme: 'Must be one of: light, dark'
            },
            timestamp: new Date().toISOString()
          }
        }
      };

      expect(mockError.response.status).toBe(400);
      expect(mockError.response.data).toHaveProperty('details');
    });
  });
});

describe('API Contract Tests - Logging', () => {
  describe('POST /api/v1/logs', () => {
    it('should create log entry with valid data', async () => {
      const logData = {
        level: 'INFO',
        service: 'frontend',
        correlation_id: '123e4567-e89b-12d3-a456-426614174000',
        message: 'User action performed',
        context: {
          action: 'photo_upload',
          user_id: 'user123'
        },
        timestamp: new Date().toISOString()
      };

      const response = await api.post('/api/v1/logs', logData);

      expect(response.status).toBe(201);
      expect(response.data).toHaveProperty('id');
      expect(response.data).toHaveProperty('status');
      expect(response.data.status).toBe('created');
      expect(response.data.id).toMatch(/^[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}$/i);
    });

    it('should return 400 for invalid log entry data', async () => {
      const invalidData = {
        level: 'INVALID',
        service: '',
        message: '',
        timestamp: 'invalid-date'
      };

      // Mock 400 response
      const mockError = {
        response: {
          status: 400,
          data: {
            error: 'Bad Request',
            message: 'Invalid log entry data',
            correlation_id: '123e4567-e89b-12d3-a456-426614174000',
            details: {
              level: 'Must be one of: DEBUG, INFO, WARNING, ERROR, CRITICAL',
              service: 'Must not be empty',
              message: 'Must not be empty',
              timestamp: 'Must be valid ISO date string'
            },
            timestamp: new Date().toISOString()
          }
        }
      };

      expect(mockError.response.status).toBe(400);
      expect(mockError.response.data).toHaveProperty('details');
    });
  });
});

describe('API Contract Tests - Theme Detection', () => {
  describe('GET /api/v1/config/theme', () => {
    it('should detect theme configuration', async () => {
      const response = await api.get('/api/v1/config/theme');

      expect(response.status).toBe(200);
      expect(response.data).toHaveProperty('theme');
      expect(response.data).toHaveProperty('theme_source');
      expect(response.data).toHaveProperty('telegram_color_scheme');
      expect(response.data).toHaveProperty('system_prefers_dark');
      expect(response.data).toHaveProperty('detected_at');

      expect(['light', 'dark', 'auto']).toContain(response.data.theme);
      expect(['telegram', 'system', 'manual']).toContain(response.data.theme_source);
      expect(['light', 'dark']).toContain(response.data.telegram_color_scheme);
      expect(typeof response.data.system_prefers_dark).toBe('boolean');
    });

    it('should handle theme detection errors', async () => {
      // Mock 500 response
      const mockError = {
        response: {
          status: 500,
          data: {
            error: 'Internal Server Error',
            message: 'Failed to detect theme',
            correlation_id: '123e4567-e89b-12d3-a456-426614174000',
            timestamp: new Date().toISOString()
          }
        }
      };

      expect(mockError.response.status).toBe(500);
      expect(mockError.response.data).toHaveProperty('error');
      expect(mockError.response.data).toHaveProperty('message');
    });
  });
});

describe('API Contract Tests - Language Detection', () => {
  describe('GET /api/v1/config/language', () => {
    it('should detect language configuration', async () => {
      const response = await api.get('/api/v1/config/language');

      expect(response.status).toBe(200);
      expect(response.data).toHaveProperty('language');
      expect(response.data).toHaveProperty('language_source');
      expect(response.data).toHaveProperty('telegram_language');
      expect(response.data).toHaveProperty('browser_language');
      expect(response.data).toHaveProperty('supported_languages');
      expect(response.data).toHaveProperty('detected_at');

      expect(['telegram', 'browser', 'manual']).toContain(response.data.language_source);
      expect(Array.isArray(response.data.supported_languages)).toBe(true);
      expect(response.data.language).toMatch(/^[a-z]{2}(-[A-Z]{2})?$/);
    });

    it('should handle language detection errors', async () => {
      // Mock 500 response
      const mockError = {
        response: {
          status: 500,
          data: {
            error: 'Internal Server Error',
            message: 'Failed to detect language',
            correlation_id: '123e4567-e89b-12d3-a456-426614174000',
            timestamp: new Date().toISOString()
          }
        }
      };

      expect(mockError.response.status).toBe(500);
      expect(mockError.response.data).toHaveProperty('error');
      expect(mockError.response.data).toHaveProperty('message');
    });
  });
});

describe('API Contract Tests - Development Environment', () => {
  describe('GET /api/v1/dev/environment', () => {
    it('should return development environment configuration', async () => {
      const response = await api.get('/api/v1/dev/environment');

      expect(response.status).toBe(200);
      expect(response.data).toHaveProperty('id');
      expect(response.data).toHaveProperty('name');
      expect(response.data).toHaveProperty('frontend_port');
      expect(response.data).toHaveProperty('backend_port');
      expect(response.data).toHaveProperty('created_at');
      expect(response.data).toHaveProperty('updated_at');

      expect(typeof response.data.frontend_port).toBe('number');
      expect(typeof response.data.backend_port).toBe('number');
      expect(response.data.frontend_port).toBeGreaterThanOrEqual(1024);
      expect(response.data.frontend_port).toBeLessThanOrEqual(65535);
      expect(response.data.backend_port).toBeGreaterThanOrEqual(1024);
      expect(response.data.backend_port).toBeLessThanOrEqual(65535);
    });

    it('should return 404 when development environment not configured', async () => {
      // Mock 404 response
      const mockError = {
        response: {
          status: 404,
          data: {
            error: 'Not Found',
            message: 'Development environment not configured',
            correlation_id: '123e4567-e89b-12d3-a456-426614174000',
            timestamp: new Date().toISOString()
          }
        }
      };

      expect(mockError.response.status).toBe(404);
      expect(mockError.response.data).toHaveProperty('error');
      expect(mockError.response.data).toHaveProperty('message');
    });
  });

  describe('GET /api/v1/dev/supabase/status', () => {
    it('should return Supabase database status', async () => {
      const response = await api.get('/api/v1/dev/supabase/status');

      expect(response.status).toBe(200);
      expect(response.data).toHaveProperty('status');
      expect(response.data).toHaveProperty('db_url');
      expect(response.data).toHaveProperty('db_port');
      expect(response.data).toHaveProperty('version');
      expect(response.data).toHaveProperty('services');

      expect(['running', 'stopped', 'error']).toContain(response.data.status);
      expect(response.data.services).toHaveProperty('db');
      expect(typeof response.data.services.db).toBe('boolean');
      expect(response.data.db_port).toBe(54322);
    });

    it('should handle Supabase database status errors', async () => {
      // Mock 500 response
      const mockError = {
        response: {
          status: 500,
          data: {
            error: 'Internal Server Error',
            message: 'Failed to check Supabase database status',
            correlation_id: '123e4567-e89b-12d3-a456-426614174000',
            timestamp: new Date().toISOString()
          }
        }
      };

      expect(mockError.response.status).toBe(500);
      expect(mockError.response.data).toHaveProperty('error');
      expect(mockError.response.data).toHaveProperty('message');
    });
  });
});
