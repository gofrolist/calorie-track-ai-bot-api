from fastapi import APIRouter, HTTPException
from pydantic import BaseModel

from ...services.db import db_create_or_update_goal, db_get_goal

router = APIRouter()


class GoalCreateRequest(BaseModel):
    daily_kcal_target: int


class GoalUpdateRequest(BaseModel):
    daily_kcal_target: int


@router.get("/goals")
async def get_goal():
    """Get user's goal."""
    try:
        # For now, use a dummy user_id since we don't have authentication
        # In a real implementation, this would use the authenticated user's ID
        dummy_user_id = "00000000-0000-0000-0000-000000000001"
        goal = db_get_goal(dummy_user_id)
        return goal
    except Exception as e:
        # If table doesn't exist, return None
        if "Could not find the table" in str(e):
            return None
        raise HTTPException(500, str(e)) from e


@router.post("/goals")
async def create_goal(goal_data: GoalCreateRequest):
    """Create a new goal."""
    try:
        # For now, use a dummy user_id since we don't have authentication
        # In a real implementation, this would use the authenticated user's ID
        dummy_user_id = "00000000-0000-0000-0000-000000000001"
        goal = db_create_or_update_goal(dummy_user_id, goal_data.daily_kcal_target)
        return goal
    except Exception as e:
        # If table doesn't exist, return a helpful error message
        if "Could not find the table" in str(e):
            raise HTTPException(
                503,
                "Goals feature not yet available. Please create the goals table in the database.",
            ) from e
        raise HTTPException(500, str(e)) from e


@router.patch("/goals")
async def update_goal(goal_data: GoalUpdateRequest):
    """Update user's goal."""
    try:
        # For now, use a dummy user_id since we don't have authentication
        # In a real implementation, this would use the authenticated user's ID
        dummy_user_id = "00000000-0000-0000-0000-000000000001"
        goal = db_create_or_update_goal(dummy_user_id, goal_data.daily_kcal_target)
        return goal
    except Exception as e:
        # If table doesn't exist, return a helpful error message
        if "Could not find the table" in str(e):
            raise HTTPException(
                503,
                "Goals feature not yet available. Please create the goals table in the database.",
            ) from e
        raise HTTPException(500, str(e)) from e
