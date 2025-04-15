from __future__ import with_statement
from alembic import context
from sqlalchemy import engine_from_config, pool
from logging.config import fileConfig
import os
import sys

# Add the parent directory to path so we can import our app modules
sys.path.append(os.path.dirname(os.path.dirname(__file__)))

# Import our models for Alembic to detect
from app.database import Base

# This is the Alembic Config object
config = context.config

# Set the SQLAlchemy URL from the DATABASE_URL environment variable
db_url = os.getenv("DATABASE_URL")
if not db_url:
    # Fallback for local development
    db_url = "sqlite:///./pdf_qa.db"

# Replace the SQLAlchemy URL in the config
section = config.config_ini_section
config.set_section_option(section, "DB_URL", db_url)

# Interpret the config file for Python logging
fileConfig(config.config_file_name)

# Add your model's MetaData object here for 'autogenerate' support
target_metadata = Base.metadata

def run_migrations_offline():
    """Run migrations in 'offline' mode."""
    url = config.get_main_option("sqlalchemy.url")
    context.configure(
        url=url, target_metadata=target_metadata, literal_binds=True
    )

    with context.begin_transaction():
        context.run_migrations()

def run_migrations_online():
    """Run migrations in 'online' mode."""
    connectable = engine_from_config(
        config.get_section(config.config_ini_section),
        prefix="sqlalchemy.",
        poolclass=pool.NullPool,
    )

    with connectable.connect() as connection:
        context.configure(
            connection=connection,
            target_metadata=target_metadata
        )

        with context.begin_transaction():
            context.run_migrations()

if context.is_offline_mode():
    run_migrations_offline()
else:
    run_migrations_online()