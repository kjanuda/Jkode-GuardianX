from logging.config import fileConfig

from alembic import context
from sqlalchemy import pool
from sqlalchemy.engine import Connection

from app.db.base import Base
from app.db.session import engine

# Important:
# importing app.models registers every SQLAlchemy model
import app.models  # noqa: F401


config = context.config


if config.config_file_name is not None:
    fileConfig(config.config_file_name)


target_metadata = Base.metadata


def include_object(
    object_,
    name,
    type_,
    reflected,
    compare_to,
):
    # PostGIS-managed system table.
    # Never let Alembic autogenerate create/drop it.
    if (
        type_ == "table"
        and name == "spatial_ref_sys"
    ):
        return False

    return True


def run_migrations_offline() -> None:
    database_url = engine.url.render_as_string(
        hide_password=False
    )

    context.configure(
        url=database_url,
        target_metadata=target_metadata,
        include_object=include_object,
        literal_binds=True,
        dialect_opts={
            "paramstyle": "named",
        },
        compare_type=True,
    )

    with context.begin_transaction():
        context.run_migrations()


def do_run_migrations(connection: Connection) -> None:
    context.configure(
        connection=connection,
        target_metadata=target_metadata,
        include_object=include_object,
        compare_type=True,
    )

    with context.begin_transaction():
        context.run_migrations()


def run_migrations_online() -> None:
    connectable = engine

    with connectable.connect() as connection:
        do_run_migrations(connection)


if context.is_offline_mode():
    run_migrations_offline()
else:
    run_migrations_online()


