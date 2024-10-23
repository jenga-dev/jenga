"""Build files for Jenga."""

# standard library imports
import json
import pathlib
from datetime import datetime
from typing import Optional

# 3rd party imports
import yaml

# local imports
from .parsing import weidu_log_to_build_dict


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
