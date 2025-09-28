// Frontend Configuration
// Environment-specific settings for the Calorie Track Mini App

export interface AppConfig {
  // API Configuration
  apiBaseUrl: string;
  apiTimeout: number;

  // Environment
  environment: 'development' | 'production';
  isProduction: boolean;
  isDevelopment: boolean;

  // Telegram WebApp
  telegramBotName?: string;
  telegramAppUrl?: string;

  // UI/UX Configuration
  ui: {
    enableSafeAreas: boolean;
    enableThemeDetection: boolean;
    enableLanguageDetection: boolean;
    defaultTheme: 'light' | 'dark' | 'auto';
    defaultLanguage: string;
    supportedLanguages: ('en' | 'ru')[];
  };

  // Connectivity Configuration
  connectivity: {
    enableMonitoring: boolean;
    checkInterval: number;
    retryAttempts: number;
    timeout: number;
  };

  // Features
  features: {
    enableDebugLogging: boolean;
    enableErrorReporting: boolean;
    enableAnalytics: boolean;
    enableDevTools: boolean;
    enableThemeDetection: boolean;
    enableLanguageDetection: boolean;
    enableSafeAreas: boolean;
    enableConnectivityMonitoring: boolean;
    enableLogging: boolean;
  };

  // App Metadata
  appVersion: string;
  buildTimestamp: string;
}

// Environment variable validation and defaults
const getEnvVar = (key: string, defaultValue?: string): string => {
  const value = import.meta.env[key];
  if (value === undefined && defaultValue === undefined) {
    throw new Error(`Required environment variable ${key} is not set`);
  }
  return value || defaultValue || '';
};

const getBooleanEnvVar = (key: string, defaultValue: boolean = false): boolean => {
  const value = import.meta.env[key];
  if (value === undefined) return defaultValue;
  return value.toLowerCase() === 'true' || value === '1';
};

// Environment detection
const environment = (import.meta.env.NODE_ENV as AppConfig['environment']) || 'development';
const isProduction = environment === 'production';
const isDevelopment = environment === 'development';

// API Configuration
const apiBaseUrl = getEnvVar('VITE_API_BASE_URL',
  isDevelopment ? 'http://localhost:8000' : 'https://calorie-track-ai-bot.fly.dev'
);

// Telegram Configuration
const telegramBotName = import.meta.env.VITE_TELEGRAM_BOT_NAME;
const telegramAppUrl = import.meta.env.VITE_TELEGRAM_APP_URL;

// UI/UX Configuration
const ui = {
  enableSafeAreas: getBooleanEnvVar('VITE_ENABLE_SAFE_AREAS', true),
  enableThemeDetection: getBooleanEnvVar('VITE_ENABLE_THEME_DETECTION', true),
  enableLanguageDetection: getBooleanEnvVar('VITE_ENABLE_LANGUAGE_DETECTION', true),
  defaultTheme: (getEnvVar('VITE_DEFAULT_THEME', 'auto') as 'light' | 'dark' | 'auto'),
  defaultLanguage: getEnvVar('VITE_DEFAULT_LANGUAGE', 'en'),
  supportedLanguages: (getEnvVar('VITE_SUPPORTED_LANGUAGES', 'en,ru')).split(',') as ('en' | 'ru')[],
};

// Connectivity Configuration
const connectivity = {
  enableMonitoring: getBooleanEnvVar('VITE_ENABLE_CONNECTIVITY_MONITORING', true),
  checkInterval: parseInt(getEnvVar('VITE_CONNECTIVITY_CHECK_INTERVAL', '30000'), 10),
  retryAttempts: parseInt(getEnvVar('VITE_CONNECTIVITY_RETRY_ATTEMPTS', '5'), 10),
  timeout: parseInt(getEnvVar('VITE_CONNECTIVITY_TIMEOUT', '10000'), 10),
};

// Feature flags
const features = {
  enableDebugLogging: getBooleanEnvVar('VITE_ENABLE_DEBUG_LOGGING', isDevelopment),
  enableErrorReporting: getBooleanEnvVar('VITE_ENABLE_ERROR_REPORTING', isProduction),
  enableAnalytics: getBooleanEnvVar('VITE_ENABLE_ANALYTICS', isProduction),
  enableDevTools: getBooleanEnvVar('VITE_ENABLE_DEV_TOOLS', isDevelopment),
  enableThemeDetection: ui.enableThemeDetection,
  enableLanguageDetection: ui.enableLanguageDetection,
  enableSafeAreas: ui.enableSafeAreas,
  enableConnectivityMonitoring: connectivity.enableMonitoring,
  enableLogging: getBooleanEnvVar('VITE_ENABLE_LOGGING', true),
};

// App metadata
const appVersion = import.meta.env.VITE_APP_VERSION || '1.0.0';
const buildTimestamp = import.meta.env.VITE_BUILD_TIMESTAMP || new Date().toISOString();

// Create and export configuration
export const config: AppConfig = {
  // API
  apiBaseUrl,
  apiTimeout: parseInt(import.meta.env.VITE_API_TIMEOUT || '30000', 10),

  // Environment
  environment,
  isProduction,
  isDevelopment,

  // Telegram
  telegramBotName,
  telegramAppUrl,

  // UI/UX
  ui,

  // Connectivity
  connectivity,

  // Features
  features,

  // Metadata
  appVersion,
  buildTimestamp,
};

// Validation
if (isProduction && !apiBaseUrl) {
  throw new Error('API_BASE_URL must be set in production environment');
}

// Debug logging in development
if (isDevelopment && features.enableDebugLogging) {
  console.log('App Configuration:', {
    environment,
    apiBaseUrl,
    telegramBotName,
    features,
    appVersion,
  });
}

// Environment-specific configurations
export const environments = {
  development: {
    apiBaseUrl: 'http://localhost:8000',
    enableLogging: true,
    enableDevTools: true,
  },
  production: {
    apiBaseUrl: 'https://calorie-track-ai-bot.fly.dev',
    enableLogging: false,
    enableDevTools: false,
  },
} as const;

// Utility functions
export const configUtils = {
  // Check if feature is enabled
  isFeatureEnabled: (feature: keyof AppConfig['features']): boolean => {
    return config.features[feature];
  },

  // Get API endpoint URL
  getApiUrl: (path: string): string => {
    const baseUrl = config.apiBaseUrl.endsWith('/')
      ? config.apiBaseUrl.slice(0, -1)
      : config.apiBaseUrl;
    const cleanPath = path.startsWith('/') ? path : `/${path}`;
    return `${baseUrl}${cleanPath}`;
  },

  // Check if running in Telegram
  isInTelegram: (): boolean => {
    return !!(window.Telegram?.WebApp);
  },

  // Get user language preference
  getUserLanguage: (): string => {
    // Try Telegram user language first
    if (window.Telegram?.WebApp?.initDataUnsafe?.user?.language_code) {
      const lang = window.Telegram.WebApp.initDataUnsafe.user.language_code;
      // Check if language is supported
      if (config.ui.supportedLanguages.includes(lang)) {
        return lang;
      }
      // Try language without region (e.g., 'en-US' -> 'en')
      const primaryLang = lang.split('-')[0];
      if (config.ui.supportedLanguages.includes(primaryLang)) {
        return primaryLang;
      }
    }

    // Fall back to browser language
    if (typeof navigator !== 'undefined' && navigator.language) {
      const browserLang = navigator.language.split('-')[0];
      if (config.ui.supportedLanguages.includes(browserLang as 'en' | 'ru')) {
        return browserLang;
      }
    }

    // Default language
    return config.ui.defaultLanguage;
  },

  // Get user theme preference
  getUserTheme: (): 'light' | 'dark' | 'auto' => {
    // Try Telegram theme first
    if (window.Telegram?.WebApp?.colorScheme) {
      return window.Telegram.WebApp.colorScheme as 'light' | 'dark';
    }

    // Try system preference
    if (typeof window !== 'undefined' && window.matchMedia) {
      const prefersDark = window.matchMedia('(prefers-color-scheme: dark)').matches;
      return prefersDark ? 'dark' : 'light';
    }

    // Default theme
    return config.ui.defaultTheme;
  },

  // Check if safe areas are needed
  needsSafeAreas: (): boolean => {
    if (!config.ui.enableSafeAreas) return false;

    // Check if device has safe areas
    if (typeof window !== 'undefined' && CSS.supports) {
      return CSS.supports('padding-top: env(safe-area-inset-top)');
    }

    return false;
  },

  // Get supported languages
  getSupportedLanguages: (): string[] => {
    return [...config.ui.supportedLanguages];
  },

  // Check if language is supported
  isLanguageSupported: (language: string): boolean => {
    return config.ui.supportedLanguages.includes(language as 'en' | 'ru');
  },

  // Log configuration info
  logConfig: (): void => {
    if (config.features.enableDebugLogging) {
      console.group('🔧 App Configuration');
      console.log('Environment:', config.environment);
      console.log('API Base URL:', config.apiBaseUrl);
      console.log('Version:', config.appVersion);
      console.log('Build Time:', config.buildTimestamp);
      console.log('Features:', config.features);
      console.log('Telegram Bot:', config.telegramBotName);
      console.groupEnd();
    }
  },

  // Validate environment
  validateEnvironment: (): boolean => {
    try {
      // Check required environment variables
      if (config.isProduction && !config.apiBaseUrl) {
        throw new Error('API base URL is required in production');
      }

      // Check API URL format
      if (config.apiBaseUrl && !config.apiBaseUrl.match(/^https?:\/\//)) {
        throw new Error('API base URL must be a valid HTTP/HTTPS URL');
      }

      return true;
    } catch (error) {
      console.error('Environment validation failed:', error);
      return false;
    }
  },
};

// Initialize configuration logging
if (config.features.enableDebugLogging) {
  configUtils.logConfig();
}

// Validate environment on load
if (!configUtils.validateEnvironment()) {
  throw new Error('Environment validation failed. Check console for details.');
}

export default config;
