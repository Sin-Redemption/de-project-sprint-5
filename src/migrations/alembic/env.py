from logging.config import fileConfig
from alembic import context
from sqlalchemy import engine_from_config, pool, text
from sqlalchemy import MetaData
from sqlalchemy.ext.declarative import declarative_base
from config import settings
metadata_base = MetaData(schema="metadata")
DeclarativeBase = declarative_base(metadata=metadata_base)
# this is the Alembic Config object, which provides
# access to the values within the .ini file in use.
config = context.config
# Interpret the config file for Python logging.
# This line sets up loggers basically.
fileConfig(config.config_file_name)
# add your model's MetaData object here
# for 'autogenerate' support
# from myapp import mymodel
# target_metadata = mymodel.Base.metadata
target_metadata = DeclarativeBase.metadata
# other values from the config, defined by the needs of env.py,
# can be acquired:
# my_important_option = config.get_main_option("my_important_option")
# ... etc.
config.set_main_option("sqlalchemy.url", settings.DATABASE_URI)
def run_migrations_online():
    """
    Run migrations in 'online' mode.
    In this scenario we need to create an Engine
    and associate a connection with the context.
    """
    engine = engine_from_config(
        config.get_section(config.config_ini_section),
        prefix="sqlalchemy.",
        poolclass=pool.NullPool,
    )
    with engine.connect() as connection:
        context.configure(
            connection=connection,
            target_metadata=target_metadata,
            include_schemas=True,
            compare_type=True,
            version_table_schema='public',
            version_table=settings.ALEMBIC_TABLE_NAME
        )
        with context.begin_transaction():
            # Need for rights another users from this role
            if settings.DATABASE_ROLE:
                connection.execute(text(f"SET ROLE {settings.DATABASE_ROLE}"))
            # Create alembic_version if not exists
            migration_context = context.get_context()
            migration_context._ensure_version_table()  # noQA
            # Forbidden several migrations
            connection.execute(text(f"LOCK TABLE public.{settings.ALEMBIC_TABLE_NAME} IN ACCESS EXCLUSIVE MODE"))
            context.execute("SET search_path to staging")
            context.run_migrations()
run_migrations_online()