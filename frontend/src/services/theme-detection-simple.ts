/**
 * Simplified Theme Detection Service
 * Temporary replacement to resolve build issues
 */

export type ThemeType = 'light' | 'dark' | 'auto';
export type ThemeSource = 'system' | 'telegram' | 'manual' | 'fallback';

export interface ThemeState {
  theme: ThemeType;
  source: ThemeSource;
}

export interface ThemeChangeEvent {
  theme: ThemeType;
  source: ThemeSource;
  previousTheme: ThemeType;
  automatic: boolean;
  timestamp: number;
}

export class ThemeDetectionService {
  private currentTheme: ThemeType = 'light';
  private listeners: ((event: ThemeChangeEvent) => void)[] = [];

  constructor() {
    this.detectTheme();
  }

  getCurrentTheme(): ThemeType {
    return this.currentTheme;
  }

  async setTheme(theme: ThemeType, source: ThemeSource = 'manual'): Promise<void> {
    const previousTheme = this.currentTheme;
    this.currentTheme = theme;

    this.notifyListeners({
      theme,
      source,
      previousTheme,
      automatic: source !== 'manual',
      timestamp: Date.now()
    });
  }

  async detectTheme(): Promise<{ theme: ThemeType; source: ThemeSource }> {
    // Simple system theme detection
    if (typeof window !== 'undefined' && window.matchMedia) {
      const prefersDark = window.matchMedia('(prefers-color-scheme: dark)').matches;
      const theme: ThemeType = prefersDark ? 'dark' : 'light';
      this.currentTheme = theme;
      return { theme, source: 'system' };
    }

    return { theme: 'light', source: 'fallback' };
  }

  onThemeChange(listener: (event: ThemeChangeEvent) => void): () => void {
    this.listeners.push(listener);
    return () => {
      const index = this.listeners.indexOf(listener);
      if (index > -1) {
        this.listeners.splice(index, 1);
      }
    };
  }

  private notifyListeners(event: ThemeChangeEvent): void {
    this.listeners.forEach(listener => {
      try {
        listener(event);
      } catch (error) {
        console.error('Theme change listener error:', error);
      }
    });
  }

  getState(): ThemeState {
    return {
      theme: this.currentTheme,
      source: 'system'
    };
  }

  isInTelegram(): boolean {
    return typeof window !== 'undefined' &&
           Boolean(window.Telegram) &&
           Boolean(window.Telegram?.WebApp);
  }

  initialize(): void {
    this.detectTheme();
  }

  destroy(): void {
    this.listeners = [];
  }
}

// Export singleton instance
export const themeDetectionService = new ThemeDetectionService();
