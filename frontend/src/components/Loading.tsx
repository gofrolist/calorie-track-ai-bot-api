import React from 'react';
import { useTranslation } from 'react-i18next';

// CSS animations as inline styles
const spinKeyframes = `
@keyframes spin {
  0% { transform: rotate(0deg); }
  100% { transform: rotate(360deg); }
}
`;

const pulseKeyframes = `
@keyframes pulse {
  0%, 100% { opacity: 1; }
  50% { opacity: 0.5; }
}
`;

interface LoadingProps {
  message?: string;
  size?: 'small' | 'medium' | 'large';
  inline?: boolean;
  className?: string;
  style?: React.CSSProperties;
}

export const Loading: React.FC<LoadingProps> = ({
  message,
  size = 'medium',
  inline = false,
  className = '',
  style = {}
}) => {
  const { t } = useTranslation();

  const sizeStyles = {
    small: { width: '16px', height: '16px', borderWidth: '2px' },
    medium: { width: '32px', height: '32px', borderWidth: '3px' },
    large: { width: '48px', height: '48px', borderWidth: '4px' }
  };

  const spinnerStyle: React.CSSProperties = {
    border: `${sizeStyles[size].borderWidth} solid var(--tg-hint-color, #e0e0e0)`,
    borderTop: `${sizeStyles[size].borderWidth} solid var(--tg-button-color, #007aff)`,
    borderRadius: '50%',
    width: sizeStyles[size].width,
    height: sizeStyles[size].height,
    animation: 'spin 1s linear infinite',
    ...style
  };

  const containerStyle: React.CSSProperties = {
    display: inline ? 'inline-flex' : 'flex',
    flexDirection: 'column',
    alignItems: 'center',
    justifyContent: 'center',
    gap: '12px',
    padding: inline ? '0' : '24px',
    ...style
  };

  return (
    <div className={`loading-container ${className}`} style={containerStyle}>
      <style dangerouslySetInnerHTML={{ __html: spinKeyframes }} />
      <div className="loading-spinner" style={spinnerStyle} />
      {message && (
        <div
          style={{
            color: 'var(--tg-hint-color, #666666)',
            fontSize: '0.9em',
            textAlign: 'center'
          }}
        >
          {message}
        </div>
      )}
    </div>
  );
};

// Skeleton loading component for content placeholders
interface SkeletonProps {
  lines?: number;
  width?: string | number;
  height?: string | number;
  className?: string;
  style?: React.CSSProperties;
}

export const Skeleton: React.FC<SkeletonProps> = ({
  lines = 1,
  width = '100%',
  height = '16px',
  className = '',
  style = {}
}) => {
  const skeletonStyle: React.CSSProperties = {
    backgroundColor: 'var(--tg-hint-color, #e0e0e0)',
    borderRadius: '4px',
    animation: 'pulse 1.5s ease-in-out infinite',
    width,
    height,
    marginBottom: lines > 1 ? '8px' : '0',
    ...style
  };

  if (lines === 1) {
    return (
      <div className={`skeleton ${className}`} style={skeletonStyle}>
        <style dangerouslySetInnerHTML={{ __html: pulseKeyframes }} />
      </div>
    );
  }

  return (
    <div className={`skeleton-container ${className}`}>
      <style dangerouslySetInnerHTML={{ __html: pulseKeyframes }} />
      {Array.from({ length: lines }, (_, index) => (
        <div
          key={index}
          className="skeleton"
          style={{
            ...skeletonStyle,
            width: index === lines - 1 ? '60%' : width, // Last line shorter
          }}
        />
      ))}
    </div>
  );
};

// Loading states for different content types
interface LoadingCardProps {
  className?: string;
  style?: React.CSSProperties;
}

export const LoadingCard: React.FC<LoadingCardProps> = ({
  className = '',
  style = {}
}) => (
  <div className={`tg-card ${className}`} style={{ padding: '16px', ...style }}>
    <Skeleton width="60%" height="20px" style={{ marginBottom: '12px' }} />
    <Skeleton lines={3} />
  </div>
);

interface LoadingListProps {
  items?: number;
  className?: string;
  style?: React.CSSProperties;
}

export const LoadingList: React.FC<LoadingListProps> = ({
  items = 3,
  className = '',
  style = {}
}) => (
  <div className={`loading-list ${className}`} style={style}>
    {Array.from({ length: items }, (_, index) => (
      <LoadingCard key={index} style={{ marginBottom: '12px' }} />
    ))}
  </div>
);

export default Loading;
