import { describe, it, expect, vi, beforeEach, afterEach } from 'vitest';

// Mock window.Telegram
const mockTelegramWebApp = {
  ready: vi.fn(),
  expand: vi.fn(),
  initDataUnsafe: {
    user: {
      id: 123456789,
      first_name: 'Test',
      username: 'test_user',
      language_code: 'en'
    }
  },
  initData: 'test_init_data',
  themeParams: {
    bg_color: '#ffffff',
    text_color: '#000000'
  },
  colorScheme: 'light'
};

const mockWindow = {
  Telegram: {
    WebApp: mockTelegramWebApp
  },
  location: {
    href: 'https://calorie-track-ai-bot.vercel.app/',
    search: '',
    hash: ''
  },
  localStorage: {
    getItem: vi.fn(),
    setItem: vi.fn(),
    removeItem: vi.fn()
  }
};

describe('Telegram WebApp Integration Tests', () => {
  beforeEach(() => {
    // Reset mocks
    vi.clearAllMocks();

    // Mock window object
    Object.defineProperty(window, 'Telegram', {
      value: mockWindow.Telegram,
      writable: true,
      configurable: true
    });

    Object.defineProperty(window, 'location', {
      value: mockWindow.location,
      writable: true,
      configurable: true
    });

    Object.defineProperty(window, 'localStorage', {
      value: mockWindow.localStorage,
      writable: true,
      configurable: true
    });
  });

  afterEach(() => {
    vi.restoreAllMocks();
  });

  describe('User ID Detection Logic', () => {
    it('should detect user ID from Telegram WebApp', () => {
      // Test the core logic for detecting user ID
      let userId = null;

      // Try to get user ID from Telegram WebApp
      if (window.Telegram?.WebApp?.initDataUnsafe?.user?.id) {
        userId = window.Telegram.WebApp.initDataUnsafe.user.id.toString();
      }

      expect(userId).toBe('123456789');
    });

    it('should fallback to URL parameters when Telegram WebApp is not available', () => {
      // Remove Telegram WebApp
      Object.defineProperty(window, 'Telegram', {
        value: undefined,
        writable: true,
        configurable: true
      });

      // Set URL parameters
      Object.defineProperty(window, 'location', {
        value: {
          ...mockWindow.location,
          search: '?user_id=987654321'
        },
        writable: true,
        configurable: true
      });

      let userId = null;

      // Try to get user ID from Telegram WebApp
      if (window.Telegram?.WebApp?.initDataUnsafe?.user?.id) {
        userId = window.Telegram.WebApp.initDataUnsafe.user.id.toString();
      }

      // Fallback: try to get from URL parameters
      if (!userId) {
        const urlParams = new URLSearchParams(window.location.search);
        userId = urlParams.get('user_id') ||
                 urlParams.get('tg_user_id') ||
                 urlParams.get('user') ||
                 urlParams.get('id');
      }

      expect(userId).toBe('987654321');
    });

    it('should fallback to hash parameters when URL parameters are not available', () => {
      // Remove Telegram WebApp
      Object.defineProperty(window, 'Telegram', {
        value: undefined,
        writable: true,
        configurable: true
      });

      // Set hash parameters
      Object.defineProperty(window, 'location', {
        value: {
          ...mockWindow.location,
          hash: '#user_id=555666777'
        },
        writable: true,
        configurable: true
      });

      let userId = null;

      // Try to get user ID from Telegram WebApp
      if (window.Telegram?.WebApp?.initDataUnsafe?.user?.id) {
        userId = window.Telegram.WebApp.initDataUnsafe.user.id.toString();
      }

      // Fallback: try to get from URL parameters
      if (!userId) {
        const urlParams = new URLSearchParams(window.location.search);
        userId = urlParams.get('user_id') ||
                 urlParams.get('tg_user_id') ||
                 urlParams.get('user') ||
                 urlParams.get('id');
      }

      // Also check hash parameters
      if (!userId && window.location.hash) {
        const hashParams = new URLSearchParams(window.location.hash.substring(1));
        userId = hashParams.get('user_id') ||
                 hashParams.get('tg_user_id') ||
                 hashParams.get('user') ||
                 hashParams.get('id');
      }

      expect(userId).toBe('555666777');
    });

    it('should fallback to localStorage when other sources are not available', () => {
      // Remove Telegram WebApp
      Object.defineProperty(window, 'Telegram', {
        value: undefined,
        writable: true,
        configurable: true
      });

      // Mock localStorage with stored user
      vi.mocked(window.localStorage.getItem).mockReturnValue(
        JSON.stringify({ id: 111222333 })
      );

      let userId = null;

      // Try to get user ID from Telegram WebApp
      if (window.Telegram?.WebApp?.initDataUnsafe?.user?.id) {
        userId = window.Telegram.WebApp.initDataUnsafe.user.id.toString();
      }

      // Fallback: try to get from URL parameters
      if (!userId) {
        const urlParams = new URLSearchParams(window.location.search);
        userId = urlParams.get('user_id') ||
                 urlParams.get('tg_user_id') ||
                 urlParams.get('user') ||
                 urlParams.get('id');
      }

      // Also check hash parameters
      if (!userId && window.location.hash) {
        const hashParams = new URLSearchParams(window.location.hash.substring(1));
        userId = hashParams.get('user_id') ||
                 hashParams.get('tg_user_id') ||
                 hashParams.get('user') ||
                 hashParams.get('id');
      }

      // Additional fallback: check if we have stored user info
      if (!userId) {
        try {
          const storedUser = localStorage.getItem('telegram_user');
          if (storedUser) {
            const userData = JSON.parse(storedUser);
            userId = userData.id?.toString();
          }
        } catch (e) {
          // Ignore parsing errors
        }
      }

      expect(userId).toBe('111222333');
    });

    it('should handle missing user ID gracefully', () => {
      // Remove all user ID sources
      Object.defineProperty(window, 'Telegram', {
        value: undefined,
        writable: true,
        configurable: true
      });

      Object.defineProperty(window, 'location', {
        value: {
          ...mockWindow.location,
          search: '',
          hash: ''
        },
        writable: true,
        configurable: true
      });

      vi.mocked(window.localStorage.getItem).mockReturnValue(null);

      let userId = null;

      // Try to get user ID from Telegram WebApp
      if (window.Telegram?.WebApp?.initDataUnsafe?.user?.id) {
        userId = window.Telegram.WebApp.initDataUnsafe.user.id.toString();
      }

      // Fallback: try to get from URL parameters
      if (!userId) {
        const urlParams = new URLSearchParams(window.location.search);
        userId = urlParams.get('user_id') ||
                 urlParams.get('tg_user_id') ||
                 urlParams.get('user') ||
                 urlParams.get('id');
      }

      // Also check hash parameters
      if (!userId && window.location.hash) {
        const hashParams = new URLSearchParams(window.location.hash.substring(1));
        userId = hashParams.get('user_id') ||
                 hashParams.get('tg_user_id') ||
                 hashParams.get('user') ||
                 hashParams.get('id');
      }

      // Additional fallback: check if we have stored user info
      if (!userId) {
        try {
          const storedUser = localStorage.getItem('telegram_user');
          if (storedUser) {
            const userData = JSON.parse(storedUser);
            userId = userData.id?.toString();
          }
        } catch (e) {
          // Ignore parsing errors
        }
      }

      expect(userId).toBeNull();
    });
  });

  describe('Debug Information Generation', () => {
    it('should generate correct debug info when Telegram WebApp is available', () => {
      const debugInfo = {
        timestamp: new Date().toISOString(),
        telegramAvailable: !!window.Telegram?.WebApp,
        userId: window.Telegram?.WebApp?.initDataUnsafe?.user?.id?.toString() || null,
        url: '/api/v1/goals',
        hasStoredUser: !!localStorage.getItem('telegram_user')
      };

      expect(debugInfo.telegramAvailable).toBe(true);
      expect(debugInfo.userId).toBe('123456789');
      expect(debugInfo.url).toBe('/api/v1/goals');
    });

    it('should generate correct debug info when Telegram WebApp is not available', () => {
      // Remove Telegram WebApp
      Object.defineProperty(window, 'Telegram', {
        value: undefined,
        writable: true,
        configurable: true
      });

      const debugInfo = {
        timestamp: new Date().toISOString(),
        telegramAvailable: !!window.Telegram?.WebApp,
        userId: window.Telegram?.WebApp?.initDataUnsafe?.user?.id?.toString() || null,
        url: '/api/v1/goals',
        hasStoredUser: !!localStorage.getItem('telegram_user')
      };

      expect(debugInfo.telegramAvailable).toBe(false);
      expect(debugInfo.userId).toBeNull();
      expect(debugInfo.url).toBe('/api/v1/goals');
    });
  });

  describe('Telegram WebApp Properties', () => {
    it('should have all required Telegram WebApp properties', () => {
      const webApp = window.Telegram?.WebApp;

      expect(webApp).toBeDefined();
      expect(webApp?.ready).toBeDefined();
      expect(webApp?.expand).toBeDefined();
      expect(webApp?.initDataUnsafe).toBeDefined();
      expect(webApp?.initData).toBeDefined();
      expect(webApp?.themeParams).toBeDefined();
      expect(webApp?.colorScheme).toBeDefined();
    });

    it('should have user data in initDataUnsafe', () => {
      const user = window.Telegram?.WebApp?.initDataUnsafe?.user;

      expect(user).toBeDefined();
      expect(user?.id).toBe(123456789);
      expect(user?.first_name).toBe('Test');
      expect(user?.username).toBe('test_user');
      expect(user?.language_code).toBe('en');
    });

    it('should have theme parameters', () => {
      const themeParams = window.Telegram?.WebApp?.themeParams;

      expect(themeParams).toBeDefined();
      expect(themeParams?.bg_color).toBe('#ffffff');
      expect(themeParams?.text_color).toBe('#000000');
    });
  });

  describe('Environment Detection', () => {
    it('should detect Telegram WebApp environment', () => {
      const isTelegramAvailable = !!window.Telegram?.WebApp;
      expect(isTelegramAvailable).toBe(true);
    });

    it('should detect non-Telegram environment', () => {
      // Remove Telegram WebApp
      Object.defineProperty(window, 'Telegram', {
        value: undefined,
        writable: true,
        configurable: true
      });

      const isTelegramAvailable = !!window.Telegram?.WebApp;
      expect(isTelegramAvailable).toBe(false);
    });
  });

  describe('Data Storage', () => {
    it('should store user data in localStorage', () => {
      const user = window.Telegram?.WebApp?.initDataUnsafe?.user;

      if (user) {
        localStorage.setItem('telegram_user', JSON.stringify(user));
        expect(window.localStorage.setItem).toHaveBeenCalledWith(
          'telegram_user',
          JSON.stringify(user)
        );
      }
    });

    it('should retrieve user data from localStorage', () => {
      const user = { id: 123456789, first_name: 'Test' };
      vi.mocked(window.localStorage.getItem).mockReturnValue(JSON.stringify(user));

      const storedUser = localStorage.getItem('telegram_user');
      const userData = storedUser ? JSON.parse(storedUser) : null;

      expect(userData).toEqual(user);
    });
  });
});
