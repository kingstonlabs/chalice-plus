import sys
import os

from functools import cache

from alembic import command
from alembic.config import Config
from alembic.migration import MigrationContext
from sqlalchemy import create_engine

from .config import get_app_name
from .ssm import get_ssm_parameter


@cache
def get_connection_string(stage):
    app_name = get_app_name()
    DATABASE_USER = get_ssm_parameter(app_name, stage, "DATABASE_USER")
    DATABASE_PASSWORD = get_ssm_parameter(app_name, stage, "DATABASE_PASSWORD")
    DATABASE_HOST = get_ssm_parameter(app_name, stage, "DATABASE_HOST")
    DATABASE_NAME = get_ssm_parameter(app_name, stage, "DATABASE_NAME")
    return (
        f"postgresql+psycopg2://{DATABASE_USER}:{DATABASE_PASSWORD}"
        f"@{DATABASE_HOST}/{DATABASE_NAME}"
    )


def get_db_engine(stage):
    connection_string = get_connection_string(stage)
    return create_engine(connection_string)


def get_current_revision(stage):
    connection_string = get_connection_string(stage)
    engine = create_engine(connection_string)
    with engine.begin() as connection:
        context = MigrationContext.configure(connection)
        return context.get_current_revision()


def run_alembic_command(stage, function, *args, **kwargs):
    project_path = os.getcwd()
    sys.path.insert(0, project_path)
    connection_string = get_connection_string(stage)
    config = Config('alembic.ini')
    config.set_main_option('script_location', os.path.join(project_path, "alembic"))
    config.set_main_option('sqlalchemy.url', connection_string)
    getattr(command, function)(config, *args, **kwargs)
    sys.path.remove(project_path)


def upgrade_database(stage):
    run_alembic_command(stage, "upgrade", "head")


def downgrade_database(stage, revision):
    run_alembic_command(stage, "downgrade", revision)
