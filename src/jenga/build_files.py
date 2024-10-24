"""Build files for Jenga."""

# standard library imports
import json
import pathlib
from datetime import datetime
from typing import Optional

import yaml

# 3rd party imports
# local imports
from .parsing import weidu_log_to_build_dict
from .printing import (
    oper_print,
    sccs_print,
)


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
    oper_print(
        "Converting WeiDU log file in:\n"
        f"{weidu_log_path}\n"
        "to a Jenga .json build file in:\n"
        f"{build_file_path}\n..."
    )
    result = weidu_log_to_build_dict(weidu_log_path)
    # Write the output to a JSON file
    with open(build_file_path, "wt+", encoding="utf-8") as json_file:
        json.dump(result, json_file, indent=4)
    sccs_print("Done.")


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
    oper_print(
        "Converting WeiDU log file in:\n"
        f"{weidu_log_path}\n"
        "to a Jenga .yaml build file in:\n"
        f"{build_file_path}\n..."
    )
    result = weidu_log_to_build_dict(weidu_log_path)
    # Write the output to a YAML file
    with open(build_file_path, "wt+", encoding="utf-8") as yaml_file:
        yaml.dump(result, yaml_file, default_flow_style=False, sort_keys=False)
    sccs_print("Done.")


def build_file_to_build_order_file(
    build_file_path: str,
    build_file_type: Optional[str] = None,
    build_order_file_path: Optional[str] = None,
) -> None:
    """Extracts mod build order and writes it to a text file.

    Parameters
    ----------
    build_file_path : str
        The path to the input build file.
    build_file_type : str, optional
        The type of the build file. If not provided, it is inferred from the
        file extension.
    build_order_file_path : str, optional
        The path to the output build order file. If not provided, a file name
        of the pattern jenga_build_order_<build_name>.txt will be created.

    """
    oper_print(
        "Extracting build order from Jenga build file in:\n"
        f"{build_file_path}\n"
    )
    if build_file_type is None:
        build_file_type = build_file_path.split(".")[-1]
    if build_file_type == "json":
        with open(build_file_path, "rt", encoding="utf-8") as build_file:
            build = json.load(build_file)
    elif build_file_type == "yaml":
        with open(build_file_path, "rt", encoding="utf-8") as build_file:
            build = yaml.safe_load(build_file)
    else:
        raise ValueError(
            f"Unsupported build file type: {build_file_type}. "
            "Supported types are 'json' and 'yaml'."
        )
    build_name = build["config"]["build_name"]
    if build_order_file_path is None:
        build_order_file_name = f"jenga_build_order_{build_name}.txt"
        build_file_dir = pathlib.Path(build_file_path).parent
        build_order_file_path = str(build_file_dir / build_order_file_name)
    mods = build["mods"]
    build_order = [mod["mod"] for mod in mods]
    with open(
        build_order_file_path, "wt+", encoding="utf-8"
    ) as build_order_file:
        for mod in build_order:
            build_order_file.write(f"{mod}\n")
    sccs_print(
        "Build order extracted and written to:\n" f"{build_order_file_path}\n"
    )


def reorder_build_file_by_build_order_file(
    build_file_path: str,
    build_order_file_path: str,
    reordered_build_file_path: Optional[str] = None,
) -> None:
    """Reorders the mod portion of a build file by a build order file.

    This method support the spliting of a mod install component into
    several ones.

    Also, every mod name encountered in the txt file that is not in the build
    will be added in the proper place in the mods list, with a generic
    description and no components, to prompt the user install it manually.

    This method supports both yaml and json build files, inferring the file
    type from the file extension.

    Parameters
    ----------
    build_file_path : str
        The path to the input build file.
    build_order_file_path : str
        The path to the build ordecr file, dictating new order.
    reordered_build_file_path : str, optional
        The path to the output reordered build file. If not provided, a file
        name of the pattern reordered_<build_file_name> will be created.

    Examples
    --------
    This method support the spliting of a mod install component into
    several ones.

    For example, if the build file contains the following mod install:
    mods: [
        {
            "mod": "ITEM_REV",
            "version": "V4 (Revised V1.3.900)",
            "language_int": "0",
            "install_list": "0 10 17 1030",
            "components": [
                {
                    "number": "0",
                    "description": "Item Revisions by Demivrgvs"
                },
                {
                    "number": "1030",
                    "description": "Store Revisions"
                },
                {
                    "number": "10",
                    "description": "Revised Shield Bonuses"
                },
                {
                    "number": "17",
                    "description": "Weapon Changes"
                }
            ]
        }
    ]
    And the build order file contains:
    ITEM_REV 0
    ITEM_REV 1030
    ITEM_REV 10 17 19 1070 1080 1200
    In three seperate rows (possibly not contiguous), the mods section of the
    reorderd build file will have split the ITEM_REV mod install into three
    seperate mod installs, each with its own components:
    mods: [
        {
            "mod": "ITEM_REV",
            "version": "V4 (Revised V1.3.900)",
            "language_int": "0",
            "install_list": "0",
            "components": [
                {
                    "number": "0",
                    "description": "Item Revisions by Demivrgvs"
                },
            ]
        },
        ...
        {
            "mod": "ITEM_REV",
            "version": "V4 (Revised V1.3.900)",
            "language_int": "0",
            "install_list": "1030",
            "components": [
                {
                    "number": "1030",
                    "description": "Store Revisions"
                },
            ]
        },
        ...
        {
            "mod": "ITEM_REV",
            "version": "V4 (Revised V1.3.900)",
            "language_int": "0",
            "install_list": "10 17",
            "components": [
                {
                    "number": "10",
                    "description": "Revised Shield Bonuses"
                },
                {
                    "number": "17",
                    "description": "Weapon Changes"
                }
            ]
        }
    ]

    Also, every mod name encountered in the txt file that is not in the build
    will be added in the proper place in the mods list, with a generic
    description and no components, to prompt the user install it manually.

    For example, encountering the following linse in the mod order file, where
    MOD_A and MOD_B are found in the build file, but MOD_NOT_IN_BUILD is not:
    MOD_A
    MOD_NOT_IN_BUILD
    MOD_B

    Will result in the following entry for MOD_NOT_IN_BUILD directly after the
    entery for MOD_A and directly before the entry for MOD_B:
    {
        "mod": "MOD_NOT_IN_BUILD",
        "version": "Unknown",
        "language_int": "0",
        "install_list": "0",
        "components": [],
        "prompt_for_manual_install": true
    }

    """
    oper_print(
        "Reordering Jenga build file in:\n"
        f"{build_file_path}\n"
        "by build order file in:\n"
        f"{build_order_file_path}\n..."
    )

    # Set up the output file path
    build_file_dir_path = pathlib.Path(build_file_path).parent
    reordered_build_file_name = (
        f"reordered_{pathlib.Path(build_file_path).name}"
    )
    reordered_build_file_path = str(
        build_file_dir_path / reordered_build_file_name
    )

    # Read the build file
    build_file_type = build_file_path.split(".")[-1]
    with open(build_file_path, "rt", encoding="utf-8") as build_file:
        if build_file_type == "json":
            build = json.load(build_file)
        elif build_file_type == "yaml":
            build = yaml.safe_load(build_file)
        else:
            raise ValueError(
                f"Unsupported build file type: {build_file_type}. "
                "Supported types are 'json' and 'yaml'."
            )

    # Read the build order file
    with open(
        build_order_file_path, "rt", encoding="utf-8"
    ) as build_order_file:
        build_order = build_order_file.readlines()

    # Reorder the build file
    mod_dict = {mod_entry["mod"]: mod_entry for mod_entry in build["mods"]}
    new_mods = []

    for line in build_order:
        parts = line.strip().split()
        if not parts:
            continue
        mod_name = parts[0]
        components = parts[1:]

        if mod_name in mod_dict:
            original_mod = mod_dict[mod_name]
            matched_components = [
                comp
                for comp in original_mod["components"]
                if comp["number"] in components
            ]

            # If no components specified, use all available
            if not components:
                matched_components = original_mod["components"]

            new_mod_entry = {
                "mod": mod_name,
                "version": original_mod.get("version", "Unknown"),
                "language_int": original_mod.get("language_int", "0"),
                "install_list": " ".join(
                    comp["number"] for comp in matched_components
                ),
                "components": matched_components,
            }
            new_mods.append(new_mod_entry)
        else:
            new_mods.append(
                {
                    "mod": mod_name,
                    "version": "Unknown",
                    "language_int": "0",
                    "install_list": "0",
                    "components": [],
                    "prompt_for_manual_install": True,
                }
            )

    build["mods"] = new_mods

    # Write the reordered build file
    with open(reordered_build_file_path, "wt", encoding="utf-8") as build_file:
        if build_file_type == "json":
            json.dump(build, build_file, indent=4)
        elif build_file_type == "yaml":
            yaml.dump(
                build, build_file, default_flow_style=False, sort_keys=False
            )

    sccs_print(
        "Build file reordered and written to:\n"
        f"{reordered_build_file_path}\n"
    )
