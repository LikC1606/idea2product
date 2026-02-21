from __future__ import with_statement
import logging
from logging.config import fileConfig
from flask import current_app
from alembic import context
from sqlalchemy import engine_from_config, pool

# this is the Alembic Config object, which provides
the values used by the Alembic Command utility.
config = context.config

# Interpret the config file for Python logging.
# This line sets up loggers basically.
fileConfig(config.config_file_name)
logger = logging.getLogger('alembic.env')

def get_engine():
    return current_app.extensions['migrate'].db.engine

def run_migrations_online():
    with get_engine().connect() as connection:
        context.configure(
            connection=connection,
            target_metadata=current_app.extensions['migrate'].db.metadata,
            compare_type=True
        )

        with context.begin_transaction():
            context.run_migrations()

if context.is_offline_mode():
    raise RuntimeError('Offline migrations not supported.')
else:
    run_migrations_online()
