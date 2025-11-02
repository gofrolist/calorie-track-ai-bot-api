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

    try {
      setIsSubmitting(true);

      const request: FeedbackSubmissionRequest = {
        message_type: 'other', // Default type since user doesn't select
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

    } catch (err) {
      setError(t('feedback.error'));
      console.error('Failed to submit feedback:', err);
    } finally {
      setIsSubmitting(false);
    }
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
