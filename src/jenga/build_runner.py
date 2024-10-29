"""The Jenga build runner."""

# Standard library imports
import json
import os
import shutil
import subprocess
import sys
import warnings
from datetime import datetime
from enum import Enum
from pathlib import Path
from typing import Dict, List, Optional, Tuple

# Third-party imports
from rich.console import Console
from rich.table import Table

# Local imports
from .config import (
    CFG,
    CfgKey,
    get_all_target_game_dirs,
    get_game_dir,
    print_config_info_box,
)
from .errors import (
    ConfigurationError,
    IllformedExtractedModDirError,
)
from .fixes import (
    get_cmd_fixes_for_mod,
    get_prepost_fixes_for_mod,
)
from .fs_basics import dir_name_from_dir_path
from .fs_util import (
    ExtractionType,
    extract_mod_to_extracted_mods_dir,
    fuzzy_find_file_or_dir,
    make_all_files_in_dir_writable,
    safe_copy_dir_to_game_dir,
    tp2_fpath_from_mod_dpath,
)
from .mod_data import (
    get_aliases_by_mod,
    get_mod_name_by_alias,
)
from .mod_index import (
    get_mod_info,
)
from .parsing import (
    UNVERSIONED_MOD_MARKER,
)
from .printing import (
    OPER_CLR,
    fail_print,
    full_line_marker,
    note_print,
    oper_print,
    print_goodbye,
    rprint,
    sccs_print,
)
from .weidu_util import (
    get_mod_info_from_weidu_log,
    update_weidu_conf,
)


class InstallationStatus(Enum):
    """The installation status."""

    SUCCESS = "success"
    WARNINGS = "warnings"
    FAILURE = "failure"


def _get_mod_info_from_installed_mods_info(
    mod_name: str,
    installed_mods_info: dict,
) -> Optional[dict]:
    mod_installation = None
    try:
        mod_installation = installed_mods_info[mod_name]
    except KeyError:
        uniform_mod_name = get_mod_name_by_alias(mod_name)
        if not uniform_mod_name:
            fail_print(
                f"Could not find a uniform name for mod {mod_name}, and so "
                "couldn't find its information in the installed mods info."
            )
            return None
        try:
            mod_installation = installed_mods_info[uniform_mod_name]
        except KeyError:
            mod_aliases = get_aliases_by_mod(uniform_mod_name)
            for alias in mod_aliases:
                try:
                    mod_installation = installed_mods_info[alias]
                    break
                except KeyError:
                    continue
        if not mod_installation:
            fail_print(
                f"Could not find information about {mod_name} in the installed "
                "mods info."
            )
        return mod_installation


def uninstall_mod(
    mod_name: str,
    weidu_exec_path: str,
    game_install_dir: str,
    installed_mods_info: dict,
) -> bool:
    """Uninstall the mod.

    Parameters
    ----------
    mod_name : str
        The name of the mod.
    weidu_exec_path : str
        The path to the WeiDU executable.
    game_install_dir : str
        The directory where the game is installed.
    installed_mods_info : dict
        The information about the installed mods.

    Returns
    -------
    bool
        Whether the mod was uninstalled successfully.

    """
    oper_print(f"Uninstalling {mod_name}...")
    mod_installation = _get_mod_info_from_installed_mods_info(
        mod_name, installed_mods_info
    )
    if not mod_installation:
        fail_print(
            f"Could not find information about {mod_name} in the installed mods "
            "info. Cannot uninstall."
        )
        return False
    tp2_rel_fpath = mod_installation["tp2_rel_fpath"]
    command = [
        f'"{weidu_exec_path}"',
        f'"{tp2_rel_fpath}"',
        "--uninstall",
    ]
    note_print("About to run the following command:")
    note_print(" ".join(command))
    note_print("Please confirm the uninstallation by typing 'y'/'yes'.")
    user_input = input().strip().lower()
    if user_input not in ("y", "yes"):
        fail_print("Uninstallation aborted.")
        return False
    oper_print(">>> Running command:")
    oper_print(" ".join(command))
    proc = subprocess.Popen(
        " ".join(command),
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
        errors="replace",
        shell=True,
        universal_newlines=True,
        cwd=game_install_dir,
    )
    for stdout_line in proc.stdout:
        print(stdout_line, end="")
    proc.stdout.close()
    returncode = proc.wait()

    if returncode == 0:
        sccs_print(f"{mod_name} uninstalled successfully.")
        return True
    else:
        fail_print(f"Uninstallation of {mod_name} failed.")
        return False


def execute_mod_installation(
    mod_name: str,
    run_config: dict,
    weidu_exec_path: str,
    mod_dir_path: str,
    mod_tp2_path: str,
    game_install_dir: str,
    language_int: int,
    install_list: str,
    log_file: str,
    lang: str,
) -> InstallationStatus:
    """Execute installation command and return the result.

    Parameters
    ----------
    mod_name : str
        The name of the mod.
    run_config : dict
        The run configuration.
    weidu_exec_path : str
        The path to the WeiDU executable.
    mod_dir_path : str
        The path to the mod directory.
    mod_tp2_path : str
        The path to the .tp2 file of the mod.
    game_install_dir : str
        The directory where the game is installed.
    language_int : int
        The language integer to set for the installation process, determining
        the language used to describe components and to interact with the
        user.
    install_list : str
        The list of components to install.
    log_file : str
        The path to the log file to write logs to.
    lang : str
        The language directory the mod should operate on. E.g. en_US, etc.

    Returns
    -------
    InstallationStatus
        The installation status.

    """
    os.chmod(weidu_exec_path, 0o755)
    os.chmod(mod_tp2_path, 0o755)
    make_all_files_in_dir_writable(mod_dir_path)
    rel_mod_tp2_path = os.path.relpath(mod_tp2_path, game_install_dir)
    command = [
        f'"{weidu_exec_path}"',
        f'"{rel_mod_tp2_path}"',
        "--no-exit-pause",
        "--game",
        f'"{game_install_dir}"',
        "--log",
        f'"{log_file}"',
        "--language",
        str(language_int),
        "--skip-at-view",
        "--force-install-list",
        install_list,
        "--use-lang",
        lang,
    ]
    oper_print(f"Searching for cmd fixes for mod {mod_name}...")
    cmd_fixes = get_cmd_fixes_for_mod(mod_name)
    if cmd_fixes:
        oper_print(f"Applying cmd fixes for mod {mod_name}...")
        for fix in cmd_fixes:
            command = fix.apply(
                cmd=command,
                jenga_config=CFG,
                run_config=run_config,
            )
            sccs_print(f"Applied {fix.fix_name}.")
    oper_print(">>> Running command:")
    oper_print(" ".join(command))
    proc = subprocess.Popen(
        " ".join(command),
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
        errors="replace",
        shell=True,
        universal_newlines=True,
        cwd=game_install_dir,
    )
    with open(log_file, "ab") as lf:
        for stdout_line in proc.stdout:
            print(stdout_line, end="")
            lf.write(stdout_line.encode("utf-8", errors="replace"))
            # out.write(stdout_line)
    proc.stdout.close()
    returncode = proc.wait()

    # for more on WeiDU return codes, see
    # Section 13.2  "WeiDU Return Values", in the WeiDU readme:
    # https://weidu.org/~thebigg/beta/README-WeiDU.html#sec56
    if returncode == 0:
        return InstallationStatus.SUCCESS
    elif returncode == 3:
        return InstallationStatus.WARNINGS
    else:
        return InstallationStatus.FAILURE


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
    with open(state_file_path, "r", encoding="utf-8") as f:
        build_state = json.load(f)
    return build_state["last_mod_index"] + 1


def write_ongoing_state(
    build_name: str,
    index: int,
    state_file_path: str,
) -> None:
    """Write ongoing builg state to file.

    Parameters
    ----------
    build_name : str
        The name of the build.
    index : int
        The index of the last installed mod.
    state_file_path : str
        The name of the state file.

    """
    state = {"build_name": build_name, "last_mod_index": index}
    with open(state_file_path, "w", encoding="utf-8") as f:
        json.dump(state, f, indent=4)


def find_latest_build_state_file(
    build_name: str,
    game_install_dir: str,
) -> Optional[str]:
    """Find the latest build state file.

    Parameters
    ----------
    build_name : str
        The name of the build.
    game_install_dir : str
        The directory where the game is installed.

    Returns
    -------
    Optional[str]
        The path to the latest build state file.

    """
    # note: state file pattern is jenga_{build_name}_{timestamp}.json
    state_files = [
        file
        for file in os.listdir(game_install_dir)
        if file.startswith(f"jenga_state_{build_name}")
    ]
    if not state_files:
        return None
    state_files.sort()
    return os.path.join(game_install_dir, state_files[-1])


def _convert_components_dicts_list_to_lists_list(
    components_dict: List[Dict[str, str]],
) -> List[Tuple[str, str]]:
    """Convert components dicts list to list of 2-tuples.

    An example components list is:
    [{
        'number': '0',
        'description': "lefreut's Enhanced UI (BG1EE skin) - Core component"
      },
      {
        'number': '1'
       'description': "lefreut's Enhanced UI (BG1EE skin) - BG2 vanilla bams"
      }]
    This function converts it to a list of 2-tuples:
    [('0', "lefreut's Enhanced UI (BG1EE skin) - Core component"),
     ('1', "lefreut's Enhanced UI (BG1EE skin) - BG2 vanilla bams")]

    Parameters
    ----------
    components_dict : List[Dict[str, str]]
        The list of components dicts.

    Returns
    -------
    List[Tuple[str]]
        The list of corresponding 2-tuples.

    """
    return [(c["number"], c["description"]) for c in components_dict]


def mod_is_installed_identically(
    mod_name: str,
    mod_version: str,
    desired_components: List[Dict[str, str]],
    installed_mods_info: Optional[dict] = None,
) -> Tuple[bool, bool]:
    """Check if the mod is installed identically.

    Parameters
    ----------
    mod_name : str
        The name of the mod.
    mod_version : str
        The version of the mod.
    desired_components : list
        The list of installed components.
    installed_mods_info : dict, optional
        The information about the mod installation.
        If not provided, returns False.

    Returns
    -------
    bool
        Whether the mod is installed identically.

    """
    if not installed_mods_info:
        fail_print(
            "Cannot check if mod is installed identically without mod install"
            " information."
        )
        return False, False
    mod_installation = _get_mod_info_from_installed_mods_info(
        mod_name, installed_mods_info
    )
    if not mod_installation:
        fail_print(
            "Cannot check if mod is installed identically without mod install"
            " information."
        )
        return False, False
    oper_print(
        f"Comparing planned {mod_name} installation with version:\n"
        f"{mod_version}\n and components:\n {desired_components}\n"
        f" against install_info:\n {mod_installation}"
    )
    installed_comp_list = _convert_components_dicts_list_to_lists_list(
        mod_installation["components"]
    )
    desired_comp_list = _convert_components_dicts_list_to_lists_list(
        desired_components
    )
    version_match = mod_installation["version"] == mod_version
    if mod_installation["version"] == UNVERSIONED_MOD_MARKER:
        version_match = True
    # name_match = mod_installation["mod"] == mod_name.lower()
    comp_match = set(installed_comp_list) == set(desired_comp_list)
    # print(">>>>>> installed identically debug <<<<<<<<")
    # oper_print(f"name_match: {name_match}")
    oper_print(f"version_match: {version_match}")
    oper_print(f"comp_match: {comp_match}")
    is_installed_identically = version_match and comp_match
    return is_installed_identically, True


def _resolve_game_dir(
    game_install_dir: Optional[str] = None,
    game: Optional[str] = None,
) -> str:
    """Resolve the game directory argument.

    Parameters
    ----------
    game_install_dir : str, optional
        The directory where the game is installed.
    game : str, optional
        The game alias.

    Returns
    -------
    str
        The resolved game directory path. None if resolution fails.

    """
    if game_install_dir is not None:
        return game_install_dir
    # attempt to extract the target game directory from the Jenga config.
    dir_from_conf = get_game_dir(game, CfgKey.TARGET)
    if dir_from_conf is not None:
        return dir_from_conf
    game_dirs = get_all_target_game_dirs()
    if not len(game_dirs) == 1:
        raise ValueError(
            "A path to the target game directory to mod must be provided "
            "explicitly if the game to mod is not configured in the build file"
            ", and there is not exactly one target game directory path "
            "in your Jenga configuration."
        )
    lonely_path = game_dirs[0]
    if not lonely_path:
        raise ValueError(
            "A path to the game directory to mod must be provided."
        )
    return lonely_path


def print_run_config_info_box(runcfg: dict, console: Console) -> None:
    tcolor = OPER_CLR
    table1 = Table()
    table1.add_column(
        "Build Name", justify="center", style=tcolor, no_wrap=True
    )
    table1.add_column("Game", justify="center", style=tcolor, no_wrap=True)
    table1.add_column(
        "Game Install Dir", justify="center", style=tcolor, no_wrap=True
    )
    table1.add_column("Language", justify="center", style=tcolor, no_wrap=True)
    table1.add_column(
        "Force lang in weidu.conf",
        justify="center",
        style=tcolor,
        no_wrap=True,
    )
    table1.add_column(
        "Prefer mod index",
        justify="center",
        style=tcolor,
        no_wrap=True,
    )
    table1.add_column(
        "Prefer zipped mods",
        justify="center",
        style=tcolor,
        no_wrap=True,
    )
    table1.add_row(
        f"{runcfg.get('build_name')}",
        f"{runcfg.get('game')}",
        f"{runcfg.get('game_install_dir')}",
        f"{runcfg.get('lang')}",
        f"{runcfg.get('force_lang_in_weidu_conf')}",
        f"{runcfg.get('prefer_mod_index')}",
        f"{runcfg.get('prefer_zipped_mods')}",
    )

    table2 = Table()
    table2.add_column(
        "Skip Installed Mods", justify="center", style=tcolor, no_wrap=True
    )
    table2.add_column(
        "Pause Every X Mods", justify="center", style=tcolor, no_wrap=True
    )
    table2.add_column(
        "State File Path", justify="center", style=tcolor, no_wrap=True
    )
    table2.add_row(
        f"{runcfg.get('skip_installed_mods')}",
        f"{runcfg.get('pause_every_x_mods')}",
        f"{runcfg.get('state_file_path')}",
    )

    table3 = Table(title="Run Configuration")
    table3.add_column(justify="center", no_wrap=True)
    table3.add_row(table1)
    table3.add_row(table2)
    console.print(table3)
    # console.print(Panel(table3))


def print_mod_info_box(mod: dict, console: Console) -> None:
    """Print the mod information in a rich info box.

    Parameters
    ----------
    mod : dict
        The mod information.
    console : Console
        The rich console object.

    """
    tcolor = OPER_CLR
    table = Table()
    table.add_column("Name", justify="center", style=tcolor, no_wrap=True)
    table.add_column("Version", justify="center", style=tcolor, no_wrap=True)
    table.add_column(
        "Language Int", justify="center", style=tcolor, no_wrap=True
    )
    table.add_column(
        "Install List", justify="center", style=tcolor, no_wrap=True
    )
    table.add_row(
        f"{mod['mod']}",
        f"{mod['version']}",
        f"{mod['language_int']}",
        f"{mod['install_list']}",
    )
    console.print(table)

    table = Table(title="Components List")
    table.add_column("Number", justify="center", style=tcolor, no_wrap=True)
    table.add_column("Description", justify="left", style=tcolor, no_wrap=True)
    for c in mod["components"]:
        table.add_row(f"{c['number']}", f"{c['description']}")
    console.print(table)
    # rprint(Panel(Pretty(omod), title=mod["mod"], style="magenta"))


def run_build(
    build_file_path: str,
    extracted_mods_dir: Optional[str] = None,
    zipped_mods_dir: Optional[str] = None,
    weidu_exec_path: Optional[str] = None,
    game_install_dir: Optional[str] = None,
    state_file_path: Optional[str] = None,
    skip_installed_mods: Optional[bool] = None,
    resume: Optional[bool] = False,
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
        to the directory of the game listed in the provided build file is
        looked for in your Jenga configuration.
    state_file_path : str, optional
        The path to the state file.
    skip_installed_mods : bool, optional
        Whether to skip the installation of already installed mods.
        Default is False.
    resume : bool, optional
        Whether to resume the build from a state file. Default is False.

    """
    full_line_marker()
    oper_print("Starting the build process!")
    oper_print("Reading the build file...")

    # Handling optional arguments
    extracted_mods_dir = extracted_mods_dir or CFG.get(
        CfgKey.EXTRACTED_MOD_CACHE_DIR_PATH
    )
    if not extracted_mods_dir:
        warnings.warn(
            "No extracted mods directory provided or found in the "
            "configuration. The zipped mods directory must be provided.",
            stacklevel=2,
        )
        raise ValueError(
            "A path to an extracted mods directory must be provided."
            "Zipped mod directory support is not implemented yet."
        )
    zipped_mods_dir = zipped_mods_dir or CFG.get(
        CfgKey.ZIPPED_MOD_CACHE_DIR_PATH
    )
    if not zipped_mods_dir and not extracted_mods_dir:
        raise ValueError(
            "A path to neither a zipped mods directory or an extracted mod"
            " directory was provided. At least one must be provided."
            " Program exiting."
        )
    weidu_exec_path = weidu_exec_path or CFG.get(CfgKey.WEIDU_EXEC_PATH)
    if not weidu_exec_path:
        raise ValueError("A path to the WeiDU executable must be provided.")

    # Load the build file
    with open(build_file_path, "r", encoding="utf-8") as f:
        build = json.load(f)
    config = {}
    run_config = {}
    try:
        config = build["config"]
        run_config = build["config"]
    except KeyError as e:
        raise ConfigurationError(
            "The build file must contain a 'config' key."
        ) from e
    game = config.get("game")
    game_install_dir = _resolve_game_dir(game_install_dir, game)
    run_config["game_install_dir"] = game_install_dir
    installed_mods_info = None
    if skip_installed_mods is None:
        skip_installed_mods = config.get("skip_installed_mods")
    run_config["skip_installed_mods"] = skip_installed_mods
    if skip_installed_mods:
        installed_mods_info = get_mod_info_from_weidu_log(game_install_dir)
    build_name = config.get("build_name")
    if build_name is None:
        raise ValueError(
            "The build file must contain a 'build_name' key in the config "
            "section, mapping to a string suitable as a file name component."
        )
    lang = config.get("lang")
    if lang is None:
        lang = CFG.get(CfgKey.DEFAULT_LANG)
        if lang is None:
            raise ConfigurationError(
                "The build file must contain a 'lang' key or the Jenga "
                "configuration must contain a 'DEFAULT_LANG' key."
            )
    run_config["lang"] = lang
    try:
        force_lang_in_weidu_conf = config["force_lang_in_weidu_conf"]
    except KeyError:
        force_lang_in_weidu_conf = False
    run_config["force_lang_in_weidu_conf"] = force_lang_in_weidu_conf
    pause_every_x_mods = config.get("pause_every_x_mods")
    run_config["pause_every_x_mods"] = pause_every_x_mods
    prefer_zipped_mods = config.get("prefer_zipped_mods", False)
    run_config["prefer_zipped_mods"] = prefer_zipped_mods
    prefer_mod_index = config.get("prefer_mod_index", False)
    run_config["prefer_mod_index"] = prefer_mod_index
    try:
        mods = build["mods"]
    except KeyError as e:
        raise ConfigurationError(
            "The build file must contain a 'mods' key."
        ) from e

    console = Console()
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    new_state_file_name = f"jenga_state_{build_name}_{timestamp}.json"
    new_state_file_path = os.path.join(game_install_dir, new_state_file_name)
    run_config["state_file_path"] = new_state_file_path
    # running_on_mac = False
    # if platform.system() == "Darwin":
    #     running_on_mac = True

    note_print("Build configuration:")
    print_run_config_info_box(run_config, console)
    note_print("Tool configuration:")
    print_config_info_box()

    # Handling resuming from a build state file
    if not state_file_path and resume:
        state_file_path = find_latest_build_state_file(
            build_name, game_install_dir
        )
        if not state_file_path:
            raise FileNotFoundError(
                "No state file found in the game directory to resume the build"
                " from. Please provide a path to the state file."
            )
        oper_print(f"Resuming build from state file: {state_file_path}")

    start_index = 0
    if state_file_path:
        if os.path.exists(state_file_path):
            start_index = get_start_index_from_build_state_file(
                state_file_path
            )
        else:
            raise FileNotFoundError(
                f"State file {state_file_path} does not exist."
            )

    for i in range(start_index, len(mods)):
        mod = mods[i]
        print("\n")
        oper_print("Processing mod:")
        print_mod_info_box(mod, console)
        mod_name = mod["mod"]
        language_int = mod["language_int"]
        version = mod["version"]
        components = mod["components"]
        install_list = mod["install_list"]
        prompt_for_manual_install = mod.get("prompt_for_manual_install", False)

        if prompt_for_manual_install:
            user_input = "blah"
            while user_input not in ("m", "manual", "s", "skip", "f", "force"):
                note_print(
                    f"Prompting for manual installation of {mod_name}. "
                    "Type 'm'/'manual' to save build state and "
                    "halt; type 's'/'skip' to skip this mod and continue; "
                    "type 'f'/'force' to attempt to install the mod anyway."
                )
                user_input = input().strip().lower()
                if user_input in ("m", "manual"):
                    oper_print("Halting the process based on user input.")
                    write_ongoing_state(build_name, i, new_state_file_path)
                    sccs_print(f"Build state saved to {new_state_file_path}")
                    print_goodbye()
                    sys.exit(0)
                elif user_input in ("s", "skip"):
                    note_print(f"Skipping {mod_name}...")
                    continue
                elif user_input in ("f", "force"):
                    pass

        is_instld_ident, is_instld = mod_is_installed_identically(
            mod_name, version, components, installed_mods_info
        )
        if skip_installed_mods and is_instld_ident:
            note_print(
                f"{mod_name} is already identically installed. wkipping..."
            )
            continue
        if is_instld and not is_instld_ident:
            note_print(
                f"{mod_name} is already installed, but not identically. "
                "Uninstalling..."
            )
            if installed_mods_info is None:
                fail_print(
                    "Cannot uninstall mod without installed mods information."
                )
                write_ongoing_state(build_name, i - 1, new_state_file_path)
                note_print(f"Build state saved to {new_state_file_path}")
                sys.exit(1)
            uninst_sccs = uninstall_mod(
                mod_name,
                weidu_exec_path,
                game_install_dir,
                installed_mods_info,
            )
            if not uninst_sccs:
                fail_print(
                    f"Failed to uninstall {mod_name}. Terminating the build "
                    "process."
                )
                write_ongoing_state(build_name, i - 1, new_state_file_path)
                note_print(f"Build state saved to {new_state_file_path}")
                sys.exit(1)

        log_file = f'setup-{mod_name.lower().replace(" ", "_")}.debug'

        # Update Weidu.conf with the language if necessary
        if force_lang_in_weidu_conf:
            update_weidu_conf(game_install_dir, lang)

        target_mod_dir = None
        target_tp2_path = None
        # First, we check for the possibility of using the mod index
        from_mod_index = False
        if prefer_mod_index:
            oper_print(
                f"Mod index preferred, so trying to find mod {mod_name} in the"
                " mod index..."
            )
            mod_info = get_mod_info(mod_name.lower())
            if mod_info:
                from_mod_index = True
                mod_dir = mod_info.extracted_dpath
                mod_dir_name = dir_name_from_dir_path(mod_dir)
                target_mod_dir = os.path.join(game_install_dir, mod_dir_name)
                tp2_fpath = mod_info.tp2_fpath
                oper_print(
                    f"Found mod {mod_name} in the mod index:\n" f"{mod_info}\n"
                )
                safe_copy_dir_to_game_dir(mod_dir, target_mod_dir)
                tp2_fname = os.path.basename(tp2_fpath)
                # find tp2 parent dir in extracted mods dir to understand
                # where to copy it to
                tp2_path = Path(tp2_fpath)
                tp2_dpath = tp2_path.parent.absolute()
                tp2_dname = tp2_dpath.name
                if str(tp2_dpath) == extracted_mods_dir:
                    target_tp2_path = os.path.join(game_install_dir, tp2_fname)
                    shutil.copy(tp2_fpath, target_tp2_path)
                    oper_print(
                        f"Copied tp2 file to game directory:\n"
                        f"{target_tp2_path}"
                    )
                elif str(tp2_dpath) == mod_dir:
                    # no need to copy tp2 file, it's already in the mod dir
                    target_tp2_path = os.path.join(target_mod_dir, tp2_fname)
                else:
                    raise IllformedExtractedModDirError(
                        "The tp2 file was found in the an expected location "
                        "in the mod directory or the extracted mods directory."
                    )
                oper_print(
                    "Mod copied to game directory.\n"
                    f"Target mod directory: {target_mod_dir}\n"
                    f"Target tp2 file path: {target_tp2_path}"
                )

        # Find the mod zipped archive, if available and preferred
        from_archive = False
        if prefer_zipped_mods and not from_mod_index:
            mod_dir = None
            target_mod_dir = None
            target_tp2_path = None
            oper_print("Zipped mods preferred, so...")
            if not zipped_mods_dir:
                msg = (
                    "prefer_zipped_mods set to True, but no zipped mods "
                    "directory provided in the configuration. The extracted "
                    "mods directory will be used."
                )
                warnings.warn(msg, stacklevel=2)
                note_print(msg)
            else:
                res = extract_mod_to_extracted_mods_dir(
                    zipped_mods_dir, extracted_mods_dir, mod_name
                )
                oper_print("Extraction results:")
                rprint(res)
                from_archive = True
                mod_dir = res.mod_folder_path
                mod_dir_name = dir_name_from_dir_path(mod_dir)
                target_mod_dir = os.path.join(game_install_dir, mod_dir_name)
                safe_copy_dir_to_game_dir(mod_dir, target_mod_dir)
                ex_type = res.extraction_type
                if ex_type in [ExtractionType.TYPE_A, ExtractionType.TYPE_B]:
                    # in both cases we copy a single mod dir with the all
                    # possible tp2 files insides of it, so guessting the
                    # most appropriate tp2 file from it is enough
                    target_tp2_path = tp2_fpath_from_mod_dpath(
                        target_mod_dir, mod_name
                    )
                elif ex_type == ExtractionType.TYPE_C:
                    # in this case we have a single tp2 file in the root
                    # of the extracted mod dir, so we have to copy it
                    # separately into the game dir (and not the mod dir!)
                    tp2_to_copy = res.tp2_file_path
                    tp2_fanme = os.path.basename(tp2_to_copy)
                    target_tp2_path = os.path.join(game_install_dir, tp2_fanme)
                    shutil.copy(tp2_to_copy, target_tp2_path)
                elif ex_type == ExtractionType.TYPE_E:
                    # here we have more than one mod folders, but also tp2
                    # file/s directly in the unpacked archive itself, so the
                    # unpacked archive was treated as a single mode dir, and
                    # we can guess the tp2 file from it
                    target_tp2_path = tp2_fpath_from_mod_dpath(
                        target_mod_dir, mod_name
                    )
                elif ex_type == ExtractionType.TYPE_D:
                    # here we have more than one mod folder, but no tp2 files
                    # in the root of the unpacked archive, so we have to copy
                    # additional mod folders
                    target_tp2_path = tp2_fpath_from_mod_dpath(
                        target_mod_dir, mod_name
                    )
                    for mod_folder in res.additional_mod_folder_paths:
                        mod_folder_name = dir_name_from_dir_path(mod_folder)
                        target_mod_folder = os.path.join(
                            game_install_dir, mod_folder_name
                        )
                        safe_copy_dir_to_game_dir(
                            mod_folder, target_mod_folder
                        )
                        additional_fpaths = res.additional_file_paths
                        for fpath in additional_fpaths:
                            f_name = os.path.basename(fpath)
                            target_fpath = os.path.join(
                                game_install_dir, f_name
                            )
                            shutil.copy(fpath, target_fpath)

        if not from_mod_index and not from_archive:
            oper_print("No mod index entry found, and no zipped mod found.")
            oper_print(
                "Searching for the mod in the extracted mods directory..."
            )
            # Find the mod directory
            mod_dir = fuzzy_find_file_or_dir(
                extracted_mods_dir, mod_name, dir_search=True
            )
            # Copy the mod directory to the game directory
            target_mod_dir = os.path.join(game_install_dir, mod_name)
            safe_copy_dir_to_game_dir(mod_dir, target_mod_dir)
            # Find .tp2 file inside
            target_tp2_path = fuzzy_find_file_or_dir(
                target_mod_dir, mod_name, setup_file_search=True
            )

        if target_mod_dir is None or target_tp2_path is None:
            fail_print(
                f"Could not find the mod directory or the .tp2 file for "
                f"{mod_name}. Terminating the build process."
            )
            write_ongoing_state(build_name, i - 1, new_state_file_path)
            note_print(f"Build state saved to {new_state_file_path}")
            sys.exit(1)

        # Apply any pre-fixes for the mod
        oper_print(f"Looking for pre-fixes for {mod_name}...")
        pre_fixes = get_prepost_fixes_for_mod(mod_name, prefix=True)
        if pre_fixes:
            oper_print(f"Applying pre-fixes for {mod_name}...")
            for fix in pre_fixes:
                note_print(
                    f"Shoud {fix.fix_name} be applied? Type 'y'/'yes' to"
                    " apply, 't'/'terminate' to terminate build execution, "
                    "or any other key to skip.")
                user_input = input().strip().lower()
                if user_input in ("y", "yes"):
                    fix.apply(
                        mod_dir=target_mod_dir,
                        mod_tp2_path=target_tp2_path,
                        jenga_config=CFG,
                        run_config=run_config,
                    )
                    sccs_print(f"Applied {fix.fix_name}.")
                elif user_input in ("t", "terminate"):
                    note_print(
                        "Terminating the build process on user request.")
                    write_ongoing_state(build_name, i - 1, new_state_file_path)
                    note_print(f"Build state saved to {new_state_file_path}")
                    sys.exit(0)

        oper_print(f"Installing {mod_name}...")
        status = execute_mod_installation(
            mod_name,
            run_config,
            weidu_exec_path,
            target_mod_dir,
            target_tp2_path,
            game_install_dir,
            language_int,
            install_list,
            log_file,
            lang,
        )

        if status == InstallationStatus.FAILURE:
            fail_print(
                "Installation of at least one component of "
                f"[{OPER_CLR}]{mod_name}[/{OPER_CLR}] failed. "
                "Terminating the build process."
            )
            write_ongoing_state(build_name, i - 1, new_state_file_path)
            note_print(f"Build state saved to {new_state_file_path}")
            sys.exit(1)
        elif status == InstallationStatus.WARNINGS:
            note_print(
                f"Installation of [{OPER_CLR}]{mod_name}[/{OPER_CLR}] "
                "completed with warnings. Would you like to continue the build"
                "process? (Enter 'y'/'yes' to continue, any other input to "
                "halt."
            )
            user_input = input().strip().lower()
            if user_input not in ("yes", "y"):
                write_ongoing_state(build_name, i, new_state_file_path)
                note_print(f"Build state saved to {new_state_file_path}")
                sys.exit(1)
        sccs_print(f"{mod_name} installed successfully.")

        # Apply any post-fixes for the mod
        oper_print(f"Looking for post-fixes for {mod_name}...")
        post_fixes = get_prepost_fixes_for_mod(mod_name, prefix=False)
        if post_fixes:
            oper_print(f"Applying post-fixes for {mod_name}...")
            for fix in post_fixes:
                fix.apply(
                    mod_dir=target_mod_dir,
                    mod_tp2_path=target_tp2_path,
                    jenga_config=CFG,
                    run_config=run_config,
                )
                sccs_print(f"Applied {fix.fix_name}.")

        # Pause installation every x mods as required
        if (i + 1) % pause_every_x_mods == 0:
            note_print(
                f"Paused after installing {pause_every_x_mods} "
                "mods. Press Enter or type 'yes'/'y' to continue, or any "
                "other key to halt: "
            )
            user_input = input().strip().lower()
            if user_input not in ("", "yes", "y"):
                oper_print("Halting the process based on user input.")
                write_ongoing_state(build_name, i, new_state_file_path)
                sccs_print(f"Build state saved to {new_state_file_path}")
                print_goodbye()
                sys.exit(0)
