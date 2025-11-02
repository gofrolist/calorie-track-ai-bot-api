import { defineConfig, devices } from '@playwright/test';

/**
 * Enhanced Playwright Configuration for Telegram Mini App E2E Testing
 *
 * Features:
 * - Multiple device testing (mobile-first approach)
 * - Parallel test execution
 * - Video/screenshot recording on failure
 * - Retry mechanism for flaky tests
 * - Test reporting and debugging
 * - Mobile device simulation for safe areas
 * - Theme and language testing
 */

export default defineConfig({
  // Test directory structure
  testDir: './tests/e2e',

  // Global test configuration
  timeout: 30 * 1000, // 30 seconds per test
  expect: {
    timeout: 5 * 1000, // 5 seconds for assertions
  },

  // Test execution configuration
  fullyParallel: true, // Run tests in parallel
  forbidOnly: !!process.env.CI, // Fail CI if test.only() is left
  retries: process.env.CI ? 2 : 0, // Retry on CI
  workers: process.env.CI ? 1 : undefined, // Limit workers on CI

  // Test reporting
  reporter: [
    ['html', { open: 'never' }],
    ['json', { outputFile: 'test-results/results.json' }],
    ['junit', { outputFile: 'test-results/junit.xml' }],
    process.env.CI ? ['github'] : ['list'],
  ],

  // Global test setup and teardown (optional - remove if files don't exist)
  // globalSetup: require.resolve('./tests/global-setup.ts'),
  // globalTeardown: require.resolve('./tests/global-teardown.ts'),

  // Output directory for test artifacts
  outputDir: 'test-results/',

  // Web server configuration
  webServer: [
    // Frontend development server
    {
    command: 'npm run dev',
      url: 'http://localhost:3000',
    reuseExistingServer: !process.env.CI,
    timeout: 120_000,
      env: {
        // Test environment variables
        VITE_API_BASE_URL: 'http://localhost:8000',
        VITE_ENABLE_DEBUG_LOGGING: 'true',
        VITE_ENABLE_ERROR_REPORTING: 'false',
        VITE_ENABLE_ANALYTICS: 'false',
        VITE_ENABLE_DEV_TOOLS: 'true',
      },
    },
    // Backend API server (if not already running)
    ...(process.env.CI ? [{
      command: 'cd ../backend && make dev',
      url: 'http://localhost:8000/health/live',
      reuseExistingServer: true,
      timeout: 60_000,
    }] : []),
  ],

  // Global test configuration
  use: {
    // Base URL for tests
    baseURL: 'http://localhost:3000',

    // Browser configuration
    headless: !!process.env.CI,

    // Traces and debugging
    trace: 'on-first-retry',
    video: 'retain-on-failure',
    screenshot: 'only-on-failure',

    // Timeouts
    actionTimeout: 10 * 1000,
    navigationTimeout: 30 * 1000,

    // Locale and timezone
    locale: 'en-US',
    timezoneId: 'America/New_York',

    // Permissions (for Telegram Mini App features)
    // Note: 'camera' is not supported in Playwright context permissions
    // permissions: ['geolocation'],

    // Extra HTTP headers for all requests
    extraHTTPHeaders: {
      'Accept-Language': 'en-US,en;q=0.9',
      'User-Agent': 'Mozilla/5.0 (iPhone; CPU iPhone OS 16_0 like Mac OS X) AppleWebKit/605.1.15 Telegram',
    },
  },

  // Test projects for different devices and scenarios
  projects: [
    // =============================================================================
    // DESKTOP TESTING (for development)
    // =============================================================================
    {
      name: 'Desktop Chrome',
      use: {
        ...devices['Desktop Chrome'],
        viewport: { width: 1280, height: 720 },
      },
      testMatch: ['**/*.desktop.spec.ts', '**/basic-*.spec.ts'],
    },

    // =============================================================================
    // MOBILE DEVICE TESTING (primary focus for Telegram Mini App)
    // =============================================================================
    {
      name: 'iPhone 14 Pro',
      use: {
        ...devices['iPhone 14 Pro'],
        // Telegram Mini App specific headers
        extraHTTPHeaders: {
          'x-telegram-color-scheme': 'light',
          'x-telegram-language-code': 'en',
          'User-Agent': 'Mozilla/5.0 (iPhone; CPU iPhone OS 16_0 like Mac OS X) AppleWebKit/605.1.15 Telegram',
        },
      },
      testMatch: ['**/*.mobile.spec.ts', '**/safe-areas.spec.ts', '**/theme-*.spec.ts'],
    },

    {
      name: 'iPhone 14 Pro Dark',
      use: {
        ...devices['iPhone 14 Pro'],
        colorScheme: 'dark',
        extraHTTPHeaders: {
          'x-telegram-color-scheme': 'dark',
          'x-telegram-language-code': 'en',
          'User-Agent': 'Mozilla/5.0 (iPhone; CPU iPhone OS 16_0 like Mac OS X) AppleWebKit/605.1.15 Telegram',
        },
      },
      testMatch: ['**/theme-switching.spec.ts'],
    },

    {
      name: 'iPhone SE',
      use: {
        ...devices['iPhone SE'],
        extraHTTPHeaders: {
          'x-telegram-color-scheme': 'light',
          'x-telegram-language-code': 'en',
          'User-Agent': 'Mozilla/5.0 (iPhone; CPU iPhone OS 15_0 like Mac OS X) AppleWebKit/605.1.15 Telegram',
        },
      },
      testMatch: ['**/*.mobile.spec.ts', '**/safe-areas.spec.ts'],
    },

    {
      name: 'Samsung Galaxy S23',
      use: {
        ...devices['Galaxy S23'],
        extraHTTPHeaders: {
          'x-telegram-color-scheme': 'light',
          'x-telegram-language-code': 'en',
          'User-Agent': 'Mozilla/5.0 (Linux; Android 13; SM-S911B) AppleWebKit/537.36 Telegram',
        },
      },
      testMatch: ['**/*.mobile.spec.ts', '**/safe-areas.spec.ts'],
    },

    // =============================================================================
    // LANGUAGE TESTING
    // =============================================================================
    {
      name: 'Russian Language',
      use: {
        ...devices['iPhone 14 Pro'],
        locale: 'ru-RU',
        extraHTTPHeaders: {
          'x-telegram-color-scheme': 'light',
          'x-telegram-language-code': 'ru',
          'Accept-Language': 'ru-RU,ru;q=0.9',
          'User-Agent': 'Mozilla/5.0 (iPhone; CPU iPhone OS 16_0 like Mac OS X) AppleWebKit/605.1.15 Telegram',
        },
      },
      testMatch: ['**/language-detection.spec.ts'],
    },

    // =============================================================================
    // TABLET TESTING (for larger screens)
    // =============================================================================
    {
      name: 'iPad Pro',
      use: {
        ...devices['iPad Pro'],
        extraHTTPHeaders: {
          'x-telegram-color-scheme': 'light',
          'x-telegram-language-code': 'en',
          'User-Agent': 'Mozilla/5.0 (iPad; CPU OS 16_0 like Mac OS X) AppleWebKit/605.1.15 Telegram',
        },
      },
      testMatch: ['**/*.tablet.spec.ts', '**/safe-areas.spec.ts'],
    },

    // =============================================================================
    // PERFORMANCE TESTING
    // =============================================================================
    {
      name: 'Performance',
      use: {
        ...devices['iPhone 14 Pro'],
        // Slower network to test performance
        networkInterceptions: true,
      },
      testMatch: ['**/performance-*.spec.ts'],
      timeout: 60 * 1000, // Longer timeout for performance tests
    },

    // =============================================================================
    // ACCESSIBILITY TESTING
    // =============================================================================
    {
      name: 'Accessibility',
      use: {
        ...devices['iPhone 14 Pro'],
        // Force reduced motion for accessibility testing
        reducedMotion: 'reduce',
      },
      testMatch: ['**/accessibility-*.spec.ts', '**/accessibility.spec.ts'],
    },

    // =============================================================================
    // UI/UX VALIDATION TESTING
    // =============================================================================
    {
      name: 'UI-UX Validation',
      use: {
        ...devices['iPhone 14 Pro'],
      },
      testMatch: ['**/ui-ux-validation.spec.ts'],
    },
  ],
});
