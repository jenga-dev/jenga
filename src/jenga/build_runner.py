"""The Jenga build runner."""

# Standard library imports
import json
import os
import shutil
import subprocess
import sys
import warnings
from datetime import datetime
from typing import Dict, List, Optional, Tuple

# Third-party imports
from fuzzywuzzy import fuzz, process
from rich.console import Console
from rich.table import Table

from .config import (
    CFG,
    CfgKey,
    get_all_game_dirs,
    get_game_dir,
    print_config_info_box,
)
from .fixes import (
    get_fixes_for_mod,
)

# Local imports
from .parsing import (
    weidu_log_to_build_dict,
)
from .printing import (
    OPER_CLR,
    fail_print,
    full_line_marker,
    note_print,
    oper_print,
    print_goodbye,
    sccs_print,
)
from .util import (
    ConfigurationError,
    make_all_files_in_dir_writable,
)


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
    oper_print(f"Setting {lang_dir_line} in weidu.conf...")
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


def fuzzy_find(directory: str, name: str, file_type: str = ".tp2") -> str:
    """Fuzzy find the file matching the given name in directory.

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
    result = process.extractOne(name.lower(), entries, scorer=fuzz.ratio)
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
    weidu_log_path = os.path.join(install_dir, "weidu.log")
    res = weidu_log_to_build_dict(weidu_log_path)
    mod_list = res["mods"]
    return {k["mod"]: k for k in mod_list}


def execute_mod_installation(
    weidu_exec_path: str,
    mod_dir_path: str,
    mod_tp2_path: str,
    game_install_dir: str,
    language_int: int,
    install_list: str,
    log_file: str,
    lang: str,
) -> bool:
    """Execute installation command and return success.

    Parameters
    ----------
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
    bool
        Whether the installation was successful.

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
    oper_print(">>> Running command:")
    oper_print(" ".join(command))
    proc = subprocess.Popen(  # nosec - subprocess.Popen is safe
        " ".join(command),
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        shell=True,
        universal_newlines=True,
        cwd=game_install_dir,
    )

    with open(log_file, "ab") as lf:
        for stdout_line in proc.stdout:
            print(stdout_line, end="")
            lf.write(stdout_line.encode("utf-8"))
        for stderr_line in proc.stderr:
            print(stderr_line, end="", file=sys.stderr)
            lf.write(stderr_line.encode("utf-8"))

    proc.wait()
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
) -> bool:
    """Check if the mod is installed identically.

    Parameters
    ----------
    mod_name : str
        The name of the mod.
    mod_version : str
        The version of the mod.
    desired_components : list
        The list of installed components.
    install_info : dict, optional
        The information about the mod installation.
        If not provided, returns False.

    Returns
    -------
    bool
        Whether the mod is installed identically.

    """
    if not installed_mods_info:
        return False
    try:
        mod_installation = installed_mods_info[mod_name]
    except KeyError:
        return False
    # print(
    #     f"Comparing planned {mod_name} installation with version:\n"
    #     f"{mod_version}\n and components:\n {desired_components}\n"
    #     f" against install_info:\n {mod_installation}"
    # )
    installed_comp_list = _convert_components_dicts_list_to_lists_list(
        mod_installation["components"]
    )
    desired_comp_list = _convert_components_dicts_list_to_lists_list(
        desired_components
    )
    return (
        mod_installation["mod"] == mod_name
        and mod_installation["version"] == mod_version
        and set(installed_comp_list) == set(desired_comp_list)
    )


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
    # attempt to extract the game directory from the Jenga config.
    dir_from_conf = get_game_dir(game)
    if dir_from_conf is not None:
        return dir_from_conf
    game_dirs = get_all_game_dirs()
    if not len(game_dirs) == 1:
        raise ValueError(
            "A path to the game directory to mod must be provided "
            "explicitly if the game to mod is not configured in the build file"
            ", and there is not exactly one game directory path "
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
    table1.add_row(
        f"{runcfg.get('build_name')}",
        f"{runcfg.get('game')}",
        f"{runcfg.get('game_install_dir')}",
        f"{runcfg.get('lang')}",
        f"{runcfg.get('force_lang_in_weidu_conf')}",
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

    table3 = Table(title="Run Configuraiton")
    table3.add_column(justify="center", no_wrap=True)
    table3.add_row(table1)
    table3.add_row(table2)
    console.print(table3)
    # console.print(Panel(table3))


def print_mod_info_box(mod: dict, console: Console) -> None:
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
    # rprint(Panel(Pretty(mod), title=mod["mod"], style="magenta"))


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

        if skip_installed_mods and mod_is_installed_identically(
            mod_name, version, components, installed_mods_info
        ):
            note_print(
                f"{mod_name} is already identically installed, " "skipping..."
            )
            continue
        log_file = f'setup-{mod_name.lower().replace(" ", "_")}.debug'

        # Update Weidu.conf with the language if necessary
        if force_lang_in_weidu_conf:
            update_weidu_conf(game_install_dir, lang)

        # Find the mod directory
        mod_dir = fuzzy_find(extracted_mods_dir, mod_name, "")
        # Copy the mod directory to the game directory
        target_mod_dir = os.path.join(game_install_dir, mod_name)
        make_all_files_in_dir_writable(target_mod_dir)
        if os.path.exists(target_mod_dir):
            shutil.rmtree(target_mod_dir)
        oper_print(f"Copying {mod_dir} to {target_mod_dir}...")
        shutil.copytree(mod_dir, target_mod_dir)
        make_all_files_in_dir_writable(target_mod_dir)
        # Find .tp2 file inside
        mod_tp2_path = fuzzy_find(target_mod_dir, mod_name, ".tp2")

        # Apply any pre-fixes for the mod
        oper_print(f"Looking for pre-fixes for {mod_name}...")
        pre_fixes = get_fixes_for_mod(mod_name, prefix=True)
        if pre_fixes:
            oper_print(f"Applying pre-fixes for {mod_name}...")
            for fix in pre_fixes:
                fix.apply(
                    mod_dir=target_mod_dir,
                    mod_tp2_path=mod_tp2_path,
                    jenga_config=CFG,
                    run_config=run_config,
                )
                sccs_print(f"Applied {fix.fix_name}.")

        oper_print(f"Installing {mod_name}...")
        success = execute_mod_installation(
            weidu_exec_path,
            target_mod_dir,
            mod_tp2_path,
            game_install_dir,
            language_int,
            install_list,
            log_file,
            lang,
        )

        if not success:
            fail_print(
                f"Installation of [{OPER_CLR}]{mod_name}[/{OPER_CLR}] failed"
                ", terminating the build process."
            )
            write_ongoing_state(build_name, i, new_state_file_path)
            note_print(f"Build state saved to {new_state_file_path}")
            sys.exit(1)
        sccs_print(f"{mod_name} installed successfully.")

        # Apply any post-fixes for the mod
        oper_print(f"Looking for post-fixes for {mod_name}...")
        post_fixes = get_fixes_for_mod(mod_name, prefix=False)
        if post_fixes:
            oper_print(f"Applying post-fixes for {mod_name}...")
            for fix in post_fixes:
                fix.apply(
                    mod_dir=target_mod_dir,
                    mod_tp2_path=mod_tp2_path,
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
