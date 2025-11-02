/**
 * Feedback Page
 * Feature: 005-mini-app-improvements
 *
 * Page wrapper for feedback form with navigation
 */

import { FeedbackForm } from '../components/FeedbackForm';
import Navigation from '../components/Navigation';

export function Feedback() {
  return (
    <div className="page-container">
      <FeedbackForm />
      <Navigation />
    </div>
  );
}

export default Feedback;
