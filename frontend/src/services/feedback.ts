/**
 * Feedback API Client Service
 * Feature: 005-mini-app-improvements
 *
 * Handles submission of user feedback, bugs, questions, and support requests
 */

import { api } from './api';

/**
 * Feedback message type
 */
export type FeedbackMessageType = 'feedback' | 'bug' | 'question' | 'support';

/**
 * Feedback submission request
 */
export interface FeedbackSubmissionRequest {
  message_type: FeedbackMessageType;
  message_content: string;
  user_context?: {
    page?: string;
    user_agent?: string;
    app_version?: string;
    language?: string;
    [key: string]: any;
  };
}

/**
 * Feedback submission response
 */
export interface FeedbackSubmissionResponse {
  id: string;
  status: 'new' | 'reviewed' | 'resolved';
  created_at: string;
  message: string;
}

/**
 * Submit user feedback
 *
 * @param request - Feedback submission data
 * @returns Feedback submission response with confirmation
 * @throws Error if submission fails
 */
export async function submitFeedback(
  request: FeedbackSubmissionRequest
): Promise<FeedbackSubmissionResponse> {
  const response = await api.post<FeedbackSubmissionResponse>(
    '/api/v1/feedback',
    request
  );
  return response.data;
}

/**
 * Get current page path for feedback context
 *
 * @returns Current page route
 */
export function getCurrentPage(): string {
  return window.location.pathname;
}

/**
 * Get app version from package.json or environment
 *
 * @returns App version string
 */
export function getAppVersion(): string {
  // In production, this would come from build-time env variable
  return import.meta.env.VITE_APP_VERSION || '0.1.0';
}

/**
 * Build user context object for feedback submission
 *
 * @param language - Current app language
 * @returns User context object
 */
export function buildUserContext(language: string): FeedbackSubmissionRequest['user_context'] {
  return {
    page: getCurrentPage(),
    user_agent: navigator.userAgent,
    app_version: getAppVersion(),
    language,
  };
}
