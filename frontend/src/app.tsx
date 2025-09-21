import React, { useEffect, useState } from 'react';
import { createBrowserRouter, RouterProvider } from 'react-router-dom';
import { Today } from './pages/today';
import { MealDetail } from './pages/meal-detail';
import { Stats } from './pages/stats';
import { Goals } from './pages/goals';
import ErrorBoundary from './components/ErrorBoundary';

// Telegram WebApp Context
export interface TelegramWebAppContextType {
  user: any | null;
  initData: string | null;
  theme: 'light' | 'dark';
  themeParams: any;
}

export const TelegramWebAppContext = React.createContext<TelegramWebAppContextType>({
  user: null,
  initData: null,
  theme: 'light',
  themeParams: null,
});

const router = createBrowserRouter([
  { path: '/', element: <Today /> },
  { path: '/meal/:id', element: <MealDetail /> },
  { path: '/stats', element: <Stats /> },
  { path: '/goals', element: <Goals /> },
]);

const App: React.FC = () => {
  const [telegramContext, setTelegramContext] = useState<TelegramWebAppContextType>({
    user: null,
    initData: null,
    theme: 'light',
    themeParams: null,
  });

  useEffect(() => {
    // Initialize Telegram WebApp context
    try {
      // Get Telegram WebApp instance
      const webApp = window.Telegram?.WebApp;

      if (webApp) {
        // Get init data if available
        const initDataRaw = webApp.initData;
        const user = webApp.initDataUnsafe?.user;

        // Get theme parameters
        const currentThemeParams = webApp.themeParams;
        const isDark = currentThemeParams?.bg_color === '#000000' ||
                     webApp.colorScheme === 'dark';

        setTelegramContext({
          user: user || null,
          initData: initDataRaw || null,
          theme: isDark ? 'dark' : 'light',
          themeParams: currentThemeParams,
        });

        // Apply theme to document
        document.documentElement.setAttribute('data-theme', isDark ? 'dark' : 'light');

        // Update CSS custom properties with Telegram theme colors
        if (currentThemeParams) {
          const root = document.documentElement;
          root.style.setProperty('--tg-bg-color', currentThemeParams.bg_color || '#ffffff');
          root.style.setProperty('--tg-text-color', currentThemeParams.text_color || '#000000');
          root.style.setProperty('--tg-hint-color', currentThemeParams.hint_color || '#999999');
          root.style.setProperty('--tg-link-color', currentThemeParams.link_color || '#007aff');
          root.style.setProperty('--tg-button-color', currentThemeParams.button_color || '#007aff');
          root.style.setProperty('--tg-button-text-color', currentThemeParams.button_text_color || '#ffffff');
        }
      } else {
        // Fallback for development/testing when not in Telegram environment
        setTelegramContext({
          user: null,
          initData: null,
          theme: 'light',
          themeParams: null,
        });
      }

    } catch (error) {
      console.warn('Failed to initialize Telegram context:', error);
      // Use defaults for development/testing
      setTelegramContext({
        user: null,
        initData: null,
        theme: 'light',
        themeParams: null,
      });
    }
  }, []);

  return (
    <TelegramWebAppContext.Provider value={telegramContext}>
      <ErrorBoundary>
        <div className="telegram-webapp" data-theme={telegramContext.theme}>
          <RouterProvider router={router} />
        </div>
      </ErrorBoundary>
    </TelegramWebAppContext.Provider>
  );
};

export default App;
