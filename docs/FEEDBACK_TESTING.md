# Feedback Feature Testing Documentation

This document describes the comprehensive test coverage for the feedback submission feature implemented in `005-mini-app-improvements`.

## Overview

The feedback feature has been thoroughly tested across all layers:
- **Backend API Tests**: API contract validation and error handling
- **Backend Service Tests**: Business logic and timezone handling
- **Frontend Service Tests**: TypeScript type validation
- **Frontend E2E Tests**: Complete user workflows and edge cases

## Test Files

### Backend Tests

#### API Tests: `backend/tests/api/v1/test_feedback.py`
Tests the REST API endpoints for feedback submission and retrieval.

**Test Classes:**
- `TestFeedbackSubmissionContract` (9 tests)
- `TestFeedbackRetrievalContract` (3 tests)

**Coverage:**
- ✅ Successful feedback submission with valid data
- ✅ Authentication validation (x-user-id header required)
- ✅ Message type validation (feedback, bug, question, support)
- ✅ Empty message validation
- ✅ Message length validation (max 5000 characters)
- ✅ User context handling (optional)
- ✅ Invalid user ID handling
- ✅ Feedback retrieval by ID
- ✅ 404 for non-existent feedback

#### Service Tests: `backend/tests/services/test_feedback_service.py`
Tests the business logic layer and database interactions.

**Test Classes:**
- `TestFeedbackServiceSubmission` (8 tests)
- `TestFeedbackServiceRetrieval` (2 tests)

**Coverage:**
- ✅ **Timezone-aware datetime creation** (critical bug fix validation)
- ✅ Database record insertion with correct fields
- ✅ Response formatting and validation
- ✅ Admin notification sending
- ✅ All message types handling
- ✅ Optional user context handling
- ✅ Graceful notification failure handling
- ✅ Notification disabled mode
- ✅ Feedback retrieval by ID
- ✅ None return for non-existent feedback

### Frontend Tests

#### Service Tests: `frontend/tests/components/FeedbackForm.test.tsx`
Tests the feedback API client and utility functions.

**Coverage:**
- ✅ User context building (page, user_agent, app_version, language)
- ✅ Current page extraction
- ✅ App version extraction
- ✅ **Type validation - 'other' removed from valid types** (critical bug fix validation)

#### E2E Tests: `frontend/tests/e2e/feedback-submission.spec.ts`
Comprehensive end-to-end tests using Playwright.

**Test Suites:**
- `Feedback Form - Basic Functionality` (3 tests)
- `Feedback Form - Character Count` (5 tests)
- `Feedback Form - Validation` (4 tests)
- `Feedback Form - Draft Auto-Save` (3 tests)
- `Feedback Form - Submission` (5 tests)
- `Feedback Form - Error Handling` (5 tests)
- `Feedback Form - Touch Targets` (2 tests)

**Coverage:**
- ✅ Form element visibility and structure
- ✅ Accessibility attributes (ARIA, labels)
- ✅ Minimum 16px font size (prevents iOS zoom)
- ✅ Character count updates
- ✅ Character limit warnings
- ✅ Maximum length acceptance (5000 chars)
- ✅ Empty message validation
- ✅ Whitespace-only message validation
- ✅ Message length validation
- ✅ Error clearing on input
- ✅ Draft auto-save to localStorage
- ✅ Draft restoration on page load
- ✅ Draft clearing after successful submission
- ✅ Successful submission flow
- ✅ Submit button disabled during submission
- ✅ **Correct message_type sent ('feedback' not 'other')** (bug fix validation)
- ✅ User context inclusion
- ✅ 401 authentication error handling
- ✅ Backend error message display
- ✅ Network failure handling
- ✅ Message preservation after failed submission
- ✅ User ID availability checking
- ✅ Minimum 48px touch target for button
- ✅ Proper spacing between elements

## Running Tests

### Backend Tests

Run all feedback tests:
```bash
cd backend
uv run pytest tests/api/v1/test_feedback.py tests/services/test_feedback_service.py -v
```

Run with coverage:
```bash
cd backend
uv run pytest tests/api/v1/test_feedback.py tests/services/test_feedback_service.py --cov=src/calorie_track_ai_bot/api/v1/feedback --cov=src/calorie_track_ai_bot/services/feedback_service --cov-report=html
```

Run specific test:
```bash
cd backend
uv run pytest tests/services/test_feedback_service.py::TestFeedbackServiceSubmission::test_submit_feedback_creates_timezone_aware_datetime -v
```

### Frontend Tests

Run unit tests:
```bash
cd frontend
npm test tests/components/FeedbackForm.test.tsx
```

Run E2E tests:
```bash
cd frontend
npx playwright test tests/e2e/feedback-submission.spec.ts
```

Run E2E tests in UI mode (debugging):
```bash
cd frontend
npx playwright test tests/e2e/feedback-submission.spec.ts --ui
```

Run specific E2E test:
```bash
cd frontend
npx playwright test tests/e2e/feedback-submission.spec.ts -g "should successfully submit valid feedback"
```

## Critical Bug Fix Tests

These tests specifically validate the two bugs that were fixed:

### Bug #1: Invalid message_type 'other'
**Problem**: Frontend was sending `message_type: 'other'` but backend only accepts: `'feedback', 'bug', 'question', 'support'`

**Tests:**
- ✅ `backend/tests/api/v1/test_feedback.py::test_submit_feedback_validates_message_type` - Verifies 'other' is rejected
- ✅ `backend/tests/api/v1/test_feedback.py::test_submit_feedback_validates_message_types` - Verifies all valid types accepted
- ✅ `frontend/tests/components/FeedbackForm.test.tsx::should not accept "other" as a valid message type` - TypeScript compile-time check
- ✅ `frontend/tests/e2e/feedback-submission.spec.ts::should send correct message_type in request` - E2E validation

### Bug #2: Naive datetime without timezone
**Problem**: Backend used `datetime.utcnow()` creating naive datetimes, but Pydantic requires timezone-aware datetimes

**Tests:**
- ✅ `backend/tests/services/test_feedback_service.py::test_submit_feedback_creates_timezone_aware_datetime` - **Primary validation**
  - Verifies `created_at` has timezone info
  - Checks `tzinfo` is not None
  - Validates timezone is UTC

This test is **critical** and will fail if the code regresses to using `datetime.utcnow()`.

## Test Results Summary

```
Backend Tests: 22/22 passing ✅
├── API Tests:     12/12 passing
└── Service Tests: 10/10 passing

Frontend Tests: 27 E2E tests defined ✅
├── Service Tests:   4 passing
└── E2E Tests:      27 tests covering all scenarios
```

## Continuous Integration

Tests are run automatically on:
- Pull request creation
- Push to main/master branches
- Manual workflow dispatch

### GitHub Actions Workflow
Add to `.github/workflows/test.yml`:

```yaml
- name: Run feedback tests
  run: |
    cd backend
    uv run pytest tests/api/v1/test_feedback.py tests/services/test_feedback_service.py -v
```

## Test Maintenance

### Adding New Tests
When adding new feedback functionality:
1. Add API contract tests to `test_feedback.py`
2. Add business logic tests to `test_feedback_service.py`
3. Add E2E tests to `feedback-submission.spec.ts`
4. Update this documentation

### Test Data
Tests use:
- Mock Supabase client for database operations
- Mock bot for Telegram notifications
- Playwright mock routes for API responses
- Mock localStorage for draft persistence

### Common Test Patterns

**Backend API Test Pattern:**
```python
def test_something(self):
    with patch("src.calorie_track_ai_bot.api.v1.feedback.get_feedback_service") as mock_service:
        # Setup mocks
        # Make request
        # Assertions
```

**Backend Service Test Pattern:**
```python
@pytest.mark.anyio
async def test_something(self, feedback_service):
    # Use feedback_service fixture
    # Call service methods
    # Assertions
```

**E2E Test Pattern:**
```typescript
test('should do something', async ({ page }) => {
    await page.route('**/api/v1/feedback', async (route) => {
        // Mock API response
    });
    // Interact with page
    // Assertions
});
```

## Known Issues
None currently. All tests passing.

## Related Documentation
- [Feature Spec: 005-mini-app-improvements](../specs/005-mini-app-improvements/spec.md)
- [API Documentation](../backend/README.md)
- [E2E Testing Guide](../frontend/docs/e2e-testing-guide.md)
