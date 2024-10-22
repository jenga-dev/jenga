"""Utility functions for jenga."""

import re
import json
import pathlib
from datetime import datetime
from typing import Dict, Optional


def weidu_log_to_build_file(
    weidu_log_path: str,
    build_file_path: Optional[str] = None,
) -> None:
    """Convert a WeiDU log file to a JSON build file.

    Parameters
    ----------
    weidu_log_path : str
        The path to the input WeiDU log file.
    build_file_path : str, optional
        The path to the output JSON build file. If not provided, a file name
        of the pattern <date:time>_jenga_build_from_weidu_log.json will be
        created/
    """
    if build_file_path is None:
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        build_file_name: str = f"{timestamp}_jenga_build_from_weidu_log.json"
        weidu_path_obj = pathlib.Path(weidu_log_path)
        dir_path = weidu_path_obj.parent
        build_file_path_obj = dir_path / build_file_name
        build_file_path = str(build_file_path_obj)
    print(
        "Converting WeiDU log file in:\n"
        f"{weidu_log_path}\n"
        "to a Jenga .json build file in:\n"
        f"{build_file_path}\n..."
    )
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

    # Write the output to a JSON file
    with open(build_file_path, "wt+", encoding="utf-8") as json_file:
        json.dump(result, json_file, indent=4)
