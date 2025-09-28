import React from 'react';
import { configurationService as configService, LanguageDetectionResponse } from './config';

export type LanguageSource = 'telegram' | 'browser' | 'manual' | 'fallback';

export interface LanguageState {
  language: string;
  source: LanguageSource;
  telegramLanguage?: string;
  browserLanguage?: string;
  supportedLanguages: string[];
  isAutoDetectionEnabled: boolean;
}

export interface LanguageChangeEvent {
  language: string;
  source: LanguageSource;
  previousLanguage?: string;
  timestamp: number;
}

// Language detection service class
export class LanguageDetectionService {
  private static instance: LanguageDetectionService;
  private currentState: LanguageState;
  private listeners: Set<(event: LanguageChangeEvent) => void> = new Set();
  private languageChangeListener?: () => void;
  private isInitialized = false;

  // Supported languages for the application
  // Currently supporting English and Russian, with architecture ready for future expansion
  private readonly DEFAULT_SUPPORTED_LANGUAGES = [
    'en', // English
    'ru'  // Russian
  ];

  private constructor() {
    this.currentState = {
      language: 'en',
      source: 'fallback',
      supportedLanguages: this.DEFAULT_SUPPORTED_LANGUAGES,
      isAutoDetectionEnabled: true
    };
  }

  public static getInstance(): LanguageDetectionService {
    if (!LanguageDetectionService.instance) {
      LanguageDetectionService.instance = new LanguageDetectionService();
    }
    return LanguageDetectionService.instance;
  }

  /**
   * Initialize language detection service
   */
  async initialize(): Promise<void> {
    if (this.isInitialized) return;

    try {
      // Detect initial language
      await this.detectAndUpdateLanguage();

      // Set up language change listener
      this.setupLanguageChangeListener();

      this.isInitialized = true;
    } catch (error) {
      console.error('Failed to initialize language detection service:', error);
    }
  }

  /**
   * Get current language state
   */
  getLanguageState(): LanguageState {
    return { ...this.currentState };
  }

  /**
   * Set language manually
   */
  async setLanguage(language: string, source: LanguageSource = 'manual'): Promise<void> {
    // Validate language code format
    if (!this.isValidLanguageCode(language)) {
      console.warn(`Invalid language code format: ${language}`);
      return;
    }

    // Check if language is supported
    if (!this.isLanguageSupported(language)) {
      console.warn(`Invalid language code: ${language}`);
      return;
    }

    const previousLanguage = this.currentState.language;

    this.updateState({
      language,
      source
    });

    // Apply language to document
    this.applyLanguageToDocument(language);

    // Notify listeners
    this.notifyListeners({
      language,
      source,
      previousLanguage,
      timestamp: Date.now()
    });

    // Update backend configuration if auto-detection is enabled
    if (this.currentState.isAutoDetectionEnabled) {
      try {
        await configService.updateUIConfiguration({
          language: language as 'en' | 'ru',
          language_source: source as LanguageSource
        });
      } catch (error) {
        console.warn('Failed to update language configuration in backend:', error);
      }
    }
  }

  /**
   * Enable or disable auto language detection
   */
  setAutoDetection(enabled: boolean): void {
    this.updateState({
      isAutoDetectionEnabled: enabled
    });

    if (enabled) {
      this.detectAndUpdateLanguage();
    }
  }

  /**
   * Detect language from all sources and update
   */
  async detectAndUpdateLanguage(): Promise<void> {
    if (!this.currentState.isAutoDetectionEnabled) return;

    try {
      const detection = await configService.detectLanguage();
      const previousLanguage = this.currentState.language;

      this.updateState({
        language: detection.language,
        source: detection.language_source as LanguageSource,
        telegramLanguage: detection.telegram_language,
        browserLanguage: detection.browser_language,
        supportedLanguages: detection.supported_languages
      });

      // Apply language to document
      this.applyLanguageToDocument(detection.language);

      // Notify listeners if language changed
      if (previousLanguage !== detection.language) {
        this.notifyListeners({
          language: detection.language,
          source: detection.language_source as LanguageSource || 'fallback',
          previousLanguage,
          timestamp: Date.now()
        });
      }
    } catch (error) {
      console.error('Failed to detect language:', error);
    }
  }

  /**
   * Add language change listener
   */
  addListener(listener: (event: LanguageChangeEvent) => void): () => void {
    this.listeners.add(listener);

    // Return unsubscribe function
    return () => {
      this.listeners.delete(listener);
    };
  }

  /**
   * Remove all listeners
   */
  removeAllListeners(): void {
    this.listeners.clear();
  }

  /**
   * Get supported languages
   */
  getSupportedLanguages(): string[] {
    return [...this.currentState.supportedLanguages];
  }

  /**
   * Check if language is supported
   */
  isLanguageSupported(language: string): boolean {
    return this.currentState.supportedLanguages.includes(language);
  }

  /**
   * Get language display name
   */
  getLanguageDisplayName(language: string): string {
    const languageNames: Record<string, string> = {
      'en': 'English',
      'ru': 'Русский'
      // Future languages can be added here when needed:
      // 'es': 'Español',
      // 'fr': 'Français',
      // 'de': 'Deutsch',
      // etc.
    };

    return languageNames[language] || language.toUpperCase();
  }

  /**
   * Check if running in Telegram WebApp
   */
  isInTelegram(): boolean {
    return !!(typeof window !== 'undefined' && window.Telegram?.WebApp);
  }

  /**
   * Get Telegram user language if available
   */
  getTelegramUserLanguage(): string | null {
    if (!this.isInTelegram()) return null;

    const webApp = window.Telegram?.WebApp;
    const user = webApp?.initDataUnsafe?.user;
    return user?.language_code || null;
  }

  /**
   * Get browser language
   */
  getBrowserLanguage(): string | null {
    if (typeof navigator === 'undefined') return null;

    // Get primary language from navigator.language
    const browserLang = navigator.language;
    if (browserLang) {
      // Extract language code (e.g., 'en-US' -> 'en')
      return browserLang.split('-')[0];
    }

    return null;
  }

  /**
   * Dispose service and cleanup listeners
   */
  dispose(): void {
    this.removeAllListeners();
    this.isInitialized = false;
    // Reset state for testing
    this.currentState = {
      language: 'en',
      source: 'fallback',
      supportedLanguages: this.DEFAULT_SUPPORTED_LANGUAGES,
      isAutoDetectionEnabled: true
    };
  }

  // Private methods

  /**
   * Update internal state
   */
  private updateState(updates: Partial<LanguageState>): void {
    this.currentState = {
      ...this.currentState,
      ...updates
    };
  }

  /**
   * Apply language to document
   */
  private applyLanguageToDocument(language: string): void {
    if (typeof document !== 'undefined') {
      document.documentElement.setAttribute('lang', language);
      document.documentElement.setAttribute('data-language', language);
      document.documentElement.setAttribute('data-language-source', this.currentState.source);

      // Update CSS custom properties for language
      const root = document.documentElement;
      root.style.setProperty('--language', language);

      // Set text direction for RTL languages
      // Currently only supporting LTR languages (English, Russian)
      // RTL support can be added in the future: ['ar', 'he', 'fa', 'ur']
      const rtlLanguages: string[] = [];
      const direction = rtlLanguages.includes(language) ? 'rtl' : 'ltr';
      document.documentElement.setAttribute('dir', direction);
      root.style.setProperty('--text-direction', direction);
    }
  }

  /**
   * Validate language code format (ISO 639-1)
   */
  private isValidLanguageCode(language: string): boolean {
    // Basic ISO 639-1 format validation
    const iso639Pattern = /^[a-z]{2}(-[A-Z]{2})?$/;
    return iso639Pattern.test(language);
  }

  /**
   * Set up language change listener
   */
  private setupLanguageChangeListener(): void {
    // Listen for navigator.language changes (limited browser support)
    if (typeof window !== 'undefined') {
      this.languageChangeListener = () => {
        if (!this.currentState.isAutoDetectionEnabled) return;

        const newBrowserLanguage = this.getBrowserLanguage();
        if (newBrowserLanguage && newBrowserLanguage !== this.currentState.browserLanguage) {
          this.updateState({
            browserLanguage: newBrowserLanguage
          });

          // Re-detect language if current source is browser
          if (this.currentState.source === 'browser') {
            this.detectAndUpdateLanguage();
          }
        }
      };

      // Note: Most browsers don't support language change events
      // This is mainly for future compatibility
      window.addEventListener('languagechange', this.languageChangeListener);
    }
  }

  /**
   * Notify all listeners of language change
   */
  private notifyListeners(event: LanguageChangeEvent): void {
    this.listeners.forEach(listener => {
      try {
        listener(event);
      } catch (error) {
        console.error('Error in language change listener:', error);
      }
    });
  }
}

// Export singleton instance
export const languageDetectionService = LanguageDetectionService.getInstance();

// React hook for language detection
export const useLanguageDetection = () => {
  const [languageState, setLanguageState] = React.useState<LanguageState>(
    languageDetectionService.getLanguageState()
  );

  React.useEffect(() => {
    // Initialize service
    languageDetectionService.initialize();

    // Subscribe to language changes
    const unsubscribe = languageDetectionService.addListener((event) => {
      setLanguageState(languageDetectionService.getLanguageState());
    });

    // Update state immediately
    setLanguageState(languageDetectionService.getLanguageState());

    return unsubscribe;
  }, []);

  return {
    ...languageState,
    setLanguage: languageDetectionService.setLanguage.bind(languageDetectionService),
    setAutoDetection: languageDetectionService.setAutoDetection.bind(languageDetectionService),
    isLanguageSupported: languageDetectionService.isLanguageSupported.bind(languageDetectionService),
    getLanguageDisplayName: languageDetectionService.getLanguageDisplayName.bind(languageDetectionService),
    isInTelegram: languageDetectionService.isInTelegram(),
    telegramUserLanguage: languageDetectionService.getTelegramUserLanguage(),
    browserLanguage: languageDetectionService.getBrowserLanguage()
  };
};
