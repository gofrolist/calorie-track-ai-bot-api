from fastapi import APIRouter

router = APIRouter()


@router.post("/auth/telegram/init")
async def telegram_init():
    # TODO: verify initData HMAC; mint JWT
    return {"token": "dev", "refresh_token": "dev", "user": {"id": "dev"}}
