"""Basic filesystem utility functions for jenga."""

# Standard library imports
import os
import shutil
from typing import List, Optional, Tuple

# Third-party imports
from charset_normalizer import (
    from_path,
    is_binary,
)
from thefuzz import fuzz, process

# local imports
from .printing import jprint


def dir_name_from_dir_path(dir_path: str) -> str:
    """Get the directory name from the directory path.

    Parameters
    ----------
    dir_path : str
        The path to the directory.

    Returns
    -------
    str
        The name of the directory.

    """
    return os.path.basename(os.path.normpath(dir_path))


def robust_read_text_file(path: str) -> str:
    """Read the text file at the given path.

    Parameters
    ----------
    path : str
        The path to the text file.

    Returns
    -------
    str
        The text content of the file.

    """
    if is_binary(path):
        raise ValueError(f"File at {path} is binary.")
    cs_matches = from_path(path)
    if len(cs_matches) == 0:
        raise ValueError(f"Unable to determine encoding for file at {path}.")
    if len(cs_matches) == 1:
        return cs_matches[0].output(encoding="utf-8").decode("utf-8")
    valid_prefixes = ["utf", "ascii", "iso", "ansi"]
    for cs_match in cs_matches:
        encodings = cs_match.could_be_from_charset
        for enc in encodings:
            valid = any(
                enc.lower().startswith(prefix) for prefix in valid_prefixes
            )
            if valid:
                return cs_match.output(encoding="utf-8").decode("utf-8")
    best_match = cs_matches.best()
    if best_match:
        return best_match.output(encoding="utf-8").decode("utf-8")
    raise ValueError(f"Unable to determine encoding for file at {path}.")


def robust_read_lines_from_text_file(path: str) -> List[str]:
    """Read the lines of the text file at the given path.

    Parameters
    ----------
    path : str
        The path to the text file.

    Returns
    -------
    List[str]
        The lines of the text file.

    """
    return robust_read_text_file(path).splitlines()


def mirror_backslashes_in_file(
    path: str,
) -> None:
    r"""Replace every \ in the input text file with an / character.

    Parameters
    ----------
    path : str
        The path to the input text file.

    """
    text = robust_read_text_file(path)
    text = text.replace("\\", "/")
    with open(path, "wt", encoding="utf-8") as file:
        file.write(text)


def check_all_files_in_dir_are_writeable(path: str) -> None:
    for root, dirs, files in os.walk(path):
        # check perms for sub-directories
        for momo in dirs:
            if not os.access(os.path.join(root, momo), os.W_OK):
                jprint(
                    f"[red]Directory {os.path.join(root, momo)} "
                    "is not writable."
                )
        # check perms for files
        for momo in files:
            if not os.access(os.path.join(root, momo), os.W_OK):
                jprint(
                    f"[red]File {os.path.join(root, momo)} is not writable."
                )


def make_all_files_in_dir_writable(path: str) -> None:
    jprint(f"[green]Making all files in {path} writable...")
    os.system(f'sudo chmod 777 "{path}"')
    os.system(f'sudo chmod -R 777 "{path}"')
    # permission = 0o777
    # # Change permissions for the top-level folder
    # os.chmod(path, permission)
    #
    # for root, dirs, files in os.walk(path):
    #     # set perms on sub-directories
    #     for momo in dirs:
    #         os.chmod(os.path.join(root, momo), permission)
    #         # os.chown(os.path.join(root, momo), permission, 20)
    #
    #     # set perms on files
    #     for momo in files:
    #         os.chmod(os.path.join(root, momo), permission)
    #         # os.chown(os.path.join(root, momo), permission, 20)
    check_all_files_in_dir_are_writeable(path)


def merge_dirs(src: str, dest: str) -> None:
    """Merge the source directory into the destination directory.

    Files in the source directory will overwrite files in the destination
    directory.

    Parameters
    ----------
    src : str
        The path to the source directory.
    dest : str
        The path to the destination directory.

    """
    for root, _, files in os.walk(src):
        for file in files:
            src_file = os.path.join(root, file)
            dest_file = os.path.join(dest, os.path.relpath(src_file, src))
            if os.path.exists(dest_file):
                os.remove(dest_file)
            shutil.copy2(src_file, dest_file)


def fuzzy_find(
    directory: str,
    name: str,
    file_types: Optional[List[str]] = None,
) -> Tuple[Optional[str], float]:
    """Fuzzy find the file matching the given name in directory.

    Parameters
    ----------
    directory : str
        The directory to search for the file.
    name : str
        The name of the file to search for.
    file_types : List[str], optional
        The file types to search for. If not provided, allows for all
        file types.

    Returns
    -------
    str
        The path to the best matching file/folder found in the directory.
    score
        The score of the match.

    """
    if file_types is None:
        _is_valid_entry = lambda entry: True
    else:
        kfile_types = file_types

        def _is_valid_entry(entry: str) -> bool:
            lower_entry = entry.lower()
            return any(
                lower_entry.endswith(file_type) for file_type in kfile_types
            )

    entries = [
        entry for entry in os.listdir(directory) if _is_valid_entry(entry)
    ]
    result = process.extractOne(name.lower(), entries, scorer=fuzz.ratio)
    if result is None:
        return None, 0
    best_match: str = result[0]
    score: float = result[1]
    return best_match, score
