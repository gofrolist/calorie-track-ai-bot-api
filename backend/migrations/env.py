import os
from logging.config import fileConfig

from alembic import context
from sqlalchemy import engine_from_config, pool

# this is the Alembic Config object, which provides
# access to the values within the .ini file in use.
config = context.config

# Interpret the config file for Python logging.
# This line sets up loggers basically.
if config.config_file_name is not None:
    fileConfig(config.config_file_name)

# add your model's MetaData object here
# for 'autogenerate' support
# from myapp import mymodel
# target_metadata = mymodel.Base.metadata
target_metadata = None


# Set database URL from environment variables
def get_database_url():
    """Get database URL from environment variables."""
    # Check for direct database URL first
    database_url = os.getenv("DATABASE_URL")
    if database_url:
        # Ensure it uses psycopg3 driver
        if database_url.startswith("postgresql://"):
            return database_url.replace("postgresql://", "postgresql+psycopg://")
        return database_url

    # Fallback to Supabase URL construction
    supabase_url = os.getenv("SUPABASE_URL")
    supabase_db_password = os.getenv("SUPABASE_DB_PASSWORD")

    if not supabase_url:
        raise ValueError("Either DATABASE_URL or SUPABASE_URL environment variable must be set")

    if not supabase_db_password:
        raise ValueError(
            "SUPABASE_DB_PASSWORD environment variable must be set for direct database access"
        )

    # Extract database URL from Supabase URL
    # Supabase URL format: https://project-id.supabase.co
    # We need to convert this to PostgreSQL connection string with psycopg3 driver
    if supabase_url.startswith("https://"):
        # Extract project ID from URL
        project_id = supabase_url.replace("https://", "").replace(".supabase.co", "")
        # Use Transaction pooler (Shared Pooler) connection for IPv4 compatibility
        # Format: postgresql://postgres.PROJECT_ID:PASSWORD@aws-1-us-east-1.pooler.supabase.com:6543/postgres
        db_url = f"postgresql+psycopg://postgres.{project_id}:{supabase_db_password}@aws-1-us-east-1.pooler.supabase.com:6543/postgres"
    else:
        # Assume it's already a PostgreSQL URL, but ensure it uses psycopg3 driver
        if supabase_url.startswith("postgresql://"):
            db_url = supabase_url.replace("postgresql://", "postgresql+psycopg://")
        else:
            db_url = supabase_url

    return db_url


# Set the database URL in the config
config.set_main_option("sqlalchemy.url", get_database_url())

# other values from the config, defined by the needs of env.py,
# can be acquired:
# my_important_option = config.get_main_option("my_important_option")
# ... etc.


def run_migrations_offline() -> None:
    """Run migrations in 'offline' mode.

    This configures the context with just a URL
    and not an Engine, though an Engine is acceptable
    here as well.  By skipping the Engine creation
    we don't even need a DBAPI to be available.

    Calls to context.execute() here emit the given string to the
    script output.

    """
    url = config.get_main_option("sqlalchemy.url")
    context.configure(
        url=url,
        target_metadata=target_metadata,
        literal_binds=True,
        dialect_opts={"paramstyle": "named"},
    )

    with context.begin_transaction():
        context.run_migrations()


def run_migrations_online() -> None:
    """Run migrations in 'online' mode.

    In this scenario we need to create an Engine
    and associate a connection with the context.

    """
    connectable = engine_from_config(
        config.get_section(config.config_ini_section, {}),
        prefix="sqlalchemy.",
        poolclass=pool.NullPool,
    )

    with connectable.connect() as connection:
        context.configure(connection=connection, target_metadata=target_metadata)

        with context.begin_transaction():
            context.run_migrations()


if context.is_offline_mode():
    run_migrations_offline()
else:
    run_migrations_online()
