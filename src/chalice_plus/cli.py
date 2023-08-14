import click
import os
import subprocess
import sys

from chalice.constants import DEFAULT_STAGE_NAME

from chalice_plus.deploy_utils.alembic import (
    get_current_revision,
    upgrade_database,
    downgrade_database,
)
from chalice_plus.deploy_utils.config import load_ssm_parameters_to_config, restore_config
from chalice_plus.deploy_utils.files import (
    copy_chalice_plus_vendor_folder,
    remove_chalice_plus_vendor_folder
)


@click.group()
def cli():
    pass


@cli.command(
    context_settings=dict(ignore_unknown_options=True, allow_extra_args=True)
)
@click.option(
    "--stage",
    default=DEFAULT_STAGE_NAME,
    help=(
        "Name of the Chalice stage to deploy to. Specifying a new chalice stage will "
        "create an entirely new set of AWS resources."
    ),
)
@click.option(
    "--skip-migration",
    is_flag=True,
    default=False,
    help="Skip alembic migrations",
)
@click.pass_context
def deploy(ctx, stage, skip_migration):
    if not os.path.exists(".chalice/config.json"):
        click.echo("Unable to find chalice in current directory")
        return

    click.echo(f"Deploying to stage: {stage}")
    copy_chalice_plus_vendor_folder()

    if not skip_migration:
        current_revision = get_current_revision(stage)
        click.echo(f"Current alembic revision: {current_revision}")

        click.echo("Migrating database... ", nl=False)
        upgrade_database(stage)
        click.echo("Done")

    click.echo("Fetching SSM parameters... ", nl=False)
    load_ssm_parameters_to_config(stage)
    click.echo("Done")

    try:
        subprocess.run(["chalice", "deploy"] + sys.argv[2:])
    except subprocess.CalledProcessError as e:
        click.echo(f"Error: {e}", error=True)
        if not skip_migration:
            click.echo(
                f"Downgrading database to revision {current_revision}...", nl=False
            )
            downgrade_database(stage, current_revision)
            click.echo("Done")

    restore_config()
    remove_chalice_plus_vendor_folder()
