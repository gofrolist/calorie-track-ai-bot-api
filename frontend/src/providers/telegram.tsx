import {
  createContext,
  useContext,
  useState,
  useEffect,
  useCallback,
  useMemo,
  type ReactNode,
} from "react";
import i18n from "@/i18n";

interface SafeAreaInsets {
  top: number;
  bottom: number;
  left: number;
  right: number;
}

interface TelegramContextValue {
  user: TelegramWebAppUser | null;
  initData: string | null;
  theme: "light" | "dark";
  language: "en" | "ru";
  safeAreas: SafeAreaInsets;
  setTheme: (theme: "light" | "dark") => void;
  setLanguage: (lang: "en" | "ru") => void;
}

const TelegramContext = createContext<TelegramContextValue | null>(null);

function resolveTheme(): "light" | "dark" {
  const tgScheme = window.Telegram?.WebApp?.colorScheme;
  if (tgScheme === "light" || tgScheme === "dark") return tgScheme;
  if (window.matchMedia?.("(prefers-color-scheme: dark)").matches)
    return "dark";
  return "light";
}

function resolveLanguage(): "en" | "ru" {
  const tgLang = window.Telegram?.WebApp?.initDataUnsafe?.user?.language_code;
  if (tgLang === "ru") return "ru";
  if (typeof navigator !== "undefined" && navigator.language?.startsWith("ru"))
    return "ru";
  return "en";
}

function getSafeAreas(): SafeAreaInsets {
  if (typeof document === "undefined")
    return { top: 0, bottom: 0, left: 0, right: 0 };
  const style = getComputedStyle(document.documentElement);
  return {
    top: parseFloat(style.getPropertyValue("--safe-area-top")) || 0,
    bottom: parseFloat(style.getPropertyValue("--safe-area-bottom")) || 0,
    left: parseFloat(style.getPropertyValue("--safe-area-left")) || 0,
    right: parseFloat(style.getPropertyValue("--safe-area-right")) || 0,
  };
}

export function TelegramProvider({ children }: { children: ReactNode }) {
  const webapp = window.Telegram?.WebApp;
  const user = webapp?.initDataUnsafe?.user ?? null;
  const initData = webapp?.initData ?? null;

  const [theme, setThemeState] = useState<"light" | "dark">(resolveTheme);
  const [language, setLanguageState] = useState<"en" | "ru">(resolveLanguage);
  const [safeAreas, setSafeAreas] = useState<SafeAreaInsets>(getSafeAreas);

  const setTheme = useCallback((t: "light" | "dark") => {
    setThemeState(t);
    document.documentElement.setAttribute("data-theme", t);
  }, []);

  const setLanguage = useCallback((lang: "en" | "ru") => {
    setLanguageState(lang);
    i18n.changeLanguage(lang);
  }, []);

  useEffect(() => {
    document.documentElement.setAttribute("data-theme", theme);
  }, [theme]);

  useEffect(() => {
    i18n.changeLanguage(language);
  }, [language]);

  useEffect(() => {
    const handleResize = () => setSafeAreas(getSafeAreas());
    window.addEventListener("resize", handleResize);
    return () => window.removeEventListener("resize", handleResize);
  }, []);

  const value = useMemo(
    () => ({
      user,
      initData,
      theme,
      language,
      safeAreas,
      setTheme,
      setLanguage,
    }),
    [user, initData, theme, language, safeAreas, setTheme, setLanguage],
  );

  return (
    <TelegramContext.Provider value={value}>
      {children}
    </TelegramContext.Provider>
  );
}

export function useTelegram(): TelegramContextValue {
  const context = useContext(TelegramContext);
  if (!context)
    throw new Error("useTelegram must be used within TelegramProvider");
  return context;
}
