import os

APP_ENV: str = os.getenv("APP_ENV", "dev")

OPENAI_API_KEY: str | None = os.getenv("OPENAI_API_KEY")
OPENAI_MODEL: str = os.getenv("OPENAI_MODEL", "gpt-5-mini")

SUPABASE_URL: str | None = os.getenv("SUPABASE_URL")
SUPABASE_KEY: str | None = os.getenv("SUPABASE_KEY")

REDIS_URL: str | None = os.getenv("REDIS_URL")

TIGRIS_ENDPOINT: str | None = os.getenv("TIGRIS_ENDPOINT")
TIGRIS_REGION: str = os.getenv("TIGRIS_REGION", "auto")
TIGRIS_ACCESS_KEY: str | None = os.getenv("TIGRIS_ACCESS_KEY")
TIGRIS_SECRET_KEY: str | None = os.getenv("TIGRIS_SECRET_KEY")
TIGRIS_BUCKET: str | None = os.getenv("TIGRIS_BUCKET")
