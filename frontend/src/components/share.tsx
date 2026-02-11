import React from 'react';
import { useTranslation } from 'react-i18next';

interface ShareProps {
  shareData?: {
    calories?: number;
    meals?: number;
    goal?: number;
    date?: string;
  };
  className?: string;
  style?: React.CSSProperties;
}

export const Share: React.FC<ShareProps> = ({
  shareData,
  className = '',
  style = {}
}) => {
  const { t } = useTranslation();

  const handleShare = () => {
    try {
      // Prepare share text based on available data
      let shareText = '';

      if (shareData) {
        const { calories = 0, meals = 0, goal, date } = shareData;

        if (meals > 0) {
          shareText = t('share.text', {
            calories,
            meals,
            goal: goal ? ` (${t('share.goal')}: ${goal} kcal)` : '',
            date: date || new Date().toLocaleDateString()
          });
        } else {
          shareText = t('share.textEmpty', {
            date: date || new Date().toLocaleDateString()
          });
        }
      } else {
        shareText = t('share.default');
      }

      // Use Telegram WebApp share functionality if available
      if (window.Telegram?.WebApp?.shareToStory) {
        // For Telegram Stories sharing
        window.Telegram.WebApp.shareToStory('', {
          text: shareText,
          widget_link: {
            url: window.location.origin,
            name: t('share.appName')
          }
        });
      } else if (window.Telegram?.WebApp?.showAlert) {
        // Fallback: show share text in alert for copying
        window.Telegram.WebApp.showAlert(
          `${t('share.copyText')}:\n\n${shareText}`
        );
      } else if (navigator.share) {
        // Use Web Share API as fallback
        navigator.share({
          title: t('share.title'),
          text: shareText,
          url: window.location.origin
        }).catch((error) => {
          console.warn('Error sharing:', error);
          // Final fallback: copy to clipboard
          copyToClipboard(shareText);
        });
      } else {
        // Final fallback: copy to clipboard
        copyToClipboard(shareText);
      }

      // Provide haptic feedback if available
      if (window.Telegram?.WebApp?.HapticFeedback?.notificationOccurred) {
        window.Telegram.WebApp.HapticFeedback.notificationOccurred('success');
      }

    } catch (error) {
      console.error('Error sharing:', error);

      // Show error feedback
      if (window.Telegram?.WebApp?.showAlert) {
        window.Telegram.WebApp.showAlert(t('share.error'));
      } else {
        alert(t('share.error'));
      }
    }
  };

  const copyToClipboard = async (text: string) => {
    try {
      await navigator.clipboard.writeText(text);

      if (window.Telegram?.WebApp?.showAlert) {
        window.Telegram.WebApp.showAlert(t('share.copied'));
      } else {
        alert(t('share.copied'));
      }
    } catch (error) {
      console.error('Failed to copy to clipboard:', error);

      if (window.Telegram?.WebApp?.showAlert) {
        window.Telegram.WebApp.showAlert(t('share.copyError'));
      } else {
        alert(t('share.copyError'));
      }
    }
  };

  return (
    <button
      className={`share-button ${className}`}
      onClick={handleShare}
      style={{
        display: 'inline-flex',
        alignItems: 'center',
        gap: '8px',
        padding: '8px 16px',
        backgroundColor: 'var(--tg-button-color, #007aff)',
        color: 'var(--tg-button-text-color, #ffffff)',
        border: 'none',
        borderRadius: '8px',
        fontSize: '14px',
        fontWeight: '500',
        cursor: 'pointer',
        transition: 'opacity 0.2s',
        ...style
      }}
      onMouseDown={(e) => {
        e.currentTarget.style.opacity = '0.8';
      }}
      onMouseUp={(e) => {
        e.currentTarget.style.opacity = '1';
      }}
      onMouseLeave={(e) => {
        e.currentTarget.style.opacity = '1';
      }}
    >
      <span>📤</span>
      <span>{t('share.button')}</span>
    </button>
  );
};

export default Share;
