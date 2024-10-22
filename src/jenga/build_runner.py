"""The Jenga build runner."""

# Standard library imports
import os
import sys
import json
import warnings
import subprocess
from typing import Optional
from datetime import datetime

# Third-party imports
from fuzzywuzzy import process, fuzz

# Local imports
from .util import weidu_log_to_build_dict
from .config import (
    CFG,
    CfgKey,
    get_all_game_dirs,
)


def update_weidu_conf(game_dir: str, language: str) -> None:
    """Update or append the language setting in weidu.conf.

    Parameters
    ----------
    game_dir : str
        The directory where the game is installed.
    language : str
        The language to set in the configuration file. E.g. en_US, etc.
    """
    weidu_conf_path = os.path.join(game_dir, 'weidu.conf')
    lang_dir_line = f'lang_dir = {language}\n'
    # Read the original content of the configuration file
    # If the weidu.conf does not exist, initialize with the new language line
    if not os.path.exists(weidu_conf_path):
        with open(weidu_conf_path, 'w', encoding='utf-8') as f:
            f.write(lang_dir_line)
        return
    with open(weidu_conf_path, 'r', encoding='utf-8') as f:
        lines = f.readlines()
    # Check for existing lang_dir line
    for i, line in enumerate(lines):
        if line.startswith('lang_dir ='):
            lines[i] = lang_dir_line
            break
    else:
        # Append the line if not present
        lines.append(lang_dir_line)
    # Write back the content with the updated lang_dir line
    with open(weidu_conf_path, 'w', encoding='utf-8') as f:
        f.writelines(lines)


def fuzzy_find(directory: str, name: str, file_type: str = ".tp2") -> str:
    """ Fuzzy find the file matching the given name in directory.

    Parameters
    ----------
    directory : str
        The directory to search for the file.
    name : str
        The name of the file to search for.
    file_type : str, optional
        The file type to search for. Default is ".tp2".

    Returns
    -------
    str
        The path to the file found in the directory.
    """
    entries = [
        entry
        for entry in os.listdir(directory)
        if entry.lower().endswith(file_type)
    ]
    result = process.extractOne(
        name.lower(), entries, scorer=fuzz.ratio)
    if result is None:
        raise FileNotFoundError(
            f"Unable to locate {name}{file_type} in {directory}."
        )
    best_match, score = result
    if score < 50:
        raise FileNotFoundError(
            f"Unable to locate {name}{file_type} with "
            "sufficient accuracy in {directory.}"
        )
    return os.path.join(directory, best_match)


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
    weidu_log_path = os.path.join(install_dir, 'weidu.log')
    return weidu_log_to_build_dict(weidu_log_path)


def execute_mod_installation(
    weidu_exec_path: str, mod_tp2_path: str, install_dir: str,
    language_int: int, install_list: str, log_file: str,
) -> bool:
    """Execute installation command and return success.

    Parameters
    ----------
    weidu_exec_path : str
        The path to the WeiDU executable.
    mod_tp2_path : str
        The path to the .tp2 file of the mod.
    install_dir : str
        The directory where the game is installed.
    language_int : int
        The language integer to set in the installation.
    install_list : str
        The list of components to install.
    log_file : str
        The path to the log file to write logs to.
    """
    command = [
        weidu_exec_path,
        mod_tp2_path,
        "--no-exit-pause",
        "--game", install_dir,
        "--log", log_file,
        "--language", str(language_int),
        "--skip-at-view",
        "--force-install-list", install_list
    ]
    proc = subprocess.run(
        command, stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        check=False,
    )
    # Decode the stdout and stderr
    stdout_text = proc.stdout.decode('utf-8')
    stderr_text = proc.stderr.decode('utf-8')
    # Print stdout and stderr to screen
    print(stdout_text, end='')
    print(stderr_text, end='', file=sys.stderr)
    # Append stdout and stderr to the log file
    with open(log_file, 'ab') as lf:
        lf.write(proc.stdout)
        lf.write(proc.stderr)
    return proc.returncode == 0


def get_start_index_from_build_state_file(state_file_path: str) -> int:
    """Get build order start index from provided state file.

    Parameters
    ----------
    state_file_path : str
        The path to the state file.

    Returns
    -------
    int
        The start index of the resumed build order.
    """
    with open(state_file_path, 'r', encoding='utf-8') as f:
        build_state = json.load(f)
    return build_state['last_mod_index'] + 1


def write_ongoing_state(
    build_name: str, index: int, state_file_path: str,
) -> None:
    """ Write ongoing builg state to file.

    Parameters
    ----------
    build_name : str
        The name of the build.
    index : int
        The index of the last installed mod.
    state_file_path : str
        The name of the state file.
    """
    state = {'build_name': build_name, 'last_mod_index': index}
    with open(state_file_path, 'w', encoding='utf-8') as f:
        json.dump(state, f, indent=4)


def mod_is_installed_identically(
    mod_name: str,
    mod_version: str,
    installed_components: list,
    install_info: Optional[dict] = None,
) -> bool:
    """Check if the mod is installed identically.

    Parameters
    ----------
    mod_name : str
        The name of the mod.
    mod_version : str
        The version of the mod.
    installed_components : list
        The list of installed components.
    install_info : dict, optional
        The information about the mod installation.
        If not provided, returns False.

    Returns
    -------
    bool
        Whether the mod is installed identically.
    """
    if not install_info:
        return False
    return (
        install_info['mod_name'] == mod_name
        and install_info['mod_version'] == mod_version
        and set(install_info['components']) == set(installed_components)
    )


def run_build(
    build_file_path: str,
    extracted_mods_dir: Optional[str] = None,
    zipped_mods_dir: Optional[str] = None,
    weidu_exec_path: Optional[str] = None,
    game_install_dir: Optional[str] = None,
    state_file_path: Optional[str] = None,
    skip_installed_mods: Optional[bool] = False,
) -> None:
    """Run the build process.

    Parameters
    ----------
    build_file_path : str
        The path to the build file.
    extracted_mods_dir : str, optional
        The directory containing the extracted mods. If not provided, the path
        is looked for in your Jenga configuration. Failing that, a path to a
        zipped mods directory is required, either as an argument or in your
        Jenga configuration.
    zipped_mods_dir : str, optional
        The directory containing the zipped mods. If not provided, the path
        is looked for in your Jenga configuration. Failing that, all mods must
        be present in the extracted mods directory (a path to which must br
        provided).
    weidu_exec_path : str, optional
        The path to the WeiDU executable. If not provided, the path is looked
        for in your Jenga configuration.
    game_install_dir : str, optional
        The directory where the game is installed. If not provided, the path
        for an Infinitive Engine EE game is looked for in your Jenga
        configuration. If none, or more than one, is found, user intent is
        obscured and an error is raised.
    state_file_path : str, optional
        The path to the state file.
    skip_installed_mods : bool, optional
        Whether to skip the installation of already installed mods.
        Default is False.
    """
    # Handling optional arguments
    extracted_mods_dir = extracted_mods_dir or CFG[
        CfgKey.EXTRACTED_MOD_CACHE_DIR_PATH]
    if not extracted_mods_dir:
        warnings.warn(
            "No extracted mods directory provided or found in the "
            "configuration. The zipped mods directory must be provided."
        )
        raise ValueError(
            "A path to an extracted mods directory must be provided."
            "Zipped mod directory support is not implemented yet."
        )
    zipped_mods_dir = zipped_mods_dir or CFG[CfgKey.ZIPPED_MOD_CACHE_DIR_PATH]
    if not zipped_mods_dir:
        if not extracted_mods_dir:
            raise ValueError(
                "A path to neither a zipped mods directory or an extracted mod"
                " directory was provided. At least one must be provided."
                " Program exiting."
            )
    weidu_exec_path = weidu_exec_path or CFG[CfgKey.WEIDU_EXEC_PATH]
    if not weidu_exec_path:
        raise ValueError(
            "A path to the WeiDU executable must be provided."
        )
    game_dirs = get_all_game_dirs()
    if not game_install_dir:
        if not len(game_dirs) == 1:
            raise ValueError(
                "A path to the game directory to mod must be provided "
                "explicitly if there is not exactly one game directory path "
                "in your Jenga configuration."
            )
        game_install_dir = game_dirs[0]
        if not game_install_dir:
            raise ValueError(
                "A path to the game directory to mod must be provided."
            )

    # Load the build file
    with open(build_file_path, 'r', encoding='utf-8') as f:
        build = json.load(f)
    install_mod_state = None
    if skip_installed_mods:
        install_mod_state = get_mod_info_from_weidu_log(game_install_dir)

    build_name = build["config"]["build_name"]
    language = build["config"]["language"]
    force_language_in_weidu_conf = build["config"][
        "force_language_in_weidu_conf"]
    pause_every_x_mods = build["config"]["pause_every_x_mods"]
    mods = build["mods"]

    timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
    state_file_name = f'jenga_{build_name}_{timestamp}.json'
    state_file_path = os.path.join(game_install_dir, state_file_name)

    start_index = (
        get_start_index_from_build_state_file(state_file_path)
        if state_file_path else 0
    )

    for i in range(start_index, len(mods)):
        mod = mods[i]
        mod_name = mod["mod"]
        language_int = mod["language_int"]
        version = mod["version"]
        components = mod["components"]
        install_list = mod["install_list"]

        if skip_installed_mods and mod_is_installed_identically(
            mod_name, version, components, install_mod_state
        ):
            print(f"{mod_name} is already identically installed, skipping...")
            continue
        log_file = f'setup-{mod_name.lower().replace(" ", "_")}.debug'

        # Update Weidu.conf with the language if necessary
        if force_language_in_weidu_conf:
            update_weidu_conf(game_install_dir, language)

        # Find the mod directory and .tp2 file inside
        mod_dir = fuzzy_find(mods_dir, mod_name, "")
        mod_tp2_path = fuzzy_find(mod_dir, mod_name, ".tp2")

        print(f"Installing {mod_name}...")

        success = execute_mod_installation(
            weidu_exec_path, mod_tp2_path, game_install_dir,
            language_int, install_list, log_file
        )

        if not success:
            print(f"Installation of {mod_name} failed, stopping the process.")
            write_ongoing_state(build_name, i, state_file_path)
            print(f"Build state saved to {state_file_path}")
            sys.exit(1)

        # Pause installation every x mods as required
        if (i + 1) % pause_every_x_mods == 0:
            input(
                f"Paused after installing {pause_every_x_mods} mods. "
                "Press Enter to continue...")
