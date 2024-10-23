"""Command line interface for the jenga package."""

import typer
from typing_extensions import Annotated

from jenga import (
    print_config_info_box,
    run_build,
    weidu_log_to_json_build_file,
    weidu_log_to_yaml_build_file,
)

app = typer.Typer()


@app.command()
def run_full_build(
    build_file_path: str,
) -> None:
    """Run a full build of an BG:EET game.

    Parameters
    ----------
    build_file_path : str
        The path to the build file.

    """
    run_build(
        build_file_path=build_file_path,
    )


@app.command()
def resume_partial_build(
    build_file_path: str,
    state_file_path: Annotated[
        str, typer.Option(help="The path to the state file to resume from.")
    ] = None,
) -> None:
    """Resume a partial build of an BG:EET game.

    Parameters
    ----------
    build_file_path : str
        The path to the build file.
    state_file_path : str, optional
        The path to the state file to resume from. If not provided, the game
        directory will be searched for the most recent state file for this
        build.
    """
    run_build(
        build_file_path=build_file_path,
        state_file_path=state_file_path,
        resume=True,
    )


@app.command()
def convert_weidu_log_to_json_build_file(
    weidu_log_path: str,
    build_file_path: Annotated[
        str, typer.Option(help="The path to the json build file to create.")
    ] = None,
) -> None:
    """Convert a WeiDU log file to a Jenga JSON build file.

    Parameters
    ----------
    weidu_log_path : str
        The path to the WeiDU log file.
    build_file_path : str, optional
        The path to the output JSON build file. If not provided, a file name
        of the pattern <date:time>_jenga_build_from_weidu_log.json will be
        created.

    """
    weidu_log_to_json_build_file(weidu_log_path, build_file_path)


@app.command()
def convert_weidu_log_to_yaml_build_file(
    weidu_log_path: str,
    build_file_path: Annotated[
        str, typer.Option(help="The path to the yaml build file to create.")
    ] = None,
) -> None:
    """Convert a WeiDU log file to a Jenga YAML build file.

    Parameters
    ----------
    weidu_log_path : str
        The path to the WeiDU log file.
    build_file_path : str, optional
        The path to the output YAML build file. If not provided, a file name
        of the pattern <date:time>_jenga_build_from_weidu_log.yaml will be
        created.

    """
    weidu_log_to_yaml_build_file(weidu_log_path, build_file_path)


@app.command()
def print_configuration() -> None:
    """Print the configuration."""
    print_config_info_box()


def cli():
    """Run the CLI."""
    app()


if __name__ == "__main__":
    cli()
