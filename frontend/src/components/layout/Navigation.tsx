import { useNavigate, useLocation } from "react-router-dom";
import { useTranslation } from "react-i18next";
import type { SVGProps } from "react";

function MealsIcon(props: SVGProps<SVGSVGElement>) {
  return (
    <svg
      xmlns="http://www.w3.org/2000/svg"
      viewBox="0 0 24 24"
      fill="none"
      stroke="currentColor"
      strokeWidth={2}
      strokeLinecap="round"
      strokeLinejoin="round"
      {...props}
    >
      <path d="M3 2v7c0 1.1.9 2 2 2h4a2 2 0 0 0 2-2V2" />
      <path d="M7 2v20" />
      <path d="M21 15V2a5 5 0 0 0-5 5v6c0 1.1.9 2 2 2h3Zm0 0v7" />
    </svg>
  );
}

function StatsIcon(props: SVGProps<SVGSVGElement>) {
  return (
    <svg
      xmlns="http://www.w3.org/2000/svg"
      viewBox="0 0 24 24"
      fill="none"
      stroke="currentColor"
      strokeWidth={2}
      strokeLinecap="round"
      strokeLinejoin="round"
      {...props}
    >
      <line x1="18" y1="20" x2="18" y2="10" />
      <line x1="12" y1="20" x2="12" y2="4" />
      <line x1="6" y1="20" x2="6" y2="14" />
    </svg>
  );
}

function GoalsIcon(props: SVGProps<SVGSVGElement>) {
  return (
    <svg
      xmlns="http://www.w3.org/2000/svg"
      viewBox="0 0 24 24"
      fill="none"
      stroke="currentColor"
      strokeWidth={2}
      strokeLinecap="round"
      strokeLinejoin="round"
      {...props}
    >
      <circle cx="12" cy="12" r="10" />
      <circle cx="12" cy="12" r="6" />
      <circle cx="12" cy="12" r="2" />
    </svg>
  );
}

const NAV_ITEMS = [
  { path: "/", labelKey: "navigation.meals", Icon: MealsIcon },
  { path: "/stats", labelKey: "navigation.stats", Icon: StatsIcon },
  { path: "/goals", labelKey: "navigation.goals", Icon: GoalsIcon },
] as const;

export function Navigation() {
  const navigate = useNavigate();
  const location = useLocation();
  const { t } = useTranslation();

  return (
    <nav
      aria-label={t("navigation.menu")}
      className="fixed bottom-0 left-0 right-0 z-50 flex border-t border-tg-secondary-bg bg-tg-bg pb-[var(--safe-area-bottom,0px)]"
    >
      {NAV_ITEMS.map(({ path, labelKey, Icon }) => {
        const isActive =
          path === "/"
            ? location.pathname === "/"
            : location.pathname.startsWith(path);
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
            <Icon className="h-5 w-5" />
            <span>{t(labelKey)}</span>
          </button>
        );
      })}
    </nav>
  );
}
