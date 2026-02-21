from __future__ import with_statement
import os
from flask import current_app
from flask_sqlalchemy import SQLAlchemy
from flask_migrate import Migrate, MigrateCommand
from sqlalchemy import engine_from_config, pool
from alembic import context
from logging.config import fileConfig

db = SQLAlchemy()

def run_migrations_online():
    connectable = current_app.extensions['sqlalchemy'].db.engine
    with connectable.connect() as connection:
        context.configure(connection=connection, target_metadata=db.metadata)
        with context.begin_transaction():
            context.run_migrations()

run_migrations_online()
