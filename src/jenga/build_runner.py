"""The Jenga build runner."""

# Standard library imports
import os
import json
import subprocess
import sys
from datetime import datetime

# Third-party imports
from fuzzywuzzy import process, fuzz


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
    best_match, score = process.extractOne(
        name.lower(), entries, scorer=fuzz.ratio)
    if score < 50:
        raise FileNotFoundError(
            f"Unable to locate {name}{file_type} with "
            "sufficient accuracy in {directory.}"
        )
    return os.path.join(directory, best_match)


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
    process = subprocess.run(
        command, stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        check=False,
    )
    # Decode the stdout and stderr
    stdout_text = process.stdout.decode('utf-8')
    stderr_text = process.stderr.decode('utf-8')
    # Print stdout and stderr to screen
    print(stdout_text, end='')
    print(stderr_text, end='', file=sys.stderr)
    # Append stdout and stderr to the log file
    with open(log_file, 'ab') as lf:
        lf.write(process.stdout)
        lf.write(process.stderr)
    return process.returncode == 0


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


def run_build(
    build_file_path: str,
    mods_dir: str,
    weidu_exec_path: str,
    game_install_dir: str,
    state_file_path: str = None,
) -> None:
    """Run the build process.

    Parameters
    ----------
    build_file_path : str
        The path to the build file.
    mods_dir : str
        The directory containing the mods.
    weidu_exec_path : str
        The path to the WeiDU executable.
    game_install_dir : str
        The directory where the game is installed.
    state_file_path : str, optional
        The path to the state file.
    """
    # Load the build file
    with open(build_file_path, 'r', encoding='utf-8') as f:
        build = json.load(f)

    build_name = build["config"]["build_name"]
    language = build["config"]["language"]
    force_language_in_weidu_conf = build["config"]["force_language_in_weidu_conf"]
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
        install_list = mod["install_list"]
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
            sys.exit(1)

        # Pause installation every x mods as required
        if (i + 1) % pause_every_x_mods == 0:
            input(f"Paused after installing {pause_every_x_mods} mods. Press Enter to continue...")

if __name__ == "__main__":
    if len(sys.argv) < 5:
        print("Usage: python install_weidu_mods.py <build_file_path> <mods_dir> <weidu_exec_path> <game_install_dir> [<state_file_path>]")
        sys.exit(1)

    build_file_path = sys.argv[1]
    mods_dir = sys.argv[2]
    weidu_exec_path = sys.argv[3]
    game_install_dir = sys.argv[4]
    state_file_path = sys.argv[5] if len(sys.argv) > 5 else None

    main(build_file_path, mods_dir, weidu_exec_path, game_install_dir, state_file_path)
