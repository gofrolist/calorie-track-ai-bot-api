// Frontend Configuration
// Environment-specific settings for the Calorie Track Mini App

export interface AppConfig {
  // API Configuration
  apiBaseUrl: string;
  apiTimeout: number;

  // Environment
  environment: 'development' | 'staging' | 'production';
  isProduction: boolean;
  isDevelopment: boolean;

  // Telegram WebApp
  telegramBotName?: string;
  telegramAppUrl?: string;

  // Features
  features: {
    enableDebugLogging: boolean;
    enableErrorReporting: boolean;
    enableAnalytics: boolean;
    enableDevTools: boolean;
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
  isDevelopment ? 'http://localhost:8000' : 'https://api.calorietrack.app'
);

// Telegram Configuration
const telegramBotName = import.meta.env.VITE_TELEGRAM_BOT_NAME;
const telegramAppUrl = import.meta.env.VITE_TELEGRAM_APP_URL;

// Feature flags
const features = {
  enableDebugLogging: getBooleanEnvVar('VITE_ENABLE_DEBUG_LOGGING', isDevelopment),
  enableErrorReporting: getBooleanEnvVar('VITE_ENABLE_ERROR_REPORTING', isProduction),
  enableAnalytics: getBooleanEnvVar('VITE_ENABLE_ANALYTICS', isProduction),
  enableDevTools: getBooleanEnvVar('VITE_ENABLE_DEV_TOOLS', isDevelopment),
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
  staging: {
    apiBaseUrl: 'https://staging-api.calorietrack.app',
    enableLogging: true,
    enableDevTools: false,
  },
  production: {
    apiBaseUrl: 'https://api.calorietrack.app',
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
  getUserLanguage: (): 'en' | 'ru' => {
    // Try Telegram user language first
    if (window.Telegram?.WebApp?.initDataUnsafe?.user?.language_code) {
      const lang = window.Telegram.WebApp.initDataUnsafe.user.language_code;
      if (lang.startsWith('ru')) return 'ru';
    }

    // Fall back to browser language
    const browserLang = navigator.language || 'en';
    return browserLang.startsWith('ru') ? 'ru' : 'en';
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
