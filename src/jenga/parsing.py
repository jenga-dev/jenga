"""Weidu log parsing functionality for Jenga."""

import os
import re
from typing import Dict

UNVERSIONED_MOD_MARKER = "UNVERSIONED"


def _get_tp2_rel_path_from_line(line: str) -> str:
    # Parse the line using regular expressions
    # line = ~mod_name/tp2_file.TP2~ #language_int #component_number // component_description: version
    match = re.match(
        r"~(.+\.TP2)~.*",
        line,
    )
    if match:
        return match.group(1)
    return ""


def weidu_log_to_build_dict(
    weidu_log_path: str,
) -> dict:
    """Convert a WeiDU log file to a Jenga in-memory build dict.

    Parameters
    ----------
    weidu_log_path : str
        The path to the input WeiDU log file.

    Returns
    -------
    dict
        A dictionary containing the build information.

    """
    if not os.path.exists(weidu_log_path):
        return {}
    # Dictionary to store mods information
    mods_info: Dict = {}

    # Read the input file
    with open(weidu_log_path, "rt", encoding="utf-8") as file:
        for line in file:
            line = line.strip()
            # Ignore comments
            if line.startswith("//") or not line:
                continue

            # Parse the line using regular expressions
            match = re.match(
                r"~(([^/]+)/)?([^~]+)\.TP2~ #(\d+) #(\d+) // (.+): (.+)",
                line,
            )
            if match:
                if match.group(2):
                    mod_name = match.group(2).lower()
                else:
                    mod_name = match.group(3).lower()
                language_int = match.group(4)
                component_number = match.group(5)
                component_description = match.group(6)
                version = match.group(7)
                tp2_rel_fpath = _get_tp2_rel_path_from_line(line)
                if mod_name not in mods_info:
                    mods_info[mod_name] = {
                        "mod": mod_name,
                        "version": version,
                        "language_int": language_int,
                        "install_list": [],
                        "components": [],
                        "tp2_rel_fpath": tp2_rel_fpath,
                    }
                mods_info[mod_name]["install_list"].append(component_number)
                mods_info[mod_name]["components"].append(
                    {
                        "number": component_number,
                        "description": component_description,
                    }
                )
                continue

            match2 = re.match(
                r"~(([^/]+)/)?([^~]+)\.TP2~ #(\d+) #(\d+) // (.+)",
                line,
            )
            if match2:
                if match2.group(2):
                    mod_name = match2.group(2).lower()
                else:
                    mod_name = match2.group(3).lower()
                language_int = match2.group(4)
                component_number = match2.group(5)
                component_description = match2.group(6)
                tp2_rel_fpath = _get_tp2_rel_path_from_line(line)
                if mod_name not in mods_info:
                    mods_info[mod_name] = {
                        "mod": mod_name,
                        "version": UNVERSIONED_MOD_MARKER,
                        "language_int": language_int,
                        "install_list": [],
                        "components": [],
                        "tp2_rel_fpath": tp2_rel_fpath,
                    }
                mods_info[mod_name]["install_list"].append(component_number)
                mods_info[mod_name]["components"].append(
                    {
                        "number": component_number,
                        "description": component_description,
                    }
                )

    # Convert install_list to a space-separated string
    for mod in mods_info.values():
        mod["install_list"] = " ".join(sorted(mod["install_list"], key=int))

    # Create the final dictionary structure for JSON
    result = {"mods": list(mods_info.values())}
    return result
