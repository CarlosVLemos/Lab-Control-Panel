from alembic import context

from app.db.schema import metadata
from app.db.session import create_database_engine, database_url


def run():
    if context.is_offline_mode():
        context.configure(url=database_url(), target_metadata=metadata, literal_binds=True)
        with context.begin_transaction():
            context.run_migrations()
        return

    engine = create_database_engine()
    try:
        with engine.connect() as connection:
            context.configure(connection=connection, target_metadata=metadata)
            with context.begin_transaction():
                context.run_migrations()
    finally:
        engine.dispose()


run()
