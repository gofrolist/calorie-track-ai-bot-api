import logging
import os

APP_ENV: str = os.getenv("APP_ENV", "dev")

# Logging configuration
LOG_LEVEL: str = os.getenv("LOG_LEVEL", "INFO").upper()

# Configure logging
logging.basicConfig(
    level=getattr(logging, LOG_LEVEL, logging.INFO),
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S",
)

# Set specific loggers
logger = logging.getLogger("calorie_track_ai_bot")
if LOG_LEVEL == "DEBUG":
    # Enable debug logging for all our modules when DEBUG level is set
    for module_name in ["calorie_track_ai_bot", "fastapi", "uvicorn"]:
        logging.getLogger(module_name).setLevel(logging.DEBUG)

OPENAI_API_KEY: str | None = os.getenv("OPENAI_API_KEY")
OPENAI_MODEL: str = os.getenv("OPENAI_MODEL", "gpt-5-mini")

SUPABASE_URL: str | None = os.getenv("SUPABASE_URL")
SUPABASE_KEY: str | None = os.getenv("SUPABASE_KEY")
SUPABASE_SERVICE_ROLE_KEY: str | None = os.getenv("SUPABASE_SERVICE_ROLE_KEY")

REDIS_URL: str | None = os.getenv("REDIS_URL")

# Tigris S3-compatible storage configuration
# Using standard AWS S3 environment variables as per Fly.io Tigris documentation
AWS_ENDPOINT_URL_S3: str | None = os.getenv("AWS_ENDPOINT_URL_S3")
AWS_ACCESS_KEY_ID: str | None = os.getenv("AWS_ACCESS_KEY_ID")
AWS_SECRET_ACCESS_KEY: str | None = os.getenv("AWS_SECRET_ACCESS_KEY")
BUCKET_NAME: str | None = os.getenv("BUCKET_NAME")
AWS_REGION: str = os.getenv("AWS_REGION", "auto")

# Telegram Bot configuration
TELEGRAM_BOT_TOKEN: str | None = os.getenv("TELEGRAM_BOT_TOKEN")
WEBHOOK_URL: str | None = os.getenv("WEBHOOK_URL")
USE_WEBHOOK: bool = os.getenv("USE_WEBHOOK", "false").lower() == "true"
