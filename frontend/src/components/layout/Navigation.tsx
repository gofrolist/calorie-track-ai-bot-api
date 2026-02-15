import { useNavigate, useLocation } from "react-router-dom";
import { useTranslation } from "react-i18next";

const NAV_ITEMS = [
  { path: "/", labelKey: "navigation.meals" },
  { path: "/stats", labelKey: "navigation.stats" },
  { path: "/goals", labelKey: "navigation.goals" },
] as const;

export function Navigation() {
  const navigate = useNavigate();
  const location = useLocation();
  const { t } = useTranslation();

  return (
    <nav
      role="navigation"
      className="fixed bottom-0 left-0 right-0 z-50 flex border-t border-tg-secondary-bg bg-tg-bg pb-[var(--safe-area-bottom,0px)]"
    >
      {NAV_ITEMS.map(({ path, labelKey }) => {
        const isActive = location.pathname === path;
        return (
          <button
            key={path}
            type="button"
            onClick={() => navigate(path)}
            aria-current={isActive ? "page" : undefined}
            className={`flex flex-1 flex-col items-center gap-0.5 py-2 text-xs transition-colors ${
              isActive ? "text-tg-button" : "text-tg-hint"
            }`}
          >
            <span>{t(labelKey)}</span>
          </button>
        );
      })}
    </nav>
  );
}
