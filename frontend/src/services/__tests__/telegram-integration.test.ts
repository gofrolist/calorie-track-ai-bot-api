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

describe('Telegram WebApp Integration', () => {
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

  describe('User ID Detection', () => {
    it('should detect user ID from Telegram WebApp', () => {
      // Test that Telegram WebApp user ID is available
      expect(window.Telegram?.WebApp?.initDataUnsafe?.user?.id).toBe(123456789);
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

      const urlParams = new URLSearchParams(window.location.search);
      const userId = urlParams.get('user_id');

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

      const hashParams = new URLSearchParams(window.location.hash.substring(1));
      const userId = hashParams.get('user_id');

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

      const storedUser = localStorage.getItem('telegram_user');
      const userData = storedUser ? JSON.parse(storedUser) : null;
      const userId = userData?.id?.toString();

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

      // Test that no user ID is found
      const telegramUserId = window.Telegram?.WebApp?.initDataUnsafe?.user?.id;
      const urlParams = new URLSearchParams(window.location.search);
      const urlUserId = urlParams.get('user_id');
      const storedUser = localStorage.getItem('telegram_user');

      expect(telegramUserId).toBeUndefined();
      expect(urlUserId).toBeNull();
      expect(storedUser).toBeNull();
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
