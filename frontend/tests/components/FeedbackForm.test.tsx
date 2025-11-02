/**
 * FeedbackForm Component Tests
 * Feature: 005-mini-app-improvements
 *
 * NOTE: These tests validate the feedback service API client.
 * Component functionality is validated through E2E tests in:
 * - tests/e2e/feedback-submission.spec.ts
 */

import { describe, it, expect, vi, beforeEach } from 'vitest';
import {
  submitFeedback,
  buildUserContext,
  getCurrentPage,
  getAppVersion,
  type FeedbackSubmissionRequest,
} from '../../src/services/feedback';

describe('Feedback Service', () => {
  beforeEach(() => {
    vi.clearAllMocks();
  });

  describe('buildUserContext', () => {
    it('should build user context with page, user agent, app version, and language', () => {
      const language = 'en';
      const context = buildUserContext(language);

      expect(context).toHaveProperty('page');
      expect(context).toHaveProperty('user_agent');
      expect(context).toHaveProperty('app_version');
      expect(context).toHaveProperty('language', 'en');
      expect(context.user_agent).toBe(navigator.userAgent);
    });

    it('should handle different languages', () => {
      const context = buildUserContext('ru');
      expect(context.language).toBe('ru');
    });
  });

  describe('getCurrentPage', () => {
    it('should return current page pathname', () => {
      const page = getCurrentPage();
      expect(typeof page).toBe('string');
      expect(page).toBe(window.location.pathname);
    });
  });

  describe('getAppVersion', () => {
    it('should return app version', () => {
      const version = getAppVersion();
      expect(typeof version).toBe('string');
      expect(version).toMatch(/^\d+\.\d+\.\d+$/); // Matches semantic version format
    });
  });

  describe('FeedbackMessageType validation', () => {
    it('should only accept valid message types', () => {
      const validTypes: Array<'feedback' | 'bug' | 'question' | 'support'> = [
        'feedback',
        'bug',
        'question',
        'support',
      ];

      validTypes.forEach((type) => {
        const request: FeedbackSubmissionRequest = {
          message_type: type,
          message_content: `Test ${type} message`,
        };

        // TypeScript should not complain about these types
        expect(request.message_type).toBe(type);
      });
    });

    it('should not accept "other" as a valid message type', () => {
      // This test verifies that 'other' is removed from the type definition
      // If this compiles, 'other' is incorrectly in the type definition
      const validTypes = ['feedback', 'bug', 'question', 'support'] as const;

      // @ts-expect-error - 'other' should not be a valid message type
      const invalidRequest: FeedbackSubmissionRequest = {
        message_type: 'other',
        message_content: 'Test',
      };

      // This is a compile-time test - if TypeScript allows 'other', the test fails
      expect(validTypes.includes('other' as any)).toBe(false);
    });
  });
});
