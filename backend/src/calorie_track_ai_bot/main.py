from contextlib import asynccontextmanager
from pathlib import Path

from dotenv import load_dotenv
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from .api.v1 import auth, bot, daily_summary, estimates, goals, health, meals, photos
from .services.config import TELEGRAM_BOT_TOKEN, USE_WEBHOOK, WEBHOOK_URL, logger
from .services.telegram import get_bot

# Load environment variables from .env file
env_path = Path(__file__).parent.parent.parent / ".env"
load_dotenv(env_path)


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Manage application lifespan events."""
    # Startup
    logger.info("Starting Calories Count API application")

    if USE_WEBHOOK and TELEGRAM_BOT_TOKEN and WEBHOOK_URL:
        logger.info("Setting up Telegram webhook automatically...")
        try:
            bot = get_bot()
            success = await bot.set_webhook(WEBHOOK_URL)
            if success:
                logger.info(f"✅ Telegram webhook set successfully: {WEBHOOK_URL}")
            else:
                logger.error("❌ Failed to set Telegram webhook")
        except Exception as e:
            logger.error(f"❌ Error setting up Telegram webhook: {e}")
    else:
        logger.info("Telegram webhook setup skipped (not configured)")

    logger.info("All routers registered successfully")

    yield

    # Shutdown
    try:
        bot = get_bot()
        await bot.close()
        logger.info("Telegram bot client closed")
    except Exception as e:
        logger.error(f"Error closing bot client: {e}")


app = FastAPI(title="Calories Count API", version="0.1.0", lifespan=lifespan)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include routers
app.include_router(health.router, prefix="/health", tags=["health"])
app.include_router(auth.router, prefix="/api/v1", tags=["auth"])
app.include_router(photos.router, prefix="/api/v1", tags=["photos"])
app.include_router(estimates.router, prefix="/api/v1", tags=["estimates"])
app.include_router(meals.router, prefix="/api/v1", tags=["meals"])
app.include_router(daily_summary.router, prefix="/api/v1", tags=["daily-summary"])
app.include_router(goals.router, prefix="/api/v1", tags=["goals"])
app.include_router(bot.router, tags=["bot"])


@app.get("/healthz")
def healthz():
    """Health check endpoint for Fly.io."""
    return {"status": "ok"}
