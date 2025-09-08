import os

APP_ENV: str = os.getenv("APP_ENV", "dev")

OPENAI_API_KEY: str | None = os.getenv("OPENAI_API_KEY")
OPENAI_MODEL: str = os.getenv("OPENAI_MODEL", "gpt-5-mini")

SUPABASE_URL: str | None = os.getenv("SUPABASE_URL")
SUPABASE_KEY: str | None = os.getenv("SUPABASE_KEY")

REDIS_URL: str | None = os.getenv("REDIS_URL")

# Tigris S3-compatible storage configuration
# Using standard AWS S3 environment variables as per Fly.io Tigris documentation
AWS_ENDPOINT_URL_S3: str | None = os.getenv("AWS_ENDPOINT_URL_S3")
AWS_ACCESS_KEY_ID: str | None = os.getenv("AWS_ACCESS_KEY_ID")
AWS_SECRET_ACCESS_KEY: str | None = os.getenv("AWS_SECRET_ACCESS_KEY")
BUCKET_NAME: str | None = os.getenv("BUCKET_NAME")
AWS_REGION: str = os.getenv("AWS_REGION", "auto")
