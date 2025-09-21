import React, { Component, ErrorInfo, ReactNode } from 'react';
import { useTranslation } from 'react-i18next';

interface Props {
  children: ReactNode;
  fallback?: ReactNode;
  onError?: (error: Error, errorInfo: ErrorInfo) => void;
}

interface State {
  hasError: boolean;
  error?: Error;
}

class ErrorBoundaryClass extends Component<Props, State> {
  constructor(props: Props) {
    super(props);
    this.state = { hasError: false };
  }

  static getDerivedStateFromError(error: Error): State {
    return { hasError: true, error };
  }

  componentDidCatch(error: Error, errorInfo: ErrorInfo) {
    console.error('ErrorBoundary caught an error:', error, errorInfo);

    // Call custom error handler if provided
    if (this.props.onError) {
      this.props.onError(error, errorInfo);
    }

    // Provide haptic feedback if available
    if (window.Telegram?.WebApp?.HapticFeedback?.notificationOccurred) {
      window.Telegram.WebApp.HapticFeedback.notificationOccurred('error');
    }
  }

  render() {
    if (this.state.hasError) {
      if (this.props.fallback) {
        return this.props.fallback;
      }

      return <ErrorFallback error={this.state.error} />;
    }

    return this.props.children;
  }
}

// Error fallback component that can use hooks
const ErrorFallback: React.FC<{ error?: Error }> = ({ error }) => {
  const { t } = useTranslation();

  const handleReload = () => {
    window.location.reload();
  };

  const handleGoHome = () => {
    window.location.href = '/';
  };

  return (
    <div
      className="error-boundary"
      style={{
        padding: '24px',
        textAlign: 'center',
        backgroundColor: 'var(--tg-bg-color, #ffffff)',
        color: 'var(--tg-text-color, #000000)',
        minHeight: '200px',
        display: 'flex',
        flexDirection: 'column',
        justifyContent: 'center',
        alignItems: 'center',
        gap: '16px'
      }}
    >
      <div style={{ fontSize: '3em' }}>⚠️</div>
      <h2 style={{ margin: 0, fontSize: '1.5em' }}>
        {t('errorBoundary.title')}
      </h2>
      <p style={{ margin: 0, color: 'var(--tg-hint-color)', fontSize: '0.9em' }}>
        {t('errorBoundary.message')}
      </p>

      {process.env.NODE_ENV === 'development' && error && (
        <details style={{
          marginTop: '16px',
          padding: '12px',
          backgroundColor: 'var(--tg-secondary-bg-color, #f0f0f0)',
          borderRadius: '8px',
          fontSize: '0.8em',
          textAlign: 'left',
          maxWidth: '100%',
          overflow: 'auto'
        }}>
          <summary style={{ cursor: 'pointer', marginBottom: '8px' }}>
            {t('errorBoundary.errorDetails')}
          </summary>
          <pre style={{ margin: 0, whiteSpace: 'pre-wrap' }}>
            {error.stack}
          </pre>
        </details>
      )}

      <div style={{ display: 'flex', gap: '12px', marginTop: '16px' }}>
        <button
          className="tg-button"
          onClick={handleReload}
          style={{
            backgroundColor: 'var(--tg-button-color, #007aff)',
            color: 'var(--tg-button-text-color, #ffffff)',
            border: 'none',
            borderRadius: '8px',
            padding: '8px 16px',
            fontSize: '14px',
            cursor: 'pointer'
          }}
        >
          {t('errorBoundary.reload')}
        </button>
        <button
          className="tg-button"
          onClick={handleGoHome}
          style={{
            backgroundColor: 'transparent',
            color: 'var(--tg-button-color, #007aff)',
            border: '1px solid var(--tg-button-color, #007aff)',
            borderRadius: '8px',
            padding: '8px 16px',
            fontSize: '14px',
            cursor: 'pointer'
          }}
        >
          {t('errorBoundary.goHome')}
        </button>
      </div>
    </div>
  );
};

// Hook-based error boundary wrapper
export const ErrorBoundary: React.FC<Props> = (props) => {
  return <ErrorBoundaryClass {...props} />;
};

export default ErrorBoundary;
