from __future__ import with_statement
import logging
from flask import current_app
from alembic import context
from sqlalchemy import engine_from_config, pool
from sqlalchemy import MetaData
USE_TWOPHASE = False
config = context.config
metadata = MetaData()
def run_migrations():
    connectable = current_app.extensions['migrate'].db.engine
    with connectable.connect() as connection:
        context.configure(connection=connection, target_metadata=metadata)
        with context.begin_transaction():
            context.run_migrations()
if context.is_offline_mode():
    context.configure(url=config.get_main_option('sqlalchemy.url'))
    with context.begin_transaction():
        context.run_migrations()
else:
    run_migrations()