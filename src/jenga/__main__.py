"""Command line interface for the jenga package."""

# stdlib imports
from typing import Optional

# 3rd party imports
import typer
from typing_extensions import Annotated

# local imports
from jenga import (
    build_file_to_build_order_file,
    extract_all_archives_in_zipped_mods_dir_to_extracted_mods_dir,
    extract_some_archives_in_zipped_mods_dir_to_extracted_mods_dir,
    overwrite_game_dir_with_source_dir,
    populate_mod_index_from_extracted_mods_dir,
    print_config_info_box,
    run_build,
    weidu_log_to_json_build_file,
    weidu_log_to_yaml_build_file,
)
from jenga import (
    reorder_build_file_by_build_order_file as reorder_bfile_by_border_file,
)

app = typer.Typer()


@app.command()
def run_full_build(
    build_file_path: Annotated[
        str, typer.Argument(help="The path to the build file.")
    ],
) -> None:
    """Run a full build of a modded BG:EET game."""
    run_build(
        build_file_path=build_file_path,
    )


@app.command()
def resume_partial_build(
    build_file_path: Annotated[
        str, typer.Argument(help="The path to the build file.")
    ],
    state_file_path: Annotated[
        Optional[str],
        typer.Option(
            help=(
                "The path to the state file to resume from. If not provided, the game "
                "directory will be searched for the most recent state file for this "
                "build."
            )
        ),
    ] = None,
) -> None:
    """Resume a partial build of an BG:EET game."""
    run_build(
        build_file_path=build_file_path,
        state_file_path=state_file_path,
        resume=True,
    )


@app.command()
def convert_weidu_log_to_json_build_file(
    weidu_log_path: Annotated[
        str, typer.Argument(help="The path to the WeiDU log file.")
    ],
    build_file_path: Annotated[
        Optional[str],
        typer.Option(
            help=(
                "The path to the json build file to create. If not provided, a file "
                "named '<date:time>_jenga_build_from_weidu_log.json' will be created "
                "in the same directory as the WeiDU log file."
            )
        ),
    ] = None,
) -> None:
    """Convert a WeiDU log file to a Jenga JSON build file."""
    weidu_log_to_json_build_file(weidu_log_path, build_file_path)


@app.command()
def convert_weidu_log_to_yaml_build_file(
    weidu_log_path: Annotated[
        str, typer.Argument(help="The path to the WeiDU log file.")
    ],
    build_file_path: Annotated[
        Optional[str],
        typer.Option(
            help=(
                "The path to the yaml build file to create. If not provided, a file "
                "named '<date:time>_jenga_build_from_weidu_log.yaml' will be created "
                "in the same directory as the WeiDU log file."
            )
        ),
    ] = None,
) -> None:
    """Convert a WeiDU log file to a Jenga YAML build file."""
    weidu_log_to_yaml_build_file(weidu_log_path, build_file_path)


@app.command()
def convert_build_file_to_build_order_file(
    build_file_path: Annotated[
        str, typer.Argument(help="The path to the Jenga build file.")
    ],
    build_order_file_path: Annotated[
        Optional[str],
        typer.Option(
            help=(
                "The path to the build order file to create. If not provided, "
                "a file named 'jenga_build_order_<build_file_name>.json' will be "
                "created in the same directory as the build file."
            )
        ),
    ] = None,
) -> None:
    """Convert a Jenga build file to a Jenga build order file."""
    build_file_to_build_order_file(build_file_path, build_order_file_path)


@app.command()
def reorder_build_file_by_build_order_file(
    build_file_path: Annotated[
        str, typer.Argument(help="The path to the Jenga build file.")
    ],
    build_order_file_path: Annotated[
        str, typer.Argument(help="The path to the Jenga build order file.")
    ],
    reordered_build_file_path: Annotated[
        Optional[str],
        typer.Option(
            help=(
                "The path to the reordered build file to create. If not provided, "
                "a file named 'reordered_<build_file_name>.json' will be created "
                "in the same directory as the build file."
            )
        ),
    ] = None,
) -> None:
    """Reorder a Jenga build file by a Jenga build order file."""
    reorder_bfile_by_border_file(
        build_file_path,
        build_order_file_path,
        reordered_build_file_path,
    )


@app.command()
def extract_zipped_mods_to_extracted_mods() -> None:
    """Extract all zipped mods to the extracted mods directory."""
    extract_all_archives_in_zipped_mods_dir_to_extracted_mods_dir()


@app.command()
def extract_some_zipped_mods_to_extracted_mods(
    archive_name_part: Annotated[
        str,
        typer.Argument(
            help=(
                "All archives with names containing this string will be extracted."
            )
        ),
    ],
) -> None:
    """Extract archives containing a given string to the extracted mods dir."""
    extract_some_archives_in_zipped_mods_dir_to_extracted_mods_dir(
        archive_name_part
    )


@app.command()
def populate_mod_index() -> None:
    """Populate the mod index from the extracted mods directory."""
    populate_mod_index_from_extracted_mods_dir()


@app.command()
def extract_zipped_mods_and_populate_mod_index() -> None:
    """Extract all zipped mods to the extracted mods directory and populate the
    mod index.
    """
    extract_all_archives_in_zipped_mods_dir_to_extracted_mods_dir()
    populate_mod_index_from_extracted_mods_dir()


@app.command()
def overwrite_game_dir_with_clean_source_dir(
    game: Annotated[
        str,
        typer.Argument(
            help="The game alias to overwrite the game directory for. E.g. 'BG2EE'."
        ),
    ],
    eet: Annotated[
        bool,
        typer.Option(
            "--eet",
            help=(
                "Use the configured EET-installed game directory as source, "
                "rather than the configured clean game directory."
            ),
        ),
    ] = False,
) -> None:
    """Overwrite the game directory with the clean source directory."""
    game = game.strip("'")
    if eet:
        overwrite_game_dir_with_source_dir(game, "EET_SOURCE")
    else:
        overwrite_game_dir_with_source_dir(game, "CLEAN_SOURCE")


@app.command()
def print_configuration() -> None:
    """Print the current Jenga configuration.

    This shows the configuration as set by ~/.config/jenga/cfg.json and/or
    valid JENGA__ prefixed environment variables.

    """
    print_config_info_box()


def cli():
    """Run the CLI."""
    app()


if __name__ == "__main__":
    cli()
