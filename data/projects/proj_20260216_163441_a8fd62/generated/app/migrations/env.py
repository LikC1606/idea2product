from __future__ import with_statement
import logging
from flask import current_app
from logging.config import fileConfig
from alembic import context
from sqlalchemy import engine_from_config, pool

# Interpret the config file for Python logging.
# This line sets up loggers basically.
fileConfig(context.config.config_file_name)
logger = logging.getLogger('alembic.env')

def run_migrations_online():
    # Connect to the database using SQLAlchemy's engine
    connectable = current_app.extensions['migrate'].db.engine

    with connectable.connect() as connection:
        context.configure(connection=connection, target_metadata=current_app.extensions['migrate'].db.metadata)

        with context.begin_transaction():
            context.run_migrations()

run_migrations_online()