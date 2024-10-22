"""Configuration control for jenga."""

from typing import Optional

import birch


class CfgKey:
    """Configuration keys for jenga."""

    WEIDU_EXEC_PATH = "WEIDU_EXEC_PATH"
    BGEE_DIR_PATH = "BGEE_DIR_PATH"
    BGIIEE_DIR_PATH = "BGIIEE_DIR_PATH"
    IWDEE_DIR_PATH = "IWDEE_DIR_PATH"
    IWD2EE_DIR_PATH = "IWD2EE_DIR_PATH"
    PSTEE_DIR_PATH = "PSTEE_DIR_PATH"
    ZIPPED_MOD_CACHE_DIR_PATH = "ZIPPED_MOD_CACHE_DIR_PATH"
    EXTRACTED_MOD_CACHE_DIR_PATH = "EXTRACTED_MOD_CACHE_DIR_PATH"
    DEFAULT_LANGUAGE = "DEFAULT_LANGUAGE"
    NUM_RETRIES = "NUM_RETRIES"
    STOP_ON_WARNING = "STOP_ON_WARNING"
    STOP_ON_ERROR = "STOP_ON_ERROR"


CFG = birch.Birch(
    namespace="jenga",
    defaults={
        CfgKey.DEFAULT_LANGUAGE: "en_us",
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
BGEE_DIR_PATH = CFG.get(CfgKey.BGEE_DIR_PATH)
BGIIEE_DIR_PATH = CFG.get(CfgKey.BGIIEE_DIR_PATH)
IWDEE_DIR_PATH = CFG.get(CfgKey.IWDEE_DIR_PATH)
IWD2EE_DIR_PATH = CFG.get(CfgKey.IWD2EE_DIR_PATH)
PSTEE_DIR_PATH = CFG.get(CfgKey.PSTEE_DIR_PATH)
ZIPPED_MOD_CACHE_DIR_PATH = CFG.get(CfgKey.ZIPPED_MOD_CACHE_DIR_PATH)
EXTRACTED_MOD_CACHE_DIR_PATH = CFG.get(CfgKey.EXTRACTED_MOD_CACHE_DIR_PATH)
DEFAULT_LANGUAGE = CFG.get(CfgKey.DEFAULT_LANGUAGE)
NUM_RETRIES = CFG.get(CfgKey.NUM_RETRIES)
STOP_ON_WARNING = CFG.get(CfgKey.STOP_ON_WARNING)
STOP_ON_ERROR = CFG.get(CfgKey.STOP_ON_ERROR)


def get_all_game_dirs() -> list[str | None]:
    """Get all game directories."""
    paths = [
        BGEE_DIR_PATH,
        BGIIEE_DIR_PATH,
        IWDEE_DIR_PATH,
        IWD2EE_DIR_PATH,
        PSTEE_DIR_PATH,
    ]
    return [p for p in paths if p is not None]


def print_config() -> None:
    """Print the configuration."""
    print(CFG.as_str())


_GAME_ALIAS_TO_DIR_PATH = {
    "bgee": BGEE_DIR_PATH,
    "bg:ee": BGEE_DIR_PATH,
    "baldur's gate": BGEE_DIR_PATH,
    "balder's gate: enhanced edition": BGEE_DIR_PATH,
    "bgiiee": BGIIEE_DIR_PATH,
    "bgii:ee": BGIIEE_DIR_PATH,
    "baldur's gate ii": BGIIEE_DIR_PATH,
    "balder's gate ii: enhanced edition": BGIIEE_DIR_PATH,
    "baldur's gate 2": BGIIEE_DIR_PATH,
    "baldur's gate 2: enhanced edition": BGIIEE_DIR_PATH,
    "bg2ee": BGIIEE_DIR_PATH,
    "bg2:ee": BGIIEE_DIR_PATH,
    "iwdee": IWDEE_DIR_PATH,
    "iwd:ee": IWDEE_DIR_PATH,
    "icewind dale": IWDEE_DIR_PATH,
    "icewind dale: enhanced edition": IWDEE_DIR_PATH,
    "iwd2ee": IWD2EE_DIR_PATH,
    "iwd2:ee": IWD2EE_DIR_PATH,
    "icewind dale ii": IWD2EE_DIR_PATH,
    "icewind dale 2: enhanced edition": IWD2EE_DIR_PATH,
    "icewind dale 2": IWD2EE_DIR_PATH,
    "icewind dale 2: enhanced edition": IWD2EE_DIR_PATH,
    "pstee": PSTEE_DIR_PATH,
    "pst:ee": PSTEE_DIR_PATH,
    "planescape torment": PSTEE_DIR_PATH,
    "planescape: torment: enhanced edition": PSTEE_DIR_PATH,
}


def get_game_dir(game_alias: Optional[str] = None) -> str | None:
    """Get the game directory path for the given game alias.

    Parameters
    ----------
    game_alias : str
        The game alias.

    Returns
    -------
    str | None
        The path to the game directory.

    """
    if game_alias is None:
        return None
    return _GAME_ALIAS_TO_DIR_PATH.get(game_alias.lower())
