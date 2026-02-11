/**
 * FeedbackForm Component
 * Feature: 005-mini-app-improvements
 *
 * User feedback and support submission form
 * Implements UI/UX best practices: touch targets, accessibility, error handling
 */

import { useState, useEffect } from 'react';
import { useTranslation } from 'react-i18next';
import {
  submitFeedback,
  buildUserContext,
  type FeedbackSubmissionRequest,
} from '../services/feedback';

const DRAFT_STORAGE_KEY = 'feedback_draft';
const MAX_MESSAGE_LENGTH = 5000;

export function FeedbackForm() {
  const { t, i18n } = useTranslation();

  const [messageContent, setMessageContent] = useState('');
  const [isSubmitting, setIsSubmitting] = useState(false);
  const [showSuccess, setShowSuccess] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [characterCount, setCharacterCount] = useState(0);

  // Load draft from localStorage on mount
  useEffect(() => {
    const draft = localStorage.getItem(DRAFT_STORAGE_KEY);
    if (draft) {
      try {
        const parsed = JSON.parse(draft);
        setMessageContent(parsed.messageContent || '');
        setCharacterCount(parsed.messageContent?.length || 0);
      } catch {
        // Invalid draft, ignore
        localStorage.removeItem(DRAFT_STORAGE_KEY);
      }
    }
  }, []);

  // Auto-save draft to localStorage
  useEffect(() => {
    if (messageContent) {
      const draft = {
        messageContent,
        savedAt: new Date().toISOString(),
      };
      localStorage.setItem(DRAFT_STORAGE_KEY, JSON.stringify(draft));
    }
  }, [messageContent]);

  const handleMessageChange = (e: React.ChangeEvent<HTMLTextAreaElement>) => {
    const value = e.target.value;
    setMessageContent(value);
    setCharacterCount(value.length);
    setError(null); // Clear error on input
  };

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setError(null);

    // Inline validation
    const trimmedContent = messageContent.trim();
    if (!trimmedContent) {
      setError(t('feedback.validation.emptyMessage'));
      return;
    }

    if (trimmedContent.length > MAX_MESSAGE_LENGTH) {
      setError(t('feedback.validation.tooLong'));
      return;
    }

    // Check if user ID is available before submitting
    const userId = getUserId();
    if (!userId) {
      setError('Unable to submit feedback: User authentication not available. Please make sure you opened this app from Telegram.');
      console.error('User ID not found - Telegram WebApp may not be initialized');
      return;
    }

    try {
      setIsSubmitting(true);

      const request: FeedbackSubmissionRequest = {
        message_type: 'feedback', // Default to 'feedback' since user doesn't select type
        message_content: trimmedContent,
        user_context: buildUserContext(i18n.language),
      };

      await submitFeedback(request);

      // Clear form and draft on success
      setMessageContent('');
      setCharacterCount(0);
      localStorage.removeItem(DRAFT_STORAGE_KEY);

      // Show success message
      setShowSuccess(true);
      setTimeout(() => setShowSuccess(false), 5000); // Auto-dismiss after 5 seconds

    } catch (err: any) {
      // More specific error messages based on the error type
      if (err?.response?.status === 401) {
        setError('Authentication required. Please make sure you opened this app from Telegram.');
      } else if (err?.response?.data?.detail) {
        setError(`Failed to send: ${err.response.data.detail}`);
      } else if (err?.message) {
        setError(`Failed to send: ${err.message}`);
      } else {
        setError(t('feedback.error'));
      }
      console.error('Failed to submit feedback:', err);
    } finally {
      setIsSubmitting(false);
    }
  };

  // Helper function to get user ID from various sources
  const getUserId = (): string | null => {
    // Try Telegram WebApp first
    if (window.Telegram?.WebApp?.initDataUnsafe?.user?.id) {
      return window.Telegram.WebApp.initDataUnsafe.user.id.toString();
    }

    // Try URL parameters
    const urlParams = new URLSearchParams(window.location.search);
    let userId = urlParams.get('user_id') ||
                urlParams.get('tg_user_id') ||
                urlParams.get('user') ||
                urlParams.get('id');

    if (userId) return userId;

    // Try hash parameters
    if (window.location.hash) {
      const hashParams = new URLSearchParams(window.location.hash.substring(1));
      userId = hashParams.get('user_id') ||
              hashParams.get('tg_user_id') ||
              hashParams.get('user') ||
              hashParams.get('id');
      if (userId) return userId;
    }

    // Try localStorage
    try {
      const storedUser = localStorage.getItem('telegram_user');
      if (storedUser) {
        const userData = JSON.parse(storedUser);
        if (userData.id) {
          return userData.id.toString();
        }
      }
    } catch {
      // Ignore parsing errors
    }

    return null;
  };

  const isFormValid = messageContent.trim().length > 0 && messageContent.length <= MAX_MESSAGE_LENGTH;
  const charactersRemaining = MAX_MESSAGE_LENGTH - characterCount;
  const isApproachingLimit = charactersRemaining < 500;

  return (
    <div className="feedback-form-container" data-testid="feedback-form" style={{ padding: '16px', maxWidth: '600px', margin: '0 auto' }}>
      <h2 style={{ marginBottom: '24px', fontSize: '24px', fontWeight: '600' }}>
        {t('feedback.title')}
      </h2>

      {showSuccess && (
        <div
          className="success-message"
          role="alert"
          aria-live="polite"
          style={{
            padding: '16px',
            marginBottom: '16px',
            backgroundColor: '#4CAF50',
            color: 'white',
            borderRadius: '8px',
            fontSize: '16px',
          }}
        >
          ✓ {t('feedback.success')}
        </div>
      )}

      {error && (
        <div
          className="error-message"
          role="alert"
          aria-live="assertive"
          style={{
            padding: '16px',
            marginBottom: '16px',
            backgroundColor: '#f44336',
            color: 'white',
            borderRadius: '8px',
            fontSize: '16px',
          }}
        >
          ⚠ {error}
        </div>
      )}

      <form onSubmit={handleSubmit}>
        {/* Message Content Textarea */}
        <div className="form-group" style={{ marginBottom: '24px' }}>
          <label
            htmlFor="message-content"
            style={{
              display: 'block',
              marginBottom: '8px',
              fontSize: '16px',
              fontWeight: '500',
            }}
          >
            {t('feedback.message')} *
          </label>
          <textarea
            id="message-content"
            value={messageContent}
            onChange={handleMessageChange}
            placeholder={t('feedback.messagePlaceholder')}
            disabled={isSubmitting}
            required
            aria-required="true"
            aria-label={t('feedback.message')}
            aria-describedby="character-count"
            aria-invalid={error ? 'true' : 'false'}
            style={{
              width: '100%',
              minHeight: '150px',
              padding: '12px',
              fontSize: '16px', // CHK003: Minimum 16px to prevent iOS zoom
              fontFamily: 'inherit',
              lineHeight: '1.5',
              border: '1px solid #ddd',
              borderRadius: '8px',
              resize: 'vertical',
              boxSizing: 'border-box',
            }}
          />
          <div
            id="character-count"
            style={{
              marginTop: '8px',
            fontSize: '14px',
            color: isApproachingLimit ? '#d32f2f' : 'var(--tg-hint-color, #6b6b6b)',
              textAlign: 'right',
            }}
            aria-live="polite"
          >
            {characterCount} / {MAX_MESSAGE_LENGTH}
            {isApproachingLimit && ` (${charactersRemaining} ${t('feedback.charactersRemaining')})`}
          </div>
        </div>

        {/* Submit Button - Touch-friendly */}
        <button
          type="submit"
          disabled={isSubmitting}
          aria-label={isSubmitting ? t('feedback.submitting') : t('feedback.submit')}
          style={{
            width: '100%',
            minHeight: '48px', // CHK001: Minimum 48px touch target
            padding: '14px 24px',
            fontSize: '18px',
            fontWeight: '600',
            backgroundColor: isFormValid && !isSubmitting ? 'var(--tg-button-color, #0066cc)' : '#757575',
            color: 'white',
            border: 'none',
            borderRadius: '8px',
            cursor: isFormValid && !isSubmitting ? 'pointer' : 'default',
            transition: 'all 0.2s',
            opacity: isSubmitting ? 0.7 : 1,
          }}
        >
          {isSubmitting ? t('feedback.submitting') : t('feedback.submit')}
        </button>

        {/* Help text */}
        <p
          style={{
            marginTop: '16px',
            fontSize: '14px',
            color: 'var(--tg-hint-color, #6b6b6b)',
            textAlign: 'center',
          }}
        >
          {t('feedback.helpText')}
        </p>
      </form>
    </div>
  );
}
