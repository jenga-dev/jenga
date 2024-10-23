"""Weidu log parsing functionality for Jenga."""

import re
from typing import Dict


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
                r"~([^/]+)/[^~]+~ #(\d+) #(\d+) // (.+): (.+)",
                line,
            )

            if match:
                mod_name = match.group(1)
                language_int = match.group(2)
                component_number = match.group(3)
                component_description = match.group(4)
                version = match.group(5)

                if mod_name not in mods_info:
                    mods_info[mod_name] = {
                        "mod": mod_name,
                        "version": version,
                        "language_int": language_int,
                        "install_list": [],
                        "components": [],
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
