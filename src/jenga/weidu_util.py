"""Utility functions for WeiDU operations."""

# Standard library imports
import os

from .parsing import (
    weidu_log_to_build_dict,
)

# local imports
from .printing import oper_print


def update_weidu_conf(game_dir: str, lang: str) -> None:
    """Update or append the language setting in weidu.conf.

    Parameters
    ----------
    game_dir : str
        The directory where the game is installed.
    lang : str
        The lang dir to set in the configuration file. E.g. en_US, etc.

    """
    weidu_conf_path = os.path.join(game_dir, "weidu.conf")
    lang_dir_line = f"lang_dir = {lang}\n"
    oper_print(f"Setting {lang_dir_line[:-1]} in weidu.conf...")
    # Read the original content of the configuration file
    # If the weidu.conf does not exist, initialize with the new language line
    if not os.path.exists(weidu_conf_path):
        with open(weidu_conf_path, "w", encoding="utf-8") as f:
            f.write(lang_dir_line)
        return
    with open(weidu_conf_path, "r", encoding="utf-8") as f:
        lines = f.readlines()
    # Check for existing lang_dir line
    for i, line in enumerate(lines):
        if line.startswith("lang_dir ="):
            lines[i] = lang_dir_line
            break
    else:
        # Append the line if not present
        lines.append(lang_dir_line)
    # Write back the content with the updated lang_dir line
    with open(weidu_conf_path, "w", encoding="utf-8") as f:
        f.writelines(lines)


def get_mod_info_from_weidu_log(install_dir: str) -> dict:
    """Get mod information from WeiDU log file.

    Parameters
    ----------
    install_dir : str
        The directory where the game is installed.

    Returns
    -------
    dict
        A dictionary containing the mod information.

    """
    weidu_log_path = os.path.join(install_dir, "weidu.log")
    res = weidu_log_to_build_dict(weidu_log_path)
    mod_list = res["mods"]
    return {k["mod"]: k for k in mod_list}
