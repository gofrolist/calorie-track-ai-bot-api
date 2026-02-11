import React, { useEffect, useState, useCallback, useRef } from 'react';

// TypeScript global declarations for analytics and window extensions
declare global {
  interface Window {
    gtag?: (...args: any[]) => void;
  }
}

export interface LanguageDetectionData {
  language: string;
  languageSource: 'telegram' | 'browser' | 'manual' | 'stored';
  telegramLanguageCode?: string;
  browserLanguages?: string[];
  detectedAt: Date;
  confidence?: 'high' | 'medium' | 'low';
}

export interface LanguageDetectionError {
  type: 'storage_error' | 'detection_error' | 'validation_error';
  message: string;
  context?: Record<string, unknown>;
}

export interface LanguageDetectorProps {
  onLanguageChange?: (languageData: LanguageDetectionData) => void;
  onError?: (error: LanguageDetectionError) => void;
  enableAutoDetection?: boolean;
  enableBrowserFallback?: boolean;
  defaultLanguage?: string;
  supportedLanguages?: string[];
  debugMode?: boolean;
  enableAnalytics?: boolean;
  debounceMs?: number;
  enableAccessibilityAnnouncement?: boolean;
}

/**
 * LanguageDetector component for automatic language detection from Telegram user data
 * and browser preferences with fallback handling.
 */
export const LanguageDetector: React.FC<LanguageDetectorProps> = ({
  onLanguageChange,
  onError,
  enableAutoDetection = true,
  enableBrowserFallback = true,
  defaultLanguage = 'en',
  supportedLanguages = ['en', 'ru', 'es', 'fr', 'de', 'it', 'pt', 'zh', 'ja', 'ko', 'ar'],
  debugMode = false,
  enableAnalytics = false,
  debounceMs = 300,
  enableAccessibilityAnnouncement = true
}) => {
  const [currentLanguage, setCurrentLanguage] = useState<LanguageDetectionData | null>(null);
  const [isInitialized, setIsInitialized] = useState(false);

  // Refs for debouncing and cleanup
  const debounceTimeoutRef = useRef<NodeJS.Timeout | null>(null);
  const lastDetectionRef = useRef<number>(0);
  const mountedRef = useRef(true);

  // Cleanup on unmount
  useEffect(() => {
    mountedRef.current = true;
    return () => {
      mountedRef.current = false;
      if (debounceTimeoutRef.current) {
        clearTimeout(debounceTimeoutRef.current);
      }
    };
  }, []);

  /**
   * Enhanced error reporting with analytics support
   */
  const reportError = useCallback((error: LanguageDetectionError) => {
    if (!mountedRef.current) return;

    // Call error callback if provided
    if (onError) {
      onError(error);
    }

    // Report to analytics if enabled (avoid exposing sensitive data)
    if (enableAnalytics && typeof window !== 'undefined') {
      try {
        // Example analytics call (implement based on your analytics provider)
        if (typeof window.gtag === 'function') {
          window.gtag('event', 'language_detection_error', {
            error_type: error.type,
            // Don't include the actual error message for privacy
            has_context: Boolean(error.context),
            timestamp: new Date().toISOString()
          });
        }
      } catch (analyticsError) {
        if (debugMode) {
          console.warn('LanguageDetector: Analytics reporting failed', analyticsError);
        }
      }
    }

    if (debugMode) {
      console.error('LanguageDetector: Error occurred', error);
    }
  }, [onError, enableAnalytics, debugMode]);

  /**
   * Enhanced localStorage operations with error reporting
   */
  const secureStorageGet = useCallback((key: string): string | null => {
    try {
      return localStorage.getItem(key);
    } catch (error) {
      reportError({
        type: 'storage_error',
        message: `Failed to read from localStorage: ${key}`,
        context: {
          key,
          errorType: error instanceof Error ? error.name : 'Unknown',
          // Don't include error message as it might contain sensitive info
          hasLocalStorage: typeof Storage !== 'undefined'
        }
      });
      return null;
    }
  }, [reportError]);

  const secureStorageSet = useCallback((key: string, value: string): boolean => {
    try {
      localStorage.setItem(key, value);
      return true;
    } catch (error) {
      reportError({
        type: 'storage_error',
        message: `Failed to write to localStorage: ${key}`,
        context: {
          key,
          errorType: error instanceof Error ? error.name : 'Unknown',
          hasLocalStorage: typeof Storage !== 'undefined',
          quotaExceeded: error instanceof Error && error.name === 'QuotaExceededError'
        }
      });
      return false;
    }
  }, [reportError]);

  /**
   * Enhanced language validation with confidence scoring
   */
  const validateLanguageCode = useCallback((code: string): { isValid: boolean; confidence: 'high' | 'medium' | 'low' } => {
    if (!code || typeof code !== 'string') {
      return { isValid: false, confidence: 'low' };
    }

    // Enhanced ISO 639-1 format validation
    const basicLanguageRegex = /^[a-z]{2}$/i;
    const languageWithRegionRegex = /^[a-z]{2}-[A-Z]{2}$/;
    const languageWithScriptRegex = /^[a-z]{2}-[A-Z][a-z]{3}(-[A-Z]{2})?$/;

    const normalizedCode = code.toLowerCase().trim();

    if (basicLanguageRegex.test(normalizedCode)) {
      return { isValid: true, confidence: 'high' };
    }

    if (languageWithRegionRegex.test(code)) {
      return { isValid: true, confidence: 'high' };
    }

    if (languageWithScriptRegex.test(code)) {
      return { isValid: true, confidence: 'medium' };
    }

    // Fallback for common variations
    if (normalizedCode.length === 2 && /^[a-z]+$/.test(normalizedCode)) {
      return { isValid: true, confidence: 'low' };
    }

    return { isValid: false, confidence: 'low' };
  }, []);

  /**
   * Extract primary language from language code (e.g., 'en-US' -> 'en')
   */
  const extractPrimaryLanguage = useCallback((languageCode: string): string => {
    if (!languageCode) return defaultLanguage;
    return languageCode.split('-')[0].toLowerCase();
  }, [defaultLanguage]);

  /**
   * Check if language is supported with enhanced validation
   */
  const isLanguageSupported = useCallback((language: string): boolean => {
    if (!language) return false;
    const primaryLang = extractPrimaryLanguage(language);
    return supportedLanguages.includes(primaryLang);
  }, [extractPrimaryLanguage, supportedLanguages]);

  /**
   * Accessibility announcement for language changes
   */
  const announceLanguageChange = useCallback((languageData: LanguageDetectionData) => {
    if (!enableAccessibilityAnnouncement || typeof document === 'undefined') return;

    try {
      // Create or update an aria-live region for screen readers
      let announcer = document.getElementById('language-detector-announcer');
      if (!announcer) {
        announcer = document.createElement('div');
        announcer.id = 'language-detector-announcer';
        announcer.setAttribute('aria-live', 'polite');
        announcer.setAttribute('aria-atomic', 'true');
        announcer.style.cssText = `
          position: absolute !important;
          width: 1px !important;
          height: 1px !important;
          padding: 0 !important;
          margin: -1px !important;
          overflow: hidden !important;
          clip: rect(0, 0, 0, 0) !important;
          white-space: nowrap !important;
        `;
        document.body.appendChild(announcer);
      }

      // Get language name for better accessibility
      const languageNames: Record<string, string> = {
        'en': 'English',
        'ru': 'Russian',
        'es': 'Spanish',
        'fr': 'French',
        'de': 'German',
        'it': 'Italian',
        'pt': 'Portuguese',
        'zh': 'Chinese',
        'ja': 'Japanese',
        'ko': 'Korean',
        'ar': 'Arabic'
      };

      const languageName = languageNames[languageData.language] || languageData.language;
      announcer.textContent = `Language changed to ${languageName}`;

      if (debugMode) {
        console.log('LanguageDetector: Accessibility announcement made', languageName);
      }
    } catch {
      reportError({
        type: 'detection_error',
        message: 'Failed to announce language change for accessibility',
        context: { language: languageData.language }
      });
    }
  }, [enableAccessibilityAnnouncement, debugMode, reportError]);

  /**
   * Enhanced browser language detection with quality scoring
   */
  const detectBrowserLanguage = useCallback((): {
    languages: string[];
    primary?: string;
    confidence?: 'high' | 'medium' | 'low';
    qualityScores?: Array<{ language: string; quality: number; supported: boolean }>;
  } => {
    const result: ReturnType<typeof detectBrowserLanguage> = {
      languages: [],
      primary: undefined,
      confidence: 'low',
      qualityScores: []
    };

    try {
      if (typeof navigator === 'undefined') return result;

      // Get browser languages with quality values (simplified Accept-Language parsing)
      const browserLanguages: Array<{ language: string; quality: number }> = [];

      // Primary language always has quality 1.0
      if (navigator.language) {
        browserLanguages.push({ language: navigator.language, quality: 1.0 });
      }

      // Additional languages from navigator.languages
      if (navigator.languages) {
        navigator.languages.forEach((lang, index) => {
          if (lang !== navigator.language) {
            // Assign decreasing quality scores
            const quality = Math.max(0.1, 1.0 - (index * 0.1));
            browserLanguages.push({ language: lang, quality });
          }
        });
      }

      // Remove duplicates and sort by quality
      const uniqueLanguages = Array.from(
        new Map(browserLanguages.map(item => [item.language, item])).values()
      ).sort((a, b) => b.quality - a.quality);

      result.languages = uniqueLanguages.map(item => item.language);
      result.qualityScores = uniqueLanguages.map(item => {
        const validation = validateLanguageCode(item.language);
        return {
          language: item.language,
          quality: item.quality,
          supported: validation.isValid && isLanguageSupported(item.language)
        };
      });

      // Find best supported language
      for (const item of uniqueLanguages) {
        const validation = validateLanguageCode(item.language);
        if (validation.isValid && isLanguageSupported(item.language)) {
          result.primary = extractPrimaryLanguage(item.language);
          result.confidence = item.quality > 0.8 ? 'high' : item.quality > 0.5 ? 'medium' : 'low';
          break;
        }
      }

      if (debugMode) {
        console.log('LanguageDetector: Enhanced browser language detection', {
          detected: result.primary,
          confidence: result.confidence,
          qualityScores: result.qualityScores,
          supportedLanguages
        });
      }
    } catch {
      reportError({
        type: 'detection_error',
        message: 'Failed to detect browser languages',
        context: {
          hasNavigator: typeof navigator !== 'undefined',
          hasLanguage: typeof navigator?.language !== 'undefined',
          hasLanguages: typeof navigator?.languages !== 'undefined'
        }
      });
    }

    return result;
  }, [validateLanguageCode, isLanguageSupported, extractPrimaryLanguage, supportedLanguages, debugMode, reportError]);

  /**
   * Enhanced Telegram language detection with better error handling
   */
  const detectTelegramLanguage = useCallback((): {
    languageCode?: string;
    isValid?: boolean;
    confidence?: 'high' | 'medium' | 'low';
    source?: 'telegram_user' | 'url_param';
  } => {
    try {
      // Check if Telegram WebApp is available and has user data
      if (typeof window !== 'undefined' && window.Telegram?.WebApp?.initDataUnsafe?.user) {
        const user = window.Telegram.WebApp.initDataUnsafe.user;

        if (user?.language_code) {
          const languageCode = user.language_code;
          const validation = validateLanguageCode(languageCode);
          const isValid = validation.isValid && isLanguageSupported(languageCode);

          if (debugMode && !isValid) {
            console.log('LanguageDetector: Telegram language not supported', {
              languageCode,
              validation,
              supportedLanguages
            });
          }

          if (debugMode) {
            console.log('LanguageDetector: Telegram language detected', {
              languageCode,
              isValid,
              confidence: validation.confidence,
              // Don't log full user object for privacy
              hasUser: Boolean(user)
            });
          }

          return {
            languageCode,
            isValid,
            confidence: validation.confidence,
            source: 'telegram_user'
          };
        }

        if (debugMode) {
          console.log('LanguageDetector: No language code in Telegram user data');
        }
      }

      // Alternative: Check if language code is available in URL parameters
      if (typeof window !== 'undefined') {
        const urlParams = new URLSearchParams(window.location.search);
        const langParam = urlParams.get('lang') || urlParams.get('language');

        if (langParam) {
          const validation = validateLanguageCode(langParam);
          const isValid = validation.isValid && isLanguageSupported(langParam);

          if (debugMode) {
            console.log('LanguageDetector: Language from URL parameter', {
              langParam,
              isValid,
              confidence: validation.confidence
            });
          }

          return {
            languageCode: langParam,
            isValid,
            confidence: validation.confidence,
            source: 'url_param'
          };
        }
      }

      return {};
    } catch {
      reportError({
        type: 'detection_error',
        message: 'Failed to detect Telegram language',
        context: {
          hasTelegram: typeof window?.Telegram !== 'undefined',
          hasWebApp: typeof window?.Telegram?.WebApp !== 'undefined',
          hasInitData: typeof window?.Telegram?.WebApp?.initDataUnsafe !== 'undefined'
        }
      });
      return {};
    }
  }, [validateLanguageCode, isLanguageSupported, debugMode, reportError, supportedLanguages]);

  /**
   * Enhanced language detection with confidence scoring
   */
  const performLanguageDetection = useCallback((): LanguageDetectionData => {
    const telegramLang = detectTelegramLanguage();
    const browserLang = detectBrowserLanguage();

    let language: string;
    let languageSource: LanguageDetectionData['languageSource'];
    let confidence: LanguageDetectionData['confidence'] = 'low';

    // Prioritize Telegram language if available and valid
    if (telegramLang.languageCode && telegramLang.isValid) {
      language = extractPrimaryLanguage(telegramLang.languageCode);
      languageSource = 'telegram';
      confidence = telegramLang.confidence || 'high';
    } else if (enableBrowserFallback && browserLang.primary) {
      // Fall back to browser preference
      language = browserLang.primary;
      languageSource = 'browser';
      confidence = browserLang.confidence || 'medium';
    } else {
      // Use default language
      language = defaultLanguage;
      languageSource = 'manual';
      confidence = 'low';
    }

    const languageData: LanguageDetectionData = {
      language,
      languageSource,
      telegramLanguageCode: telegramLang.languageCode,
      browserLanguages: browserLang.languages,
      detectedAt: new Date(),
      confidence
    };

    if (debugMode) {
      console.log('LanguageDetector: Enhanced language detection completed', {
        ...languageData,
        telegramConfidence: telegramLang.confidence,
        browserConfidence: browserLang.confidence,
        telegramSource: telegramLang.source
      });
    }

    return languageData;
  }, [
    detectTelegramLanguage,
    detectBrowserLanguage,
    extractPrimaryLanguage,
    enableBrowserFallback,
    defaultLanguage,
    debugMode
  ]);

  /**
   * Apply language to document and internationalization with enhanced storage
   */
  const applyLanguage = useCallback((languageData: LanguageDetectionData) => {
    if (typeof document !== 'undefined') {
      // Set lang attribute on document element
      document.documentElement.lang = languageData.language;

      // Set dir attribute for RTL languages
      const rtlLanguages = ['ar', 'he', 'fa', 'ur'];
      const isRTL = rtlLanguages.includes(languageData.language);
      document.documentElement.dir = isRTL ? 'rtl' : 'ltr';

      // Store language preference with enhanced error handling
      secureStorageSet('preferred-language', languageData.language);
      secureStorageSet('language-source', languageData.languageSource);

      // Store additional metadata for analytics
      if (languageData.confidence) {
        secureStorageSet('language-confidence', languageData.confidence);
      }

      // Announce language change for accessibility
      announceLanguageChange(languageData);

      if (debugMode) {
        console.log('LanguageDetector: Language applied to document', {
          language: languageData.language,
          dir: isRTL ? 'rtl' : 'ltr',
          confidence: languageData.confidence,
          source: languageData.languageSource
        });
      }
    }
  }, [secureStorageSet, announceLanguageChange, debugMode]);

  /**
   * Debounced language change handler to prevent excessive detection calls
   */
  const handleLanguageChange = useCallback(() => {
    if (!mountedRef.current) return;

    const now = Date.now();

    // Throttle rapid successive calls
    if (now - lastDetectionRef.current < 100) {
      return;
    }

    lastDetectionRef.current = now;

    // Clear existing timeout
    if (debounceTimeoutRef.current) {
      clearTimeout(debounceTimeoutRef.current);
    }

    // Debounce the actual detection
    debounceTimeoutRef.current = setTimeout(() => {
      if (!mountedRef.current) return;

      try {
        const languageData = performLanguageDetection();
        setCurrentLanguage(languageData);
        applyLanguage(languageData);

        if (onLanguageChange) {
          onLanguageChange(languageData);
        }
      } catch {
        reportError({
          type: 'detection_error',
          message: 'Failed to handle language change',
          context: { timestamp: new Date().toISOString() }
        });
      }
    }, debounceMs);
  }, [performLanguageDetection, applyLanguage, onLanguageChange, debounceMs, reportError]);


  /**
   * Enhanced initialization with better error handling and stored preferences
   */
  useEffect(() => {
    if (!enableAutoDetection || !mountedRef.current) return;

    const initializeLanguageDetection = async () => {
      try {
        // Check for stored language preference first
        const storedLanguage = secureStorageGet('preferred-language');
        const storedSource = secureStorageGet('language-source');
        const storedConfidence = secureStorageGet('language-confidence');

        if (storedLanguage && isLanguageSupported(storedLanguage)) {
          const languageData: LanguageDetectionData = {
            language: storedLanguage,
            languageSource: (storedSource as LanguageDetectionData['languageSource']) || 'stored',
            confidence: (storedConfidence as LanguageDetectionData['confidence']) || 'medium',
            detectedAt: new Date()
          };

          if (mountedRef.current) {
            setCurrentLanguage(languageData);
            applyLanguage(languageData);

            if (onLanguageChange) {
              onLanguageChange(languageData);
            }

            if (debugMode) {
              console.log('LanguageDetector: Using stored language preference', {
                language: storedLanguage,
                source: storedSource,
                confidence: storedConfidence
              });
            }
          }
        } else {
          // Perform fresh detection
          if (mountedRef.current) {
            handleLanguageChange();
          }
        }

        if (mountedRef.current) {
          setIsInitialized(true);
        }
      } catch {
        reportError({
          type: 'detection_error',
          message: 'Failed to initialize language detection',
          context: {
            enableAutoDetection,
            hasStoredLanguage: Boolean(secureStorageGet('preferred-language'))
          }
        });

        if (mountedRef.current) {
          setIsInitialized(true);
        }
      }
    };

    initializeLanguageDetection();
  }, [enableAutoDetection, applyLanguage, debugMode, handleLanguageChange, isLanguageSupported, onLanguageChange, reportError, secureStorageGet]);

  /**
   * Enhanced public method to manually set language
   * Note: This method is available but not currently used externally
   */
  // eslint-disable-next-line @typescript-eslint/no-unused-vars
  const setLanguage = useCallback((language: string) => {
    if (!mountedRef.current) return;

    const validation = validateLanguageCode(language);
    if (!validation.isValid || !isLanguageSupported(language)) {
      reportError({
        type: 'validation_error',
        message: `Unsupported language: ${language}`,
        context: {
          language,
          validation,
          supportedLanguages
        }
      });
      return;
    }

    const languageData: LanguageDetectionData = {
      language: extractPrimaryLanguage(language),
      languageSource: 'manual',
      confidence: validation.confidence,
      detectedAt: new Date()
    };

    setCurrentLanguage(languageData);
    applyLanguage(languageData);

    if (onLanguageChange) {
      onLanguageChange(languageData);
    }

    if (debugMode) {
      console.log('LanguageDetector: Language manually set', {
        language,
        confidence: validation.confidence,
        supported: true
      });
    }
  }, [
    validateLanguageCode,
    isLanguageSupported,
    extractPrimaryLanguage,
    applyLanguage,
    onLanguageChange,
    debugMode,
    reportError,
    supportedLanguages
  ]);

  // Note: For imperative access to methods, use a ref from parent component

  // Enhanced debug information display
  if (debugMode && currentLanguage) {
    return (
      <div className="language-detector-debug" style={{
        position: 'fixed',
        top: '60px',
        right: '10px',
        background: 'rgba(0, 0, 0, 0.9)',
        color: '#00ff00',
        padding: '10px 14px',
        borderRadius: '6px',
        fontSize: '11px',
        zIndex: 9999,
        fontFamily: 'Monaco, Consolas, monospace',
        maxWidth: '280px',
        border: '1px solid #333',
        boxShadow: '0 4px 12px rgba(0, 0, 0, 0.5)'
      }}>
        <div style={{ borderBottom: '1px solid #333', paddingBottom: '6px', marginBottom: '6px' }}>
          <strong style={{ color: '#fff' }}>🌐 Language Detector</strong>
        </div>
        <div><strong>Language:</strong> <span style={{ color: '#ffff00' }}>{currentLanguage.language}</span></div>
        <div><strong>Source:</strong> <span style={{ color: '#00ffff' }}>{currentLanguage.languageSource}</span></div>
        {currentLanguage.confidence && (
          <div><strong>Confidence:</strong> <span style={{
            color: currentLanguage.confidence === 'high' ? '#00ff00' :
                  currentLanguage.confidence === 'medium' ? '#ffff00' : '#ff9900'
          }}>{currentLanguage.confidence}</span></div>
        )}
        {currentLanguage.telegramLanguageCode && (
          <div><strong>Telegram:</strong> {currentLanguage.telegramLanguageCode}</div>
        )}
        {currentLanguage.browserLanguages && currentLanguage.browserLanguages.length > 0 && (
          <div><strong>Browser:</strong> {currentLanguage.browserLanguages.slice(0, 2).join(', ')}</div>
        )}
        <div style={{ fontSize: '10px', marginTop: '6px' }}>
          <div><strong>Supported:</strong> {supportedLanguages.slice(0, 6).join(', ')}{supportedLanguages.length > 6 ? '...' : ''}</div>
          <div><strong>Detected:</strong> {currentLanguage.detectedAt.toLocaleTimeString()}</div>
          <div><strong>Initialized:</strong> {isInitialized ? '✅' : '⏳'}</div>
          <div><strong>Dir:</strong> {document.documentElement.dir || 'ltr'}</div>
        </div>
      </div>
    );
  }

  // Component is invisible in production mode
  return null;
};

export default LanguageDetector;
