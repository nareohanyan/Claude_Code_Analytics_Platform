from __future__ import annotations

from logging.config import fileConfig
from pathlib import Path
import sys

from alembic import context
from sqlalchemy import engine_from_config, pool


PROJECT_ROOT = Path(__file__).resolve().parents[1]
SRC_DIR = PROJECT_ROOT / "src"
if str(SRC_DIR) not in sys.path:
    sys.path.insert(0, str(SRC_DIR))

from claude_analytics.config import AppConfig  # noqa: E402
from claude_analytics.db.base import Base  # noqa: E402
from claude_analytics.db import models  # noqa: F401,E402


config = context.config

if config.config_file_name is not None:
    fileConfig(config.config_file_name)

app_config = AppConfig.from_env()
config.set_main_option("sqlalchemy.url", app_config.database_url)

target_metadata = Base.metadata


def run_migrations_offline() -> None:
    context.configure(
        url=app_config.database_url,
        target_metadata=target_metadata,
        literal_binds=True,
        compare_type=True,
        dialect_opts={"paramstyle": "named"},
    )

    with context.begin_transaction():
        context.run_migrations()


def run_migrations_online() -> None:
    connectable = engine_from_config(
        config.get_section(config.config_ini_section, {}),
        prefix="sqlalchemy.",
        poolclass=pool.NullPool,
    )

    with connectable.connect() as connection:
        context.configure(
            connection=connection,
            target_metadata=target_metadata,
            compare_type=True,
        )

        with context.begin_transaction():
            context.run_migrations()


if context.is_offline_mode():
    run_migrations_offline()
else:
    run_migrations_online()
