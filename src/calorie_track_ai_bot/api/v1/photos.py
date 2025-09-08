from fastapi import APIRouter, HTTPException

from ...schemas import PhotoCreateRequest, PresignResponse
from ...services.db import db_create_photo
from ...services.storage import tigris_presign_put

router = APIRouter()


@router.post("/photos", response_model=PresignResponse)
async def create_photo(body: PhotoCreateRequest):
    try:
        key, url = await tigris_presign_put(content_type=body.content_type)
        photo_id = await db_create_photo(tigris_key=key)
        return PresignResponse(photo_id=photo_id, upload_url=url)
    except Exception as e:
        raise HTTPException(500, str(e)) from e
