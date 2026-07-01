"""Alembic env.py — configures migration context.

Reads database URL from app config (.env) instead of alembic.ini hardcoded value.
"""

import os
import sys
from logging.config import fileConfig

from alembic import context
from sqlalchemy import engine_from_config, pool

# Add project root to path so we can import app.config
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "..", ".."))

config = context.config
if config.config_file_name is not None:
    fileConfig(config.config_file_name)

# Override sqlalchemy.url from app settings (.env)
try:
    from app.config import settings
    config.set_main_option("sqlalchemy.url", settings.database_url_sync)
except Exception:
    # Fallback: try reading from environment directly
    db_url = os.getenv("DATABASE_URL_SYNC") or os.getenv("DATABASE_URL")
    if db_url:
        config.set_main_option("sqlalchemy.url", db_url)

target_metadata = None


def run_migrations_offline():
    url = config.get_main_option("sqlalchemy.url")
    context.configure(url=url, target_metadata=target_metadata, literal_binds=True)
    with context.begin_transaction():
        context.run_migrations()


def run_migrations_online():
    connectable = engine_from_config(
        config.get_section(config.config_ini_section, {}),
        prefix="sqlalchemy.",
        poolclass=pool.NullPool,
    )
    with connectable.connect() as connection:
        context.configure(connection=connection, target_metadata=target_metadata)
        with connection.begin():
            context.run_migrations()


if context.is_offline_mode():
    run_migrations_offline()
else:
    run_migrations_online()
