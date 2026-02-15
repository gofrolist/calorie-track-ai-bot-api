"""Feedback API Endpoints - User feedback and support.

Feature: 005-mini-app-improvements
Provides endpoints for submitting and managing user feedback.
"""

from uuid import UUID

from fastapi import APIRouter, HTTPException, Request

from ...schemas import FeedbackSubmission, FeedbackSubmissionRequest, FeedbackSubmissionResponse
from ...services.config import logger
from ...services.feedback_service import get_feedback_service
from ...utils.error_handling import handle_api_errors
from .deps import get_authenticated_user_id

router = APIRouter(prefix="/feedback", tags=["feedback"])


@router.post("", response_model=FeedbackSubmissionResponse, status_code=201)
@handle_api_errors("feedback submission")
async def submit_feedback(
    request: Request,
    payload: FeedbackSubmissionRequest,
) -> FeedbackSubmissionResponse:
    """Submit user feedback, bug report, question, or support request.

    Stores submission in database and sends notification to admin chat/channel.

    Args:
        request: FastAPI request object (for auth headers)
        payload: Feedback submission request body

    Returns:
        Feedback submission response with ID and confirmation

    Raises:
        HTTPException: If submission fails
    """
    # Get user ID from Telegram authentication
    user_id = await get_authenticated_user_id(request)

    logger.info(
        f"Feedback submission request from user {user_id[:8]}...",
        extra={
            "user_id": user_id,
            "message_type": payload.message_type.value,
            "message_length": len(payload.message_content),
        },
    )

    feedback_service = get_feedback_service()
    response = await feedback_service.submit_feedback(
        user_id=user_id,
        request=payload,
    )

    return response


@router.get("/{feedback_id}", response_model=FeedbackSubmission)
@handle_api_errors("feedback retrieval")
async def get_feedback(
    request: Request,
    feedback_id: UUID,
) -> FeedbackSubmission:
    """Get feedback submission by ID (admin only).

    Args:
        request: FastAPI request object (for auth)
        feedback_id: Feedback submission UUID

    Returns:
        Feedback submission details

    Raises:
        HTTPException: If feedback not found
    """
    # Validate authentication (admin access would be checked here in production)
    await get_authenticated_user_id(request)

    feedback_service = get_feedback_service()
    feedback = await feedback_service.get_feedback(feedback_id)

    if feedback is None:
        raise HTTPException(
            status_code=404,
            detail="Feedback submission not found",
        )

    return feedback
