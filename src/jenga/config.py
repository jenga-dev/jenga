"""Configuration control for jenga."""

# stdlib imports
import os
from typing import Optional, Union

# 3rd party imports
import birch
from rich.console import Console
from rich.table import Table


class CfgKey:
    """Configuration keys for jenga."""

    WEIDU_EXEC_PATH = "WEIDU_EXEC_PATH"
    ZIPPED_MOD_CACHE_DIR_PATH = "ZIPPED_MOD_CACHE_DIR_PATH"
    EXTRACTED_MOD_CACHE_DIR_PATH = "EXTRACTED_MOD_CACHE_DIR_PATH"
    DEFAULT_LANG = "DEFAULT_LANG"
    NUM_RETRIES = "NUM_RETRIES"
    STOP_ON_WARNING = "STOP_ON_WARNING"
    STOP_ON_ERROR = "STOP_ON_ERROR"
    # game paths configuration keys
    BGEE_DIR_PATHS = "BGEE_DIR_PATHS"
    BGIIEE_DIR_PATHS = "BGIIEE_DIR_PATHS"
    IWDEE_DIR_PATHS = "IWDEE_DIR_PATHS"
    IWD2EE_DIR_PATHS = "IWD2EE_DIR_PATHS"
    PSTEE_DIR_PATHS = "PSTEE_DIR_PATHS"
    # game paths configuration sub-keys
    TARGET = "TARGET"
    CLEAN_SOURCE = "CLEAN_SOURCE"
    EET_SOURCE = "EET_SOURCE"
    BGEE_SOURCE = "BGEE_SOURCE"


GAME_DIR_PATHS_KEYS = [
    CfgKey.BGEE_DIR_PATHS,
    CfgKey.BGIIEE_DIR_PATHS,
    CfgKey.IWDEE_DIR_PATHS,
    CfgKey.IWD2EE_DIR_PATHS,
    CfgKey.PSTEE_DIR_PATHS,
]


CFG = birch.Birch(
    namespace="jenga",
    defaults={
        CfgKey.DEFAULT_LANG: "en_us",
        CfgKey.NUM_RETRIES: 0,
        CfgKey.STOP_ON_WARNING: False,
        CfgKey.STOP_ON_ERROR: True,
    },
    default_casters={
        CfgKey.NUM_RETRIES: int,
        CfgKey.STOP_ON_WARNING: bool,
        CfgKey.STOP_ON_ERROR: bool,
    },
)


WEIDU_EXEC_PATH = CFG.get(CfgKey.WEIDU_EXEC_PATH)
ZIPPED_MOD_CACHE_DIR_PATH = CFG.get(CfgKey.ZIPPED_MOD_CACHE_DIR_PATH)
EXTRACTED_MOD_CACHE_DIR_PATH = CFG.get(CfgKey.EXTRACTED_MOD_CACHE_DIR_PATH)
DEFAULT_LANG = CFG.get(CfgKey.DEFAULT_LANG)
NUM_RETRIES = CFG.get(CfgKey.NUM_RETRIES)
STOP_ON_WARNING = CFG.get(CfgKey.STOP_ON_WARNING)
STOP_ON_ERROR = CFG.get(CfgKey.STOP_ON_ERROR)


def get_all_target_game_dirs() -> list[str]:
    """Get all game directories."""
    paths = []
    for key in GAME_DIR_PATHS_KEYS:
        try:
            paths.append(CFG[key][CfgKey.TARGET])
        except KeyError:
            pass
    return paths


def print_config() -> None:
    """Print the configuration."""
    print(CFG.as_str())


def print_config_info_box() -> None:
    """Print the configuration in a rich info box."""
    console = Console()
    table = Table(title="Jenga Configuration", show_header=False)
    table.add_column("Key", style="bold")
    table.add_column("Value", style="bold")
    for key, value in CFG._val_dict.items():
        table.add_row(key, str(value))
    console.print(table)


_GAME_ALIAS_TO_DIR_PATHS_KEY = {
    "bgee": CfgKey.BGEE_DIR_PATHS,
    "bg:ee": CfgKey.BGEE_DIR_PATHS,
    "baldur's gate": CfgKey.BGEE_DIR_PATHS,
    "balder's gate: enhanced edition": CfgKey.BGEE_DIR_PATHS,
    "bgiiee": CfgKey.BGIIEE_DIR_PATHS,
    "bgii:ee": CfgKey.BGIIEE_DIR_PATHS,
    "baldur's gate ii": CfgKey.BGIIEE_DIR_PATHS,
    "balder's gate ii: enhanced edition": CfgKey.BGIIEE_DIR_PATHS,
    "baldur's gate 2": CfgKey.BGIIEE_DIR_PATHS,
    "baldur's gate 2: enhanced edition": CfgKey.BGIIEE_DIR_PATHS,
    "bg2ee": CfgKey.BGIIEE_DIR_PATHS,
    "bg2:ee": CfgKey.BGIIEE_DIR_PATHS,
    "iwdee": CfgKey.IWDEE_DIR_PATHS,
    "iwd:ee": CfgKey.IWDEE_DIR_PATHS,
    "icewind dale": CfgKey.IWDEE_DIR_PATHS,
    "icewind dale: enhanced edition": CfgKey.IWDEE_DIR_PATHS,
    "iwd2ee": CfgKey.IWD2EE_DIR_PATHS,
    "iwd2:ee": CfgKey.IWD2EE_DIR_PATHS,
    "icewind dale ii": CfgKey.IWD2EE_DIR_PATHS,
    "icewind dale ii: enhanced edition": CfgKey.IWD2EE_DIR_PATHS,
    "icewind dale 2": CfgKey.IWD2EE_DIR_PATHS,
    "icewind dale 2: enhanced edition": CfgKey.IWD2EE_DIR_PATHS,
    "pstee": CfgKey.PSTEE_DIR_PATHS,
    "pst:ee": CfgKey.PSTEE_DIR_PATHS,
    "planescape torment": CfgKey.PSTEE_DIR_PATHS,
    "planescape: torment: enhanced edition": CfgKey.PSTEE_DIR_PATHS,
}


def get_game_dir(
    game_alias: Optional[str] = None,
    sub_key: Optional[str] = None,
) -> str | None:
    """Get the game directory path for the given game alias.

    Parameters
    ----------
    game_alias : str
        The game alias.
    sub_key : str
        The sub-key to get, representing a specific variant of the game
        directory. By default, the target directory is returned.

    Returns
    -------
    str | None
        The path to the game directory.

    """
    if game_alias is None:
        return None
    key = _GAME_ALIAS_TO_DIR_PATHS_KEY.get(game_alias.lower())
    if key is None:
        return None
    game_dir_paths = CFG.get(key)
    if game_dir_paths is None:
        return None
    if sub_key is None:
        return CFG[key][CfgKey.TARGET]
    return CFG[key][sub_key]


def demand_valid_dir_path_config_val(
    dir_path: Union[str, None],
    config_key: str,
) -> str:
    """Check if the directory path is valid.

    Parameters
    ----------
    dir_path : str or None
        The directory path to check.
    config_key : str
        The configuration key.

    Returns
    -------
    str
        The valid directory path.

    """
    if dir_path is None:
        raise ValueError(f"{config_key} is  not set.")
    if not os.path.exists(dir_path):
        raise FileNotFoundError(
            f"{config_key} set to {dir_path}, which does not exist."
        )
    if os.path.isfile(dir_path):
        raise IsADirectoryError(
            f"{config_key} set to {dir_path}, which is a file instead "
            "of a directory."
        )
    return dir_path


def demand_zipped_mod_cache_dir_path() -> str:
    """Get the zipped mod cache directory path."""
    return demand_valid_dir_path_config_val(
        ZIPPED_MOD_CACHE_DIR_PATH, CfgKey.ZIPPED_MOD_CACHE_DIR_PATH
    )


def demand_extracted_mod_cache_dir_path() -> str:
    """Get the extracted mod cache directory path."""
    return demand_valid_dir_path_config_val(
        EXTRACTED_MOD_CACHE_DIR_PATH, CfgKey.EXTRACTED_MOD_CACHE_DIR_PATH
    )


def demand_game_dir_path(game_alias, dir_type: Optional[str]) -> str:
    """Get the game directory path.

    Parameters
    ----------
    game_alias : str
        The game alias.
    dir_type : str, optional
        The game directory type to return. Default is the target directory.

    """
    if dir_type is None:
        dir_type = CfgKey.TARGET
    game_dir = get_game_dir(game_alias, dir_type)
    if game_dir is None:
        raise ValueError(
            f"{dir_type} game directory is not set for game {game_alias}."
        )
    return demand_valid_dir_path_config_val(
        game_dir, f"{game_alias} game directory"
    )
