from fastapi import APIRouter, HTTPException

from ...schemas import PhotoCreateRequest, PresignResponse
from ...services.config import logger
from ...services.db import db_create_photo
from ...services.storage import tigris_presign_put

router = APIRouter()


@router.post("/photos", response_model=PresignResponse)
async def create_photo(body: PhotoCreateRequest):
    logger.info(f"Creating photo upload request for content_type: {body.content_type}")
    try:
        key, url = await tigris_presign_put(content_type=body.content_type)
        logger.debug(f"Generated presigned URL for key: {key}")

        photo_id = await db_create_photo(tigris_key=key)
        logger.info(f"Photo record created with ID: {photo_id}")

        return PresignResponse(photo_id=photo_id, upload_url=url)
    except Exception as e:
        logger.error(f"Error creating photo upload request: {e}", exc_info=True)
        raise HTTPException(500, str(e)) from e
