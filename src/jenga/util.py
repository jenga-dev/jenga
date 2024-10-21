"""Utility functions for jenga."""

import json
import re
from typing import Dict


def weidu_log_to_build_file(input_file: str, output_file: str) -> None:
    """Convert a WeiDU log file to a JSON build file.

    Parameters
    ----------
    input_file : str
        The path to the input WeiDU log file.
    output_file : str
        The path to the output JSON build file.

    """
    # Dictionary to store mods information
    mods_info: Dict = {}

    # Read the input file
    with open(input_file, "rt", encoding="utf-8") as file:
        for line in file:
            line = line.strip()
            # Ignore comments
            if line.startswith("//") or not line:
                continue

            # Parse the line using regular expressions
            match = re.match(r"~([^/]+)/[^~]+~ #(\d+) #(\d+) // .+", line)

            if match:
                mod_name = match.group(1)
                language_int = match.group(2)
                component_number = match.group(3)

                if mod_name not in mods_info:
                    mods_info[mod_name] = {
                        "mod": mod_name,
                        "language_int": language_int,
                        "install_list": [],
                    }

                mods_info[mod_name]["install_list"].append(component_number)

    # Convert install_list to a space-separated string
    for mod in mods_info.values():
        mod["install_list"] = " ".join(sorted(mod["install_list"], key=int))

    # Create the final dictionary structure for JSON
    result = {"mods": list(mods_info.values())}

    # Write the output to a JSON file
    with open(output_file, "wt+", encoding="utf-8") as json_file:
        json.dump(result, json_file, indent=4)
