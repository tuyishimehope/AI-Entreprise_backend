import os
from logging.config import fileConfig

from sqlalchemy import engine_from_config, pool
from alembic import context

# --- IMPORT YOUR MODELS AND SETTINGS HERE ---
# Ensure these paths match your project structure
from app.db.base_class import Base  
from app.core.config import settings 

# This is the Alembic Config object
config = context.config

# 1. THE ASYNC-TO-SYNC BRIDGE
# FastAPI uses 'postgresql+asyncpg://', but Alembic requires 'postgresql://' (psycopg2)
original_url = settings.database_url
if original_url and "postgresql+asyncpg" in original_url:
    sync_url = original_url.replace("postgresql+asyncpg", "postgresql")
else:
    sync_url = original_url

# Inject the sync URL into the Alembic config
config.set_main_option("sqlalchemy.url", sync_url)

# 2. LOGGING SETUP
if config.config_file_name is not None:
    fileConfig(config.config_file_name)

# 3. METADATA FOR AUTOGENERATE
# This allows Alembic to see your Document and ChatHistory models
target_metadata = Base.metadata


def run_migrations_offline() -> None:
    """Run migrations in 'offline' mode (outputs SQL scripts)."""
    url = config.get_main_option("sqlalchemy.url")
    context.configure(
        url=url,
        target_metadata=target_metadata,
        literal_binds=True,
        dialect_opts={"paramstyle": "named"},
        compare_type=True, # Critical for JSON vs JSONB detection
    )

    with context.begin_transaction():
        context.run_migrations()


def run_migrations_online() -> None:
    """Run migrations in 'online' mode (executes against the DB)."""
    
    # Create the engine using the synchronous URL we set above
    connectable = engine_from_config(
        config.get_section(config.config_ini_section, {}),
        prefix="sqlalchemy.",
        poolclass=pool.NullPool,
    )

    with connectable.connect() as connection:
        context.configure(
            connection=connection, 
            target_metadata=target_metadata,
            compare_type=True, # Critical for JSON vs JSONB detection
        )

        with context.begin_transaction():
            context.run_migrations()


if context.is_offline_mode():
    run_migrations_offline()
else:
    run_migrations_online()