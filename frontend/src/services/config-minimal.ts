/**
 * Minimal configuration service for build fixes
 * Temporary replacement to resolve circular imports
 */

// Basic types needed for compilation
export interface UIConfiguration {
  api_base_url?: string;
  theme?: 'light' | 'dark' | 'auto';
  language?: 'en' | 'ru';
  language_source?: string;
  safe_area_top?: number;
  safe_area_bottom?: number;
  safe_area_left?: number;
  safe_area_right?: number;
  features?: Record<string, boolean>;
}

export interface UIConfigurationUpdate extends Partial<UIConfiguration> {}

export interface ThemeDetectionResponse {
  theme: 'light' | 'dark' | 'auto';
  source: string;
  automatic: boolean;
  timestamp: string;
}

export interface LanguageDetectionResponse {
  language: 'en' | 'ru';
  source: string;
  timestamp: string;
  supported_languages: ('en' | 'ru')[];
  language_source?: string;
  telegram_language?: 'en' | 'ru';
  browser_language?: 'en' | 'ru';
}

// Minimal service implementation
export class ConfigurationService {
  async getUIConfiguration(): Promise<UIConfiguration> {
    return {
      theme: 'light',
      language: 'en',
      api_base_url: 'http://localhost:8000',
    };
  }

  async updateUIConfiguration(config: UIConfigurationUpdate): Promise<UIConfiguration> {
    return config as UIConfiguration;
  }

  async detectTheme(): Promise<ThemeDetectionResponse> {
    return {
      theme: 'light',
      source: 'fallback',
      automatic: true,
      timestamp: new Date().toISOString(),
    };
  }

  async detectLanguage(): Promise<LanguageDetectionResponse> {
    return {
      language: 'en',
      source: 'fallback',
      timestamp: new Date().toISOString(),
      supported_languages: ['en', 'ru'],
    };
  }

  // Additional methods to match expected interface
  clearCache(): void {}
  clearCacheEntry(key: string): void {}
  getConfiguration(userId: string, options?: any): Promise<UIConfiguration> {
    return this.getUIConfiguration();
  }
  setConfiguration(userId: string, config: UIConfigurationUpdate, options?: any): Promise<UIConfiguration> {
    return this.updateUIConfiguration(config);
  }
  getTheme(): string { return 'light'; }
  setTheme(theme: string): void {}
  getLanguage(userId: string): Promise<string> { return Promise.resolve('en'); }
  setLanguage(userId: string): void {}
}

// Export singleton instance
export const configurationService = new ConfigurationService();

// Additional utility functions for compatibility
export const isFeatureEnabled = (featureName: string): boolean => false;
export const getFeatureValue = (featureName: string): any => false;
export const getSafeAreaValue = (side: string): number => 0;
export const hasSafeAreas = (): boolean => false;
export const isDevelopment = (): boolean => true;
export const isProduction = (): boolean => false;
