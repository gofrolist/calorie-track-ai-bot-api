/**
 * Simple configuration service replacement
 * Simplified wrapper to resolve build issues
 */

import { config } from '../config';
import {
  configurationService,
  ConfigurationService,
  UIConfiguration,
  UIConfigurationUpdate,
  ThemeDetectionResponse,
  LanguageDetectionResponse,
} from './config-minimal';

// Simple legacy compatibility wrappers
export const getConfiguration = async (_userId: string): Promise<UIConfiguration> => {
  return configurationService.getUIConfiguration();
};

export const setConfiguration = async (userId: string, config: UIConfigurationUpdate): Promise<UIConfiguration> => {
  return configurationService.updateUIConfiguration(config);
};

export const getTheme = (): string => {
  return configurationService.getTheme();
};

export const setTheme = (theme: string): void => {
  configurationService.setTheme(theme);
};

export const getLanguage = async (userId: string): Promise<string> => {
  return configurationService.getLanguage(userId);
};

export const setLanguage = (userId: string): void => {
  configurationService.setLanguage(userId);
};

export const clearCache = (): void => {
  configurationService.clearCache();
};

export const clearCacheEntry = (key: string): void => {
  configurationService.clearCacheEntry(key);
};

// Simple utilities
export const isFeatureEnabled = (_featureName: string): boolean => {
  return config.features?.enableDebugLogging || false;
};

export const getFeatureValue = (_featureName: string): any => {
  return false;
};

export const getSafeAreaValue = (_side: string): number => {
  return 0;
};

export const hasSafeAreas = (): boolean => {
  return config.ui?.enableSafeAreas || false;
};

export const isDevelopment = (): boolean => {
  return config.environment === 'development';
};

export const isProduction = (): boolean => {
  return config.environment === 'production';
};

// Export everything for compatibility
export {
  configurationService,
  ConfigurationService,
};

export type {
  UIConfiguration,
  UIConfigurationUpdate,
  ThemeDetectionResponse,
  LanguageDetectionResponse,
};
