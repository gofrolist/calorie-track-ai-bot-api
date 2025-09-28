/**
 * Simplified Theme Detection Service
 * Temporary replacement to resolve build issues
 */

export type ThemeType = 'light' | 'dark' | 'auto';
export type ThemeSource = 'system' | 'telegram' | 'manual' | 'fallback';

export interface ThemeState {
  theme: ThemeType;
  source: ThemeSource;
  isAutoDetectionEnabled?: boolean;
  systemPrefersDark?: boolean;
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
  private currentSource: ThemeSource = 'system';
  private listeners: ((event: ThemeChangeEvent) => void)[] = [];
  private autoDetection: boolean = true;

  constructor() {
    this.detectTheme();
  }

  getCurrentTheme(): ThemeType {
    return this.currentTheme;
  }

  async setTheme(theme: ThemeType, source: ThemeSource = 'manual'): Promise<void> {
    // Validate theme
    if (!['light', 'dark', 'auto'].includes(theme)) {
      throw new Error(`Invalid theme: ${theme}`);
    }

    const previousTheme = this.currentTheme;
    this.currentTheme = theme;
    this.currentSource = source;

    // Apply theme to DOM
    this.applyThemeToDOM(theme, source);

    this.notifyListeners({
      theme,
      source,
      previousTheme,
      automatic: source !== 'manual',
      timestamp: Date.now()
    });
  }

  private applyThemeToDOM(theme: ThemeType, source: ThemeSource): void {
    if (typeof document === 'undefined') return;

    const resolvedTheme = this.getResolvedTheme();

    // Set data attributes
    document.documentElement.setAttribute('data-theme', resolvedTheme);
    document.documentElement.setAttribute('data-theme-source', source);

    // Set CSS custom properties
    document.documentElement.style.setProperty('--theme', resolvedTheme);
  }

  async detectTheme(): Promise<{ theme: ThemeType; source: ThemeSource }> {
    // Simple system theme detection
    if (typeof window !== 'undefined' && window.matchMedia) {
      const prefersDark = window.matchMedia('(prefers-color-scheme: dark)').matches;
      const theme: ThemeType = prefersDark ? 'dark' : 'light';
      this.currentTheme = theme;
      this.currentSource = 'system';
      return { theme, source: 'system' };
    }

    this.currentTheme = 'light';
    this.currentSource = 'fallback';
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

  getThemeState(): ThemeState {
    const systemPrefersDark = typeof window !== 'undefined' && window.matchMedia
      ? window.matchMedia('(prefers-color-scheme: dark)').matches
      : false;

    return {
      theme: this.currentTheme,
      source: this.currentSource,
      isAutoDetectionEnabled: this.autoDetection,
      systemPrefersDark
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

  async detectAndUpdateTheme(): Promise<void> {
    await this.detectTheme();
  }

  addListener(listener: (event: ThemeChangeEvent) => void): () => void {
    this.listeners.push(listener);
    return () => {
      const index = this.listeners.indexOf(listener);
      if (index > -1) {
        this.listeners.splice(index, 1);
      }
    };
  }

  setAutoDetection(enabled: boolean): void {
    // Simple implementation for testing
    this.autoDetection = enabled;
  }

  getResolvedTheme(): ThemeType {
    if (this.currentTheme === 'auto') {
      // Simple auto resolution
      if (typeof window !== 'undefined' && window.matchMedia) {
        return window.matchMedia('(prefers-color-scheme: dark)').matches ? 'dark' : 'light';
      }
      return 'light';
    }
    return this.currentTheme;
  }

  destroy(): void {
    this.listeners = [];
  }

  dispose(): void {
    this.destroy();
  }
}

// Export singleton instance
export const themeDetectionService = new ThemeDetectionService();
