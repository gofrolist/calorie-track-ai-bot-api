from fastapi import APIRouter, Request
from pydantic import BaseModel

from ...services.db import db_create_or_update_goal, db_get_goal
from ...utils.error_handling import handle_api_errors, validate_user_authentication

router = APIRouter()


class GoalRequest(BaseModel):
    daily_kcal_target: int


@router.get("/goals")
@handle_api_errors("goal retrieval")
async def get_goal(request: Request):
    """Get user's goal."""
    telegram_user_id = validate_user_authentication(request)

    goal = await db_get_goal(telegram_user_id)
    return goal


@router.post("/goals")
@handle_api_errors("goal creation")
async def create_goal(goal_data: GoalRequest, request: Request):
    """Create a new goal."""
    telegram_user_id = validate_user_authentication(request)

    goal = await db_create_or_update_goal(telegram_user_id, goal_data.daily_kcal_target)
    return goal


@router.patch("/goals")
@handle_api_errors("goal update")
async def update_goal(goal_data: GoalRequest, request: Request):
    """Update user's goal."""
    telegram_user_id = validate_user_authentication(request)

    goal = await db_create_or_update_goal(telegram_user_id, goal_data.daily_kcal_target)
    return goal
