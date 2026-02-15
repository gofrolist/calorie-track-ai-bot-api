import { Component, type ReactNode } from "react";
import i18n from "@/i18n";

interface Props {
  children: ReactNode;
  fallback?: ReactNode;
}

interface State {
  hasError: boolean;
  error: Error | null;
}

export class ErrorBoundary extends Component<Props, State> {
  state: State = { hasError: false, error: null };

  static getDerivedStateFromError(error: Error): State {
    return { hasError: true, error };
  }

  componentDidCatch(error: Error, info: React.ErrorInfo) {
    console.error("ErrorBoundary caught:", error, info.componentStack);
  }

  render() {
    if (this.state.hasError) {
      if (this.props.fallback) return this.props.fallback;
      return (
        <div className="flex min-h-screen flex-col items-center justify-center gap-4 bg-tg-bg p-6 text-center text-tg-text">
          <h1 className="text-xl font-semibold">
            {i18n.t("errorBoundary.title")}
          </h1>
          <p className="text-sm text-tg-hint">
            {i18n.t("errorBoundary.message")}
          </p>
          {import.meta.env.DEV && this.state.error && (
            <pre className="max-w-full overflow-auto rounded bg-tg-secondary-bg p-3 text-left text-xs">
              {this.state.error.message}
            </pre>
          )}
          <button
            onClick={() => window.location.reload()}
            className="rounded-lg bg-tg-button px-6 py-2 text-sm font-medium text-tg-button-text"
            aria-label={i18n.t("errorBoundary.reload")}
          >
            {i18n.t("errorBoundary.reload")}
          </button>
        </div>
      );
    }
    return this.props.children;
  }
}
