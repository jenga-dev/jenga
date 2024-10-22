"""Utility functions for jenga."""

import json
import pathlib
import re
from datetime import datetime
from typing import Dict, Optional

import yaml


class ConfigurationError(Exception):
    """Configuration error."""

    pass


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


def _build_fpath_from_weidu_fpath(
    weidu_fpath: str,
    ext: str = "json",
) -> str:
    """Create a build file path from a WeiDU log file path.

    Parameters
    ----------
    weidu_fpath : str
        The path to the WeiDU log file.
    ext : str, optional
        The extension of the build file. Default is 'json'.

    Returns
    -------
    str
        The path to the build file.

    """
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    build_file_name: str = f"{timestamp}_jenga_build_from_weidu_log.{ext}"
    weidu_path_obj = pathlib.Path(weidu_fpath)
    dir_path = weidu_path_obj.parent
    build_file_path_obj = dir_path / build_file_name
    build_file_path = str(build_file_path_obj)
    return build_file_path


def weidu_log_to_json_build_file(
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
        created.

    """
    if build_file_path is None:
        build_file_path = _build_fpath_from_weidu_fpath(
            weidu_fpath=weidu_log_path,
            ext="json",
        )
    print(
        "Converting WeiDU log file in:\n"
        f"{weidu_log_path}\n"
        "to a Jenga .json build file in:\n"
        f"{build_file_path}\n..."
    )
    result = weidu_log_to_build_dict(weidu_log_path)
    # Write the output to a JSON file
    with open(build_file_path, "wt+", encoding="utf-8") as json_file:
        json.dump(result, json_file, indent=4)


def weidu_log_to_yaml_build_file(
    weidu_log_path: str, build_file_path: Optional[str] = None
) -> None:
    """Convert a WeiDU log file to a YAML build file.

    Parameters
    ----------
    weidu_log_path : str
        The path to the input WeiDU log file.
    build_file_path : str, optional
        The path to the output YAML build file. If not provided, a file name
        of the pattern <date:time>_jenga_build_from_weidu_log.yaml will be
        created.

    """
    if build_file_path is None:
        build_file_path = _build_fpath_from_weidu_fpath(
            weidu_fpath=weidu_log_path,
            ext="yaml",
        )
    print(
        "Converting WeiDU log file in:\n"
        f"{weidu_log_path}\n"
        "to a Jenga .yaml build file in:\n"
        f"{build_file_path}\n..."
    )
    result = weidu_log_to_build_dict(weidu_log_path)
    # Write the output to a YAML file
    with open(build_file_path, "wt+", encoding="utf-8") as yaml_file:
        yaml.dump(result, yaml_file, default_flow_style=False, sort_keys=False)


def mirror_backslashes_in_file(
    path: str,
) -> None:
    """Replace every \ in the input text file with an / character.

    Parameters
    ----------
    path : str
        The path to the input text file.
    """
    with open(path, "rt", encoding="utf-8") as file:
        text = file.read()
    text = text.replace("\\", "/")
    with open(path, "wt", encoding="utf-8") as file:
        file.write(text)
