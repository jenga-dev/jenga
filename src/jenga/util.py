"""Utility functions for jenga."""

# Standard library imports
import os

# local imports
from .printing import jprint


class ConfigurationError(Exception):
    """Configuration error."""

    pass


def mirror_backslashes_in_file(
    path: str,
) -> None:
    r"""Replace every \ in the input text file with an / character.

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
    print(f"Making all files in {path} writable...")
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
