import React, { lazy, Suspense, useCallback, useEffect, useState } from 'react';
import { createBrowserRouter, RouterProvider } from 'react-router-dom';
import { SpeedInsights } from '@vercel/speed-insights/react';
import { Analytics } from '@vercel/analytics/react';
// Use window.Telegram for simpler, more reliable access
import ErrorBoundary from './components/ErrorBoundary';
import ThemeDetector, { ThemeDetectionData } from './components/ThemeDetector';
import LanguageDetector, { LanguageDetectionData } from './components/LanguageDetector';
import SafeAreaWrapper from './components/SafeAreaWrapper';
import DebugInfo from './components/DebugInfo';
import { apiUtils, configApi, loggingApi } from './services/api';
import { config } from './config';

// Lazy load route components for code splitting
const Meals = lazy(() => import('./pages/Meals').then(module => ({ default: module.Meals })));
const Stats = lazy(() => import('./pages/stats').then(module => ({ default: module.Stats })));
const Goals = lazy(() => import('./pages/goals').then(module => ({ default: module.Goals })));

// Loading fallback component
const LoadingFallback = () => (
  <div style={{
    display: 'flex',
    alignItems: 'center',
    justifyContent: 'center',
    height: '100vh',
    backgroundColor: 'var(--tg-theme-bg-color, #ffffff)',
    color: 'var(--tg-theme-text-color, #000000)',
  }}>
    <div style={{ textAlign: 'center' }}>
      <div style={{
        width: '48px',
        height: '48px',
        border: '4px solid var(--tg-theme-hint-color, #999)',
        borderTopColor: 'var(--tg-theme-button-color, #3390ec)',
        borderRadius: '50%',
        animation: 'spin 1s linear infinite',
        margin: '0 auto 16px',
      }} />
      <div>Loading...</div>
    </div>
  </div>
);

// Telegram WebApp Context
export interface TelegramWebAppContextType {
  user: any | null;
  initData: string | null;
  theme: 'light' | 'dark' | 'auto';
  themeParams: any;
  language: string;
  themeDetectionData?: ThemeDetectionData;
  languageDetectionData?: LanguageDetectionData;
  isInitialized: boolean;
  isConnected: boolean;
  // Theme switching methods
  setTheme: (theme: 'light' | 'dark' | 'auto') => Promise<void>;
  // Language switching methods
  setLanguage: (language: string) => Promise<void>;
  // Safe area detection
  safeAreas: {
    top: number;
    bottom: number;
    left: number;
    right: number;
  };
}

export const TelegramWebAppContext = React.createContext<TelegramWebAppContextType>({
  user: null,
  initData: null,
  theme: 'light',
  themeParams: null,
  language: 'en',
  isInitialized: false,
  isConnected: false,
  setTheme: async () => {},
  setLanguage: async () => {},
  safeAreas: { top: 0, bottom: 0, left: 0, right: 0 },
});

const router = createBrowserRouter([
  {
    path: '/',
    element: (
      <Suspense fallback={<LoadingFallback />}>
        <Meals />
      </Suspense>
    )
  },
  {
    path: '/stats',
    element: (
      <Suspense fallback={<LoadingFallback />}>
        <Stats />
      </Suspense>
    )
  },
  {
    path: '/goals',
    element: (
      <Suspense fallback={<LoadingFallback />}>
        <Goals />
      </Suspense>
    )
  },
]);

const App: React.FC = () => {
  const [telegramContext, setTelegramContext] = useState<TelegramWebAppContextType>({
    user: null,
    initData: null,
    theme: 'light',
    themeParams: null,
    language: 'en',
    isInitialized: false,
    isConnected: false,
    setTheme: async () => {},
    setLanguage: async () => {},
    safeAreas: { top: 0, bottom: 0, left: 0, right: 0 },
  });

  // Theme switching function
  const handleSetTheme = async (newTheme: 'light' | 'dark' | 'auto') => {
    try {
      await loggingApi.logInfo('Theme change requested', {
        newTheme,
        currentTheme: telegramContext.theme,
        source: 'manual'
      });

      // Update local state immediately for responsive UI
      setTelegramContext(prev => ({ ...prev, theme: newTheme }));

      // Apply theme to document
      applyThemeToDocument(newTheme);

      // Update backend configuration
      try {
        await configApi.patchUIConfiguration({
          theme: newTheme,
          theme_source: 'manual'
        });

        await loggingApi.logInfo('Theme updated successfully', {
          theme: newTheme,
          source: 'manual'
        });
      } catch (error) {
        await loggingApi.logWarning('Failed to update theme in backend', {
          error: error instanceof Error ? error.message : String(error),
          theme: newTheme
        });
      }
    } catch (error) {
      await apiUtils.safeLog('ERROR', 'Theme switching failed', {
        error: error instanceof Error ? error.message : String(error),
        requestedTheme: newTheme
      });
    }
  };

  // Language switching function
  const handleSetLanguage = async (newLanguage: string) => {
    try {
      // Validate language is supported
      if (!config.ui.supportedLanguages.includes(newLanguage as 'en' | 'ru')) {
        throw new Error(`Language ${newLanguage} is not supported`);
      }

      await loggingApi.logInfo('Language change requested', {
        newLanguage,
        currentLanguage: telegramContext.language,
        source: 'manual'
      });

      // Update local state immediately for responsive UI
      setTelegramContext(prev => ({ ...prev, language: newLanguage }));

      // Apply language to document
      applyLanguageToDocument(newLanguage);

      // Update backend configuration
      try {
        await configApi.patchUIConfiguration({
          language: newLanguage,
          language_source: 'manual'
        });

        await loggingApi.logInfo('Language updated successfully', {
          language: newLanguage,
          source: 'manual'
        });
      } catch (error) {
        await loggingApi.logWarning('Failed to update language in backend', {
          error: error instanceof Error ? error.message : String(error),
          language: newLanguage
        });
      }
    } catch (error) {
      await apiUtils.safeLog('ERROR', 'Language switching failed', {
        error: error instanceof Error ? error.message : String(error),
        requestedLanguage: newLanguage
      });
    }
  };

  // Apply theme to document
  const applyThemeToDocument = (theme: 'light' | 'dark' | 'auto') => {
    document.documentElement.setAttribute('data-theme', theme);
    document.documentElement.setAttribute('data-theme-source', 'manual');

    // Set CSS custom property
    document.documentElement.style.setProperty('--theme', theme);

    // Handle auto theme resolution
    if (theme === 'auto') {
      const prefersDark = window.matchMedia('(prefers-color-scheme: dark)').matches;
      const resolvedTheme = prefersDark ? 'dark' : 'light';
      document.documentElement.setAttribute('data-resolved-theme', resolvedTheme);
    } else {
      document.documentElement.setAttribute('data-resolved-theme', theme);
    }
  };

  // Apply language to document
  const applyLanguageToDocument = (language: string) => {
    document.documentElement.setAttribute('lang', language);
    document.documentElement.setAttribute('data-language', language);
    document.documentElement.setAttribute('data-language-source', 'manual');

    // Set CSS custom property
    document.documentElement.style.setProperty('--language', language);

    // Set text direction (all supported languages are LTR)
    document.documentElement.setAttribute('dir', 'ltr');
    document.documentElement.style.setProperty('--text-direction', 'ltr');
  };

  // Handle theme detection changes
  const handleThemeChange = (themeData: ThemeDetectionData) => {
    setTelegramContext(prev => ({
      ...prev,
      theme: themeData.theme,
      themeDetectionData: themeData
    }));

    // Apply detected theme to document
    applyThemeToDocument(themeData.theme);
  };

  // Handle language detection changes
  const handleLanguageChange = (languageData: LanguageDetectionData) => {
    setTelegramContext(prev => ({
      ...prev,
      language: languageData.language,
      languageDetectionData: languageData
    }));

    // Apply detected language to document
    applyLanguageToDocument(languageData.language);
  };

  // Handle safe area changes
  const handleSafeAreaChange = useCallback((safeAreas: { top: number; bottom: number; left: number; right: number }) => {
    setTelegramContext(prev => ({
      ...prev,
      safeAreas
    }));
  }, []);

  // Initialize application
  useEffect(() => {
    const initializeApp = async () => {
      try {
        await loggingApi.logInfo('Application initialization started');

        // Initialize Telegram WebApp with better detection
        let telegramData: any = {};
        let isConnected = false;

        // Wait for Telegram WebApp to be available
        const waitForTelegram = async (): Promise<any> => {
          return new Promise((resolve) => {
            let attempts = 0;
            const maxAttempts = 50; // 5 seconds max wait

            const checkTelegram = () => {
              attempts++;

              if (window.Telegram?.WebApp) {
                const webApp = window.Telegram.WebApp;

                // Initialize WebApp
                webApp.ready();
                webApp.expand();

                const data = {
                  user: webApp.initDataUnsafe?.user || null,
                  initData: webApp.initData || null,
                  themeParams: webApp.themeParams,
                };

                // Store user data in localStorage for API calls
                if (webApp.initDataUnsafe?.user) {
                  localStorage.setItem('telegram_user', JSON.stringify(webApp.initDataUnsafe.user));
                }

                // Update CSS custom properties with Telegram theme colors
                if (webApp.themeParams) {
                  const root = document.documentElement;
                  root.style.setProperty('--tg-bg-color', webApp.themeParams.bg_color || '#ffffff');
                  root.style.setProperty('--tg-text-color', webApp.themeParams.text_color || '#000000');
                  root.style.setProperty('--tg-hint-color', webApp.themeParams.hint_color || '#999999');
                  root.style.setProperty('--tg-link-color', webApp.themeParams.link_color || '#007aff');
                  root.style.setProperty('--tg-button-color', webApp.themeParams.button_color || '#007aff');
                  root.style.setProperty('--tg-button-text-color', webApp.themeParams.button_text_color || '#ffffff');
                  root.style.setProperty('--tg-secondary-bg-color', webApp.themeParams.secondary_bg_color || '#f0f0f0');
                }

                resolve(data);
              } else if (attempts < maxAttempts) {
                setTimeout(checkTelegram, 100);
              } else {
                // Telegram WebApp not available after timeout
                console.log('Telegram WebApp not available after timeout');
                resolve({});
              }
            };

            checkTelegram();
          });
        };

        telegramData = await waitForTelegram();

        // Check connectivity
        try {
          const healthCheck = await apiUtils.checkApplicationHealth();
          isConnected = healthCheck.health;
        } catch (error) {
          await apiUtils.safeLog('WARNING', 'Health check failed during initialization', {
            error: error instanceof Error ? error.message : String(error)
          });
        }

        // Initialize application with API integration
        try {
          const appData = await apiUtils.initializeApplication();

          const initialTheme = appData.theme?.theme || 'light';
          const initialLanguage = appData.language?.language || 'en';

          // Apply initial theme and language
          applyThemeToDocument(initialTheme);
          applyLanguageToDocument(initialLanguage);

          setTelegramContext(prev => ({
            ...prev,
            ...telegramData,
            theme: initialTheme,
            language: initialLanguage,
            isInitialized: true,
            isConnected,
            setTheme: handleSetTheme,
            setLanguage: handleSetLanguage,
          }));

          await loggingApi.logInfo('Application initialization completed successfully', {
            theme: initialTheme,
            language: initialLanguage,
            connected: isConnected,
            telegramUser: !!telegramData.user
          });

        } catch (error) {
          // Fallback initialization
          const fallbackTheme = 'light';
          const fallbackLanguage = 'en';

          applyThemeToDocument(fallbackTheme);
          applyLanguageToDocument(fallbackLanguage);

          setTelegramContext(prev => ({
            ...prev,
            ...telegramData,
            theme: fallbackTheme,
            language: fallbackLanguage,
            isInitialized: true,
            isConnected: false,
            setTheme: handleSetTheme,
            setLanguage: handleSetLanguage,
          }));

          await apiUtils.safeLog('WARNING', 'Application initialization failed, using fallback', {
            error: error instanceof Error ? error.message : String(error)
          });
        }

      } catch (error) {
        await apiUtils.safeLog('ERROR', 'Critical application initialization failure', {
          error: error instanceof Error ? error.message : String(error)
        });

        // Minimal fallback
        setTelegramContext(prev => ({
          ...prev,
          theme: 'light',
          language: 'en',
          isInitialized: true,
          isConnected: false,
          setTheme: handleSetTheme,
          setLanguage: handleSetLanguage,
        }));
      }
    };

    initializeApp();
  }, []);

  return (
    <TelegramWebAppContext.Provider value={telegramContext}>
      <ErrorBoundary>
        {/* Theme and Language Detection Components */}
        <ThemeDetector
          onThemeChange={handleThemeChange}
          enableAutoDetection={true}
          enableSystemFallback={true}
          debugMode={config.isDevelopment && config.features.enableDebugLogging}
        />
        <LanguageDetector
          onLanguageChange={handleLanguageChange}
          enableAutoDetection={true}
          enableBrowserFallback={true}
          defaultLanguage="en"
          supportedLanguages={['en', 'ru']} // Updated to match requirement
          debugMode={config.isDevelopment && config.features.enableDebugLogging}
        />

        {/* Main App Container with Safe Area Support */}
        <SafeAreaWrapper
          enableAllSides={config.ui.enableSafeAreas}
          debugMode={config.isDevelopment && config.features.enableDebugLogging}
          onSafeAreaChange={handleSafeAreaChange}
          className="telegram-webapp main-content-safe"
        >
          <div data-theme={telegramContext.theme} data-language={telegramContext.language}>
          <RouterProvider router={router} />
        </div>
        </SafeAreaWrapper>
      </ErrorBoundary>
      <DebugInfo />
      <SpeedInsights />
      <Analytics />
    </TelegramWebAppContext.Provider>
  );
};

export default App;
