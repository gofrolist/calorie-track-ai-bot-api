declare global {
  interface Window {
    Telegram?: {
      WebApp?: {
        ready(): void;
        expand(): void;
        close(): void;
        enableClosingConfirmation(): void;
        disableClosingConfirmation(): void;
        setHeaderColor(color: string): void;
        setBackgroundColor(color: string): void;
        colorScheme: 'light' | 'dark';
        themeParams: {
          bg_color?: string;
          text_color?: string;
          hint_color?: string;
          link_color?: string;
          button_color?: string;
          button_text_color?: string;
          secondary_bg_color?: string;
        };
        initData: string;
        initDataUnsafe: {
          user?: {
            id: number;
            first_name: string;
            last_name?: string;
            username?: string;
            language_code?: string;
            is_premium?: boolean;
            photo_url?: string;
          };
          auth_date: number;
          hash: string;
        };
        viewportHeight: number;
        viewportStableHeight: number;
        isExpanded: boolean;
        MainButton: {
          text: string;
          color: string;
          textColor: string;
          isVisible: boolean;
          isActive: boolean;
          isProgressVisible: boolean;
          setText(text: string): void;
          onClick(callback: () => void): void;
          offClick(callback: () => void): void;
          show(): void;
          hide(): void;
          enable(): void;
          disable(): void;
          showProgress(leaveActive?: boolean): void;
          hideProgress(): void;
          setParams(params: {
            text?: string;
            color?: string;
            text_color?: string;
            is_active?: boolean;
            is_visible?: boolean;
          }): void;
        };
        BackButton: {
          isVisible: boolean;
          onClick(callback: () => void): void;
          offClick(callback: () => void): void;
          show(): void;
          hide(): void;
        };
        HapticFeedback: {
          impactOccurred(style: 'light' | 'medium' | 'heavy' | 'rigid' | 'soft'): void;
          notificationOccurred(type: 'error' | 'success' | 'warning'): void;
          selectionChanged(): void;
        };
        CloudStorage: {
          setItem(key: string, value: string, callback?: (error: string | null, stored?: boolean) => void): void;
          getItem(key: string, callback: (error: string | null, value?: string) => void): void;
          getItems(keys: string[], callback: (error: string | null, values?: Record<string, string>) => void): void;
          removeItem(key: string, callback?: (error: string | null, removed?: boolean) => void): void;
          removeItems(keys: string[], callback?: (error: string | null, removed?: boolean) => void): void;
          getKeys(callback: (error: string | null, keys?: string[]) => void): void;
        };
        openLink(url: string, options?: { try_instant_view?: boolean }): void;
        openTelegramLink(url: string): void;
        showAlert(message: string): void;
        showConfirm(message: string, callback?: (confirmed: boolean) => void): void;
        shareToStory(media_url: string, params?: {
          text?: string;
          widget_link?: {
            url: string;
            name?: string;
          };
        }): void;
      };
    };
  }
}

export {};
