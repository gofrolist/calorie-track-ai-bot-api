import React, { useEffect, useState, useCallback, useRef } from 'react';

// TypeScript global declarations for Telegram WebApp and analytics
declare global {
  interface Window {
    gtag?: (...args: any[]) => void;
    Telegram?: {
      WebApp?: {
        colorScheme?: 'light' | 'dark';
        themeParams?: {
          bg_color?: string;
          text_color?: string;
          hint_color?: string;
          link_color?: string;
          button_color?: string;
          button_text_color?: string;
          secondary_bg_color?: string;
          [key: string]: any;
        };
        onEvent?: (eventType: string, callback: () => void) => void;
        offEvent?: (eventType: string, callback: () => void) => void;
        [key: string]: any;
      };
    };
  }
}

export interface ThemeDetectionData {
  theme: 'light' | 'dark' | 'auto';
  themeSource: 'telegram' | 'system' | 'manual' | 'stored';
  telegramColorScheme?: 'light' | 'dark';
  systemPrefersDark?: boolean;
  detectedAt: Date;
  confidence?: 'high' | 'medium' | 'low';
}

export interface ThemeDetectionError {
  type: 'storage_error' | 'detection_error' | 'validation_error';
  message: string;
  context?: Record<string, unknown>;
}

export interface ThemeDetectorProps {
  onThemeChange?: (themeData: ThemeDetectionData) => void;
  onError?: (error: ThemeDetectionError) => void;
  enableAutoDetection?: boolean;
  enableSystemFallback?: boolean;
  enableTelegramListener?: boolean;
  debugMode?: boolean;
  enableAnalytics?: boolean;
  debounceMs?: number;
  enableAccessibilityAnnouncement?: boolean;
}

/**
 * ThemeDetector component for automatic theme detection from Telegram WebApp API
 * and system preferences with fallback handling.
 */
export const ThemeDetector: React.FC<ThemeDetectorProps> = ({
  onThemeChange,
  onError,
  enableAutoDetection = true,
  enableSystemFallback = true,
  enableTelegramListener = true,
  debugMode = false,
  enableAnalytics = false,
  debounceMs = 250,
  enableAccessibilityAnnouncement = true
}) => {
  const [currentTheme, setCurrentTheme] = useState<ThemeDetectionData | null>(null);
  const [isInitialized, setIsInitialized] = useState(false);

  // Refs for debouncing, cleanup, and Telegram listener
  const debounceTimeoutRef = useRef<NodeJS.Timeout | null>(null);
  const lastDetectionRef = useRef<number>(0);
  const mountedRef = useRef(true);
  const telegramListenerRef = useRef<(() => void) | null>(null);
  const onThemeChangeRef = useRef(onThemeChange);

  // Update ref when onThemeChange changes
  useEffect(() => {
    onThemeChangeRef.current = onThemeChange;
  }, [onThemeChange]);

  // Cleanup on unmount
  useEffect(() => {
    mountedRef.current = true;
    return () => {
      mountedRef.current = false;
      if (debounceTimeoutRef.current) {
        clearTimeout(debounceTimeoutRef.current);
      }
      // Clean up Telegram listener
      if (telegramListenerRef.current) {
        telegramListenerRef.current();
        telegramListenerRef.current = null;
      }
    };
  }, []);

  /**
   * Enhanced error reporting with analytics support
   */
  const reportError = useCallback((error: ThemeDetectionError) => {
    if (!mountedRef.current) return;

    // Call error callback if provided
    if (onError) {
      onError(error);
    }

    // Report to analytics if enabled (privacy-safe)
    if (enableAnalytics && typeof window !== 'undefined') {
      try {
        if (typeof window.gtag === 'function') {
          window.gtag('event', 'theme_detection_error', {
            error_type: error.type,
            has_context: Boolean(error.context),
            timestamp: new Date().toISOString()
          });
        }
      } catch (analyticsError) {
        if (debugMode) {
          console.warn('ThemeDetector: Analytics reporting failed', analyticsError);
        }
      }
    }

    if (debugMode) {
      console.error('ThemeDetector: Error occurred');
    }
  }, [enableAnalytics, debugMode, onError]);

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
   * Accessibility announcement for theme changes
   */
  const announceThemeChange = useCallback((themeData: ThemeDetectionData) => {
    if (!enableAccessibilityAnnouncement || typeof document === 'undefined') return;

    try {
      let announcer = document.getElementById('theme-detector-announcer');
      if (!announcer) {
        announcer = document.createElement('div');
        announcer.id = 'theme-detector-announcer';
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

      const themeNames = {
        'light': 'Light theme',
        'dark': 'Dark theme',
        'auto': 'Automatic theme'
      };

      const themeName = themeNames[themeData.theme] || themeData.theme;
      announcer.textContent = `Theme changed to ${themeName}`;

      if (debugMode) {
        console.log('ThemeDetector: Accessibility announcement made', themeName);
      }
    } catch {
      reportError({
        type: 'detection_error',
        message: 'Failed to announce theme change for accessibility',
        context: { theme: themeData.theme }
      });
    }
  }, [enableAccessibilityAnnouncement, debugMode, reportError]);

  /**
   * Enhanced system theme detection with confidence scoring
   */
  const detectSystemTheme = useCallback((): { prefersDark: boolean; confidence: 'high' | 'medium' | 'low' } => {
    try {
      if (typeof window !== 'undefined' && window.matchMedia) {
        const darkModeQuery = window.matchMedia('(prefers-color-scheme: dark)');
        const lightModeQuery = window.matchMedia('(prefers-color-scheme: light)');

        // High confidence if either dark or light is explicitly supported
        if (darkModeQuery.matches) {
          return { prefersDark: true, confidence: 'high' };
        }
        if (lightModeQuery.matches) {
          return { prefersDark: false, confidence: 'high' };
        }

        // Medium confidence if media queries are supported but no preference
        if (darkModeQuery.media !== 'not all' || lightModeQuery.media !== 'not all') {
          return { prefersDark: false, confidence: 'medium' };
        }
      }
    } catch {
      reportError({
        type: 'detection_error',
        message: 'Failed to detect system theme',
        context: {
          hasMatchMedia: typeof window?.matchMedia !== 'undefined'
        }
      });
    }

    // Low confidence fallback
    return { prefersDark: false, confidence: 'low' };
  }, [reportError]);

  /**
   * Enhanced Telegram theme detection with confidence scoring
   */
  const detectTelegramTheme = useCallback((): {
    colorScheme?: 'light' | 'dark';
    isDark?: boolean;
    confidence?: 'high' | 'medium' | 'low';
    hasThemeParams?: boolean;
  } => {
    try {
      if (typeof window !== 'undefined' && window.Telegram?.WebApp) {
        const webApp = window.Telegram.WebApp;
        const colorScheme = webApp.colorScheme;

        if (colorScheme === 'dark' || colorScheme === 'light') {
          const isDark = colorScheme === 'dark';
          const hasThemeParams = Boolean(webApp.themeParams && Object.keys(webApp.themeParams).length > 0);

          if (debugMode) {
            console.log('ThemeDetector: Telegram theme detected', {
              colorScheme,
              isDark,
              hasThemeParams,
              themeParamsCount: webApp.themeParams ? Object.keys(webApp.themeParams).length : 0
            });
          }

          return {
            colorScheme,
            isDark,
            confidence: 'high',
            hasThemeParams
          };
        } else if (webApp.colorScheme !== undefined) {
          // WebApp exists but colorScheme is unexpected
          if (debugMode) {
            console.log('ThemeDetector: Telegram WebApp present but invalid colorScheme', webApp.colorScheme);
          }
          return { confidence: 'low' };
        }
      }

      return {};
    } catch {
      reportError({
        type: 'detection_error',
        message: 'Failed to detect Telegram theme',
        context: {
          hasTelegram: typeof window?.Telegram !== 'undefined',
          hasWebApp: typeof window?.Telegram?.WebApp !== 'undefined',
          hasColorScheme: typeof window?.Telegram?.WebApp?.colorScheme !== 'undefined'
        }
      });
      return {};
    }
  }, [debugMode, reportError]);

  /**
   * Enhanced theme detection with confidence scoring
   */
  const performThemeDetection = useCallback((): ThemeDetectionData => {
    const systemTheme = detectSystemTheme();
    const telegramTheme = detectTelegramTheme();

    let theme: 'light' | 'dark' | 'auto';
    let themeSource: ThemeDetectionData['themeSource'];
    let confidence: ThemeDetectionData['confidence'] = 'low';

    // Prioritize Telegram theme if available and valid
    if (telegramTheme.colorScheme && telegramTheme.confidence === 'high') {
      theme = telegramTheme.colorScheme;
      themeSource = 'telegram';
      confidence = 'high';
    } else if (enableSystemFallback && systemTheme.confidence !== 'low') {
      // Fall back to system preference
      theme = systemTheme.prefersDark ? 'dark' : 'light';
      themeSource = 'system';
      confidence = systemTheme.confidence;
    } else {
      // Default to auto mode with enhanced fallback logic
      theme = 'auto';
      themeSource = 'manual';
      confidence = 'low';
    }

    const themeData: ThemeDetectionData = {
      theme,
      themeSource,
      telegramColorScheme: telegramTheme.colorScheme,
      systemPrefersDark: systemTheme.prefersDark,
      confidence,
      detectedAt: new Date()
    };

    if (debugMode) {
      console.log('ThemeDetector: Enhanced theme detection completed', {
        ...themeData,
        telegramConfidence: telegramTheme.confidence,
        systemConfidence: systemTheme.confidence,
        hasThemeParams: telegramTheme.hasThemeParams
      });
    }

    return themeData;
  }, [detectSystemTheme, detectTelegramTheme, enableSystemFallback, debugMode]);

  /**
   * Enhanced theme application with secure storage and accessibility
   */
  const applyTheme = useCallback((themeData: ThemeDetectionData) => {
    if (typeof document !== 'undefined') {
      // Set data-theme attribute on document element
      document.documentElement.setAttribute('data-theme', themeData.theme);

      // Apply Telegram theme colors if available
      if (typeof window !== 'undefined' && window.Telegram?.WebApp?.themeParams) {
        const telegramThemeParams = window.Telegram.WebApp.themeParams;
        const root = document.documentElement;

        // Define theme color mappings for better maintainability
        const colorMappings = [
          { param: 'bg_color', property: '--tg-bg-color' },
          { param: 'text_color', property: '--tg-text-color' },
          { param: 'hint_color', property: '--tg-hint-color' },
          { param: 'link_color', property: '--tg-link-color' },
          { param: 'button_color', property: '--tg-button-color' },
          { param: 'button_text_color', property: '--tg-button-text-color' },
          { param: 'secondary_bg_color', property: '--tg-secondary-bg-color' }
        ];

        // Apply theme colors safely
        colorMappings.forEach(({ param, property }) => {
          const colorValue = telegramThemeParams[param];
          if (colorValue && typeof colorValue === 'string') {
            root.style.setProperty(property, colorValue);
          }
        });
      }

      // Store theme preference with enhanced error handling
      secureStorageSet('preferred-theme', themeData.theme);
      secureStorageSet('theme-source', themeData.themeSource);

      if (themeData.confidence) {
        secureStorageSet('theme-confidence', themeData.confidence);
      }

      // Announce theme change for accessibility
      announceThemeChange(themeData);

      if (debugMode) {
        console.log('ThemeDetector: Theme applied to document', {
          theme: themeData.theme,
          source: themeData.themeSource,
          confidence: themeData.confidence,
          hasThemeParams: Boolean(window?.Telegram?.WebApp?.themeParams)
        });
      }
    }
  }, [secureStorageSet, announceThemeChange, debugMode]);

  /**
   * Debounced theme change handler to prevent excessive detection calls
   */
  const handleThemeChange = useCallback(() => {
    if (!mountedRef.current) return;

    const now = Date.now();

    // Throttle rapid successive calls
    if (now - lastDetectionRef.current < 50) {
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
        const themeData = performThemeDetection();
        setCurrentTheme(themeData);
        applyTheme(themeData);

        if (onThemeChangeRef.current) {
          onThemeChangeRef.current(themeData);
        }
      } catch {
        reportError({
          type: 'detection_error',
          message: 'Failed to handle theme change',
          context: { timestamp: new Date().toISOString() }
        });
      }
    }, debounceMs);
  }, [performThemeDetection, applyTheme, debounceMs, reportError]);

  /**
   * Set up Telegram theme change listener
   */
  const setupTelegramListener = useCallback(() => {
    if (!enableTelegramListener || typeof window === 'undefined' || !window.Telegram?.WebApp?.onEvent) {
      return null;
    }

    try {
      const webApp = window.Telegram.WebApp;

      const handleTelegramThemeChange = () => {
        if (debugMode) {
          console.log('ThemeDetector: Telegram theme change event received');
        }

        // Debounced theme change detection
        handleThemeChange();
      };

      // Set up Telegram theme change listener
      if (typeof webApp.onEvent === 'function') {
        webApp.onEvent('themeChanged', handleTelegramThemeChange);

        // Return cleanup function
        return () => {
          if (typeof webApp.offEvent === 'function') {
            webApp.offEvent('themeChanged', handleTelegramThemeChange);
          }
        };
      }
    } catch {
      reportError({
        type: 'detection_error',
        message: 'Failed to set up Telegram theme listener',
        context: {
          enableTelegramListener,
          hasOnEvent: typeof window?.Telegram?.WebApp?.onEvent !== 'undefined',
          hasOffEvent: typeof window?.Telegram?.WebApp?.offEvent !== 'undefined'
        }
      });
    }

    return null;
  }, [enableTelegramListener, debugMode, reportError, handleThemeChange]);

  /**
   * Enhanced initialization with Telegram listener and stored preferences
   */
  useEffect(() => {
    if (!enableAutoDetection || !mountedRef.current) return;

    const initializeThemeDetection = async () => {
      try {
        // Check for stored theme preference first
        const storedTheme = secureStorageGet('preferred-theme');
        const storedSource = secureStorageGet('theme-source');
        const storedConfidence = secureStorageGet('theme-confidence');

        // Validate stored theme
        const isValidTheme = storedTheme && ['light', 'dark', 'auto'].includes(storedTheme);

        if (isValidTheme) {
          const themeData: ThemeDetectionData = {
            theme: storedTheme as 'light' | 'dark' | 'auto',
            themeSource: (storedSource as ThemeDetectionData['themeSource']) || 'stored',
            confidence: (storedConfidence as ThemeDetectionData['confidence']) || 'medium',
            detectedAt: new Date()
          };

          if (mountedRef.current) {
            setCurrentTheme(themeData);
            applyTheme(themeData);

            if (onThemeChangeRef.current) {
              onThemeChangeRef.current(themeData);
            }

            if (debugMode) {
              console.log('ThemeDetector: Using stored theme preference', {
                theme: storedTheme,
                source: storedSource,
                confidence: storedConfidence
              });
            }
          }
        } else {
          // Perform fresh detection
          if (mountedRef.current) {
            handleThemeChange();
          }
        }

        // Set up Telegram theme change listener
        if (mountedRef.current) {
          const cleanup = setupTelegramListener();
          if (cleanup) {
            telegramListenerRef.current = cleanup;
          }
        }

        if (mountedRef.current) {
          setIsInitialized(true);
        }
      } catch {
        reportError({
          type: 'detection_error',
          message: 'Failed to initialize theme detection',
          context: {
            enableAutoDetection,
            hasStoredTheme: Boolean(secureStorageGet('preferred-theme'))
          }
        });

        if (mountedRef.current) {
          setIsInitialized(true);
        }
      }
    };

    initializeThemeDetection();
  }, [applyTheme, debugMode, enableAutoDetection, handleThemeChange, reportError, secureStorageGet, setupTelegramListener]);

  /**
   * Enhanced system theme change listener with debouncing
   */
  useEffect(() => {
    if (!enableAutoDetection || !enableSystemFallback || !mountedRef.current) return;

    if (typeof window !== 'undefined' && window.matchMedia) {
      const mediaQuery = window.matchMedia('(prefers-color-scheme: dark)');

      const handleSystemThemeChange = (event: MediaQueryListEvent) => {
        if (!mountedRef.current) return;

        if (debugMode) {
          console.log('ThemeDetector: System theme changed', {
            prefersDark: event.matches,
            timestamp: new Date().toISOString()
          });
        }

        // Only react to system changes if we're not using Telegram theme
        const telegramTheme = detectTelegramTheme();
        if (!telegramTheme.colorScheme || telegramTheme.confidence !== 'high') {
          handleThemeChange();
        }
      };

      // Add event listener with proper fallback
      try {
        if (mediaQuery.addEventListener) {
          mediaQuery.addEventListener('change', handleSystemThemeChange);
          return () => {
            if (mountedRef.current) {
              mediaQuery.removeEventListener('change', handleSystemThemeChange);
            }
          };
        } else {
          // Fallback for older browsers
          mediaQuery.addListener(handleSystemThemeChange);
          return () => {
            if (mountedRef.current) {
              mediaQuery.removeListener(handleSystemThemeChange);
            }
          };
        }
      } catch {
        reportError({
          type: 'detection_error',
          message: 'Failed to set up system theme listener',
          context: {
            hasMediaQuery: Boolean(mediaQuery),
            hasAddEventListener: typeof mediaQuery?.addEventListener !== 'undefined'
          }
        });
      }
    }
  }, [enableAutoDetection, enableSystemFallback, detectTelegramTheme, handleThemeChange, debugMode, reportError]);

  // Enhanced debug information display
  if (debugMode && currentTheme) {
    return (
      <div className="theme-detector-debug" style={{
        position: 'fixed',
        top: '10px',
        right: '10px',
        background: 'rgba(0, 0, 0, 0.9)',
        color: '#00ff88',
        padding: '10px 14px',
        borderRadius: '6px',
        fontSize: '11px',
        zIndex: 9998, // Below language detector
        fontFamily: 'Monaco, Consolas, monospace',
        maxWidth: '280px',
        border: '1px solid #333',
        boxShadow: '0 4px 12px rgba(0, 0, 0, 0.5)'
      }}>
        <div style={{ borderBottom: '1px solid #333', paddingBottom: '6px', marginBottom: '6px' }}>
          <strong style={{ color: '#fff' }}>🎨 Theme Detector</strong>
        </div>
        <div><strong>Theme:</strong> <span style={{ color: '#ffff00' }}>{currentTheme.theme}</span></div>
        <div><strong>Source:</strong> <span style={{ color: '#00ffff' }}>{currentTheme.themeSource}</span></div>
        {currentTheme.confidence && (
          <div><strong>Confidence:</strong> <span style={{
            color: currentTheme.confidence === 'high' ? '#00ff00' :
                  currentTheme.confidence === 'medium' ? '#ffff00' : '#ff9900'
          }}>{currentTheme.confidence}</span></div>
        )}
        {currentTheme.telegramColorScheme && (
          <div><strong>Telegram:</strong> <span style={{ color: '#ff88ff' }}>{currentTheme.telegramColorScheme}</span></div>
        )}
        <div><strong>System Dark:</strong> <span style={{
          color: currentTheme.systemPrefersDark ? '#ff8800' : '#88ff00'
        }}>{currentTheme.systemPrefersDark ? 'Yes' : 'No'}</span></div>
        <div style={{ fontSize: '10px', marginTop: '6px' }}>
          <div><strong>Detected:</strong> {currentTheme.detectedAt.toLocaleTimeString()}</div>
          <div><strong>Initialized:</strong> {isInitialized ? '✅' : '⏳'}</div>
          <div><strong>Listener:</strong> {enableTelegramListener && telegramListenerRef.current ? '📡' : '❌'}</div>
          <div><strong>Document:</strong> {document.documentElement.getAttribute('data-theme') || 'none'}</div>
        </div>
      </div>
    );
  }

  // Component is invisible in production mode
  return null;
};

export default ThemeDetector;
