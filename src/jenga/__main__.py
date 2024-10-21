"""Command line interface for the jenga package."""

import typer
from typing_extensions import Annotated

from jenga import weidu_log_to_build_file

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
    print(build_file_path)


@app.command()
def resume_partial_build(
    build_file_path: str,
) -> None:
    """Resume a partial build of an BG:EET game.

    Parameters
    ----------

    """
    print(build_file_path)


@app.command()
def convert_weidu_log_to_build_file(
    weidu_log_path: str,
    build_file_path: Annotated[
        str, typer.Option(help="The path to the json build file to create.")
    ] = None,
) -> None:
    """Convert a WeiDU log file to a build file.

    Parameters
    ----------
    weidu_log_path : str
        The path to the WeiDU log file.

    """
    if build_file_path is None:
        build_file_path = weidu_log_path.replace(".log", ".json")
    print(
        "Converting WeiDU log file in:\n"
        f"{weidu_log_path}\n"
        "to a Jenga .json build file in:\n"
        f"{build_file_path}\n..."
    )
    weidu_log_to_build_file(weidu_log_path, build_file_path)


def cli():
    """Run the CLI."""
    app()


if __name__ == "__main__":
    cli()
