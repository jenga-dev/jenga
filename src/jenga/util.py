"""Utility functions for jenga."""

# Standard library imports
import os
import shutil
import tempfile
from dataclasses import dataclass
from enum import Enum
from typing import List, Optional, Tuple

# Third-party imports
import patoolib
from thefuzz import fuzz, process

from .errors import (
    IllformedModArchiveError,
)
from .fixes import (
    MOD_TO_ALIAS_LIST_REGISTRY,
)

# local imports
from .printing import (
    jprint,
    note_print,
    oper_print,
)


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


def fuzzy_find(
    directory: str,
    name: str,
    file_types: Optional[List[str]] = None,
    setup_file_search: Optional[bool] = False,
) -> str:
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
    setup_file_search : bool, optional
        Whether to search for possibly setup- prefixed files. Default is False.

    Returns
    -------
    str
        The path to the file found in the directory.

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
        if file_types:
            ftstr = "/".join(file_types)
            raise FileNotFoundError(
                f"Unable to locate {name}.{ftstr} in {directory}."
            )
        raise FileNotFoundError(f"Unable to locate {name}.* in {directory}.")
    best_match, score = result
    if score < 30:
        if name.lower() in MOD_TO_ALIAS_LIST_REGISTRY:
            for alias in MOD_TO_ALIAS_LIST_REGISTRY[name.lower()]:
                if alias != name.lower():
                    return fuzzy_find(
                        directory, alias, file_types, setup_file_search
                    )
        if setup_file_search and not name.startswith("setup-"):
            setup_prefixed = f"setup-{name.lower()}"
            return fuzzy_find(directory, setup_prefixed, file_types, True)
        # try with mac- prefix for archives and folders:
        if (
            not setup_file_search
            and not name.startswith("mac-")
            and (not name.startswith("osx-"))
        ):
            mac_prefixed = f"mac-{name.lower()}"
            return fuzzy_find(directory, mac_prefixed, file_types, False)
        # try with the osx- prefix for archives and folders:
        if (
            not setup_file_search
            and not name.startswith("osx-")
            and (not name.startswith("mac-"))
        ):
            osx_prefixed = f"osx-{name.lower()}"
            return fuzzy_find(directory, osx_prefixed, file_types, False)
        if setup_file_search:
            note_print(
                f"Unable to locate {name}.tp2 in {directory} with "
                "sufficient accuracy. Returning best match: {best_match}."
            )
            return os.path.join(directory, best_match)
        if file_types:
            ftstr = "/".join(file_types)
            raise FileNotFoundError(
                f"Unable to locate {name}{ftstr} in {directory} with "
                f"sufficient accuracy. Returning best match: {best_match}."
            )
        raise FileNotFoundError(
            f"Unable to locate {name}.* in {directory} with sufficient "
            "accuracy."
        )
    return os.path.join(directory, best_match)


class ExtractionType(Enum):
    TYPE_A = 1  # Single mod folder with .tp2 file inside
    TYPE_B = 2  # One or more .tp2 file, no folders in the archive
    TYPE_C = 3  # One mod folder, no .tp2 file inside; tp2 file/s next to it
    TYPE_D = 4  # Multiple mod folders, each containing a .tp2 file
    TYPE_E = 5  # Multiple mod folders; tp2 file/s next to them


@dataclass
class ExtractionResult:
    extraction_type: ExtractionType
    mod_folder_path: str
    tp2_file_path: str
    additional_mod_folder_paths: List[str]
    additional_tp2_file_paths: List[str]


def _get_tp2_fpaths(
    mod_temp_dpath: str, mod_dpath: str, mod_name: str, tp2_fnames: List[str]
) -> Tuple[str, str, List[str], List[str]]:
    """Guess the main .tp2 file paths from the mod folder.

    Parameters
    ----------
    mod_temp_dpath : str
        The path to the temporary directory containing the mod.
    mod_dpath : str
        The path to the directory that will contain the mod.
    mod_name : str
        The name of the mod.
    tp2_fnames : List[str]
        A list of all .tp2 file names in the mod folder.

    Returns
    -------
    Tuple[str, str, List[str], List[str]]
        A tuple containing the temporary and final .tp2 file paths.

    """
    # select the most closely named .tp2 file in the primary mod folder
    mod_tp2_fnames = [
        f for f in os.listdir(mod_temp_dpath) if f.lower().endswith(".tp2")
    ]
    res = process.extractOne(mod_name, mod_tp2_fnames)
    if res is not None:
        tp2_temp_fpath = os.path.join(mod_temp_dpath, res[0])
        tp2_fpath = os.path.join(mod_dpath, res[0])
    else:
        tp2_temp_fpath = os.path.join(mod_temp_dpath, mod_tp2_fnames[0])
        tp2_fpath = os.path.join(mod_dpath, mod_tp2_fnames[0])
    additional_tp2_temp_fpaths = [
        os.path.join(mod_temp_dpath, f) for f in tp2_fnames
    ]
    additional_tp2_fpaths = [os.path.join(mod_dpath, f) for f in tp2_fnames]
    additional_tp2_temp_fpaths.remove(tp2_temp_fpath)
    additional_tp2_fpaths.remove(tp2_fpath)
    return (
        tp2_temp_fpath,
        tp2_fpath,
        additional_tp2_temp_fpaths,
        additional_tp2_fpaths,
    )


def extract_mod_to_extracted_mods_dir(
    zipped_mods_dpath: str, extracted_mods_dir_path: str, mod_name: str
) -> ExtractionResult:
    """Extract a mod to the extracted mods directory.

    Parameters
    ----------
    zipped_mods_dpath : str
        The path to the directory containing the zipped mods.
    extracted_mods_dir_path : str
        The path to the directory containing the extracted mods.
    mod_name : str
        The name of the mod to extract.

    Returns
    -------
    ExtractionResult
        A dataclass containing the extraction result.

    Explanation

    This function does the following:
    1. Searches mods_archives_dir_path for the archive (zip, tar.gz, rar,
    etc.) most closely named like mod_name (e.g.
    find osx-item_rev-v4b10.tar.gz for mod_name = "ITEM_REV") using thefuzz.
    2. Searches extracted_mods_dir_path for the folder most closely named
    like mod_name.
    3. Prompt the user for permission to delete this folder. If answers 'y' or
    'yes', delete it.
    4. Extract the archive (e.g. using patool), to a temp dir (get path w/
    tempfile.mkdtemp).
    5. E.g. osx-item_rev-v4b10.tar.gz extracted into
    '/var/folders/2q/tmpj1p/osx-item_rev-v4b10', which is the unarchived dir.
    There are 4 types of mod structures:
    (A) Most common. The unarchived dir contains a single mod folder, very
    closely named to mod_name, and few files we don't need (README.md,
    .command, .exe file, etc). In this case verify the mod folder contains a
    .tp2 file, and copy only the mod folder to extracted mods folder.
    (B) The unarchived dir contains just a .tp2 file, no folders. In this case,
    copy the unarchived dir itself to the extracted mods folder.
    (C) The unarchived dir contains a single mod folder (without a .tp2 file
    inside it) and a .tp2 file next to it. In this case, copy the mod folder
    and the .tp2 file into the extracted mods dir. (D) The unarchived dir
    contains several folders, each a sub-mod (e.g., for EET,  the folders EET,
    EET_END & EET_GUI), each containing a .tp2 file. In this case, copy each
    folder in the unarchived dir that contains a .tp2 file into the extracted
    mods dir.
    6. Delete the unarchived dir from the unique temp folder we got from the
    OS.
    7. Return a complex return object (perhaps defined using a dataclass) that
    contains both an enum detailing which of the above case was encountered,
    and the path to the newly created mod folder in the extracted mods dir,
    the path to the .tp2 file, and a list of any additional newly created mod
    folders (for case D). In case D, the path to the mod folder named most
    closely resembling the mod name is chosen as the main path returned, and

    """
    # Step 1: Find the best match for the mod archive using fuzzy matching
    oper_print(
        f"Looking for zipped archive for {mod_name} in "
        "{zipped_mods_dpath}..."
    )
    archive_fpath = fuzzy_find(
        zipped_mods_dpath, mod_name, [".zip", "tar.gz", "rar"]
    )
    archive_fname = os.path.basename(archive_fpath)
    oper_print(f"Best match for archive of mod '{mod_name}': {archive_fname}")
    # remove extention from the archive name
    archive_fname_no_ext = os.path.splitext(archive_fname)[0]

    # Step 2: Search for an existing mod folder
    extracted_mods = os.listdir(extracted_mods_dir_path)
    res = process.extractOne(mod_name, extracted_mods)
    if res is None:
        raise FileNotFoundError(
            f"Unable to locate existing mod folder for mod '{mod_name}'"
        )
    best_folder_match = res[0]
    existing_mod_folder_path = os.path.join(
        extracted_mods_dir_path, best_folder_match
    )

    # Step 3: Prompt user for deletion
    if os.path.exists(existing_mod_folder_path):
        response = input(
            f"Delete existing mod folder '{best_folder_match}'? (y/n): "
        )
        if response.lower() in ["y", "yes"]:
            shutil.rmtree(existing_mod_folder_path)

    # Step 4: Extract the archive
    temp_dir = tempfile.mkdtemp()
    patoolib.extract_archive(archive_fpath, outdir=temp_dir)

    # Step 5: Identify mod structure and handle accordingly
    files_and_folders_in_temp = os.listdir(temp_dir)
    if len(files_and_folders_in_temp) == 1:
        kname = files_and_folders_in_temp[0]
        kpath = os.path.join(temp_dir, kname)
        if os.path.isdir(kpath):
            # we have a single folder in the temp dir
            unarchived_dpath = kpath
        else:
            unarchived_dpath = temp_dir
    else:
        unarchived_dpath = temp_dir
    archive_file_and_dir_names = os.listdir(unarchived_dpath)
    archive_tp2_fnames = [
        f for f in archive_file_and_dir_names if f.endswith(".tp2")
    ]
    archive_dnames = [
        f
        for f in archive_file_and_dir_names
        if os.path.isdir(os.path.join(unarchived_dpath, f))
    ]
    mod_structure_type = None
    primary_mod_temp_dpath = ""
    primary_mod_dpath = ""
    tp2_temp_fpath = ""
    tp2_fpath = ""
    additional_mod_temp_dpaths = []
    additional_mod_dpaths = []
    additional_tp2_temp_fpaths = []
    additional_tp2_fpaths = []

    if len(archive_dnames) == 1:
        # we have a single folder in the archive...
        mod_dname = archive_dnames[0]
        mod_dpath = os.path.join(unarchived_dpath, mod_dname)
        tp2_fnames = [
            f for f in os.listdir(mod_dpath) if f.lower().endswith(".tp2")
        ]
        if len(tp2_fnames) > 0:
            # ... and it contains at least one .tp2 file!
            mod_structure_type = ExtractionType.TYPE_A
            primary_mod_temp_dpath = mod_dpath
            primary_mod_dpath = os.path.join(
                extracted_mods_dir_path, mod_dname
            )
            res = _get_tp2_fpaths(
                primary_mod_temp_dpath, primary_mod_dpath, mod_name, tp2_fnames
            )
            tp2_temp_fpath, tp2_fpath = res[:2]
            additional_tp2_temp_fpaths = res[2]
            additional_tp2_fpaths = res[3]
        else:
            # ... but no .tp2 files inside it.
            if len(archive_tp2_fnames) > 0:
                # ... however, there are .tp2 files directly in the unarchived
                # dir!
                mod_structure_type = ExtractionType.TYPE_C
                primary_mod_temp_dpath = mod_dpath
                primary_mod_dpath = os.path.join(
                    extracted_mods_dir_path, mod_dname
                )
                res = _get_tp2_fpaths(
                    unarchived_dpath,
                    extracted_mods_dir_path,
                    mod_name,
                    archive_tp2_fnames,
                )
                tp2_temp_fpath, tp2_fpath = res[:2]
                additional_tp2_temp_fpaths = res[2]
                additional_tp2_fpaths = res[3]
            else:
                # no .tp2 files in the unarchived dir either :(
                raise IllformedModArchiveError(
                    "Unable to locate .tp2 file in unarchived mod folder "
                    f"'{unarchived_dpath}'"
                )
    elif len(archive_dnames) == 0:
        # we have no folders in the archive...
        if len(archive_tp2_fnames) > 0:
            # ... but there are .tp2 files directly in the unarchived dir!
            mod_structure_type = ExtractionType.TYPE_B
            primary_mod_temp_dpath = unarchived_dpath
            primary_mod_dpath = os.path.join(
                extracted_mods_dir_path, archive_fname_no_ext
            )
            res = _get_tp2_fpaths(
                unarchived_dpath,
                primary_mod_dpath,
                mod_name,
                archive_tp2_fnames,
            )
            tp2_temp_fpath, tp2_fpath = res[:2]
            additional_tp2_temp_fpaths = res[2]
            additional_tp2_fpaths = res[3]
        else:
            # ... and no .tp2 files directly in the unarchived dir :(
            raise IllformedModArchiveError(
                "Unable to locate any folders or .tp2 files in unarchived "
                f"mod archive '{unarchived_dpath}'"
            )
    else:
        # we have more than one folder in the archive...
        if len(archive_tp2_fnames) > 0:
            # ... but also tp2 files directly in the unarchived dir!
            mod_structure_type = ExtractionType.TYPE_E
            primary_mod_temp_dpath = unarchived_dpath
            primary_mod_dpath = os.path.join(
                extracted_mods_dir_path, archive_fname_no_ext
            )
            res = _get_tp2_fpaths(
                unarchived_dpath,
                primary_mod_dpath,
                mod_name,
                archive_tp2_fnames,
            )
            tp2_temp_fpath, tp2_fpath = res[:2]
            additional_tp2_temp_fpaths = res[2]
            additional_tp2_fpaths = res[3]
        else:
            # ... and no tp2 files directly in the unarchived dir
            mod_structure_type = ExtractionType.TYPE_D
            mod_folder_candidates = [
                f
                for f in archive_dnames
                if any(
                    f.endswith(".tp2")
                    for f in os.listdir(os.path.join(unarchived_dpath, f))
                )
            ]
            if len(mod_folder_candidates) == 0:
                # and also no .tp2 files in any of the folders :(
                raise IllformedModArchiveError(
                    "Unable to locate any mod folders with .tp2 files in "
                    f"unarchived mod archive '{unarchived_dpath}'"
                )
            # out of all folders containing a tp2 file, pick the folder most
            # closely named to mod_name as the primary mod
            res = process.extractOne(mod_name, mod_folder_candidates)
            if res is None:
                primary_mod_dname = mod_folder_candidates.pop(0)
                additional_mod_dnames = [
                    f for f in archive_dnames if f != primary_mod_dname
                ]
            else:
                primary_mod_dname = res[0]
                additional_mod_dnames = [
                    f for f in archive_dnames if f != primary_mod_dname
                ]
            primary_mod_temp_dpath = os.path.join(
                unarchived_dpath, primary_mod_dname
            )
            primary_mod_dpath = os.path.join(
                extracted_mods_dir_path, primary_mod_dname
            )
            additional_mod_temp_dpaths = [
                os.path.join(unarchived_dpath, f)
                for f in additional_mod_dnames
            ]
            additional_mod_dpaths = [
                os.path.join(extracted_mods_dir_path, f)
                for f in additional_mod_dnames
            ]
            # select the most closely named .tp2 file in the primary mod folder
            tp2_fnames = [
                f
                for f in os.listdir(primary_mod_temp_dpath)
                if f.endswith(".tp2")
            ]
            res = _get_tp2_fpaths(
                primary_mod_temp_dpath, primary_mod_dpath, mod_name, tp2_fnames
            )
            tp2_temp_fpath, tp2_fpath = res[:2]
            additional_tp2_temp_fpaths = res[2]
            additional_tp2_fpaths = res[3]

    # Step 6: Move to extracted_mods_dir_path
    # 6.1: Copy the primary mod folder
    if os.path.exists(primary_mod_dpath):
        make_all_files_in_dir_writable(primary_mod_dpath)
        shutil.rmtree(primary_mod_dpath)
    shutil.copytree(primary_mod_temp_dpath, primary_mod_dpath)
    # 6.2: Copy additional mod folders
    for temp_dpath, dpath in zip(
        additional_mod_temp_dpaths, additional_mod_dpaths
    ):
        if os.path.exists(dpath):
            make_all_files_in_dir_writable(dpath)
            shutil.rmtree(dpath)
        shutil.copytree(temp_dpath, dpath)
    # 6.3: Copy the main .tp2 file
    if os.path.exists(tp2_fpath):
        os.remove(tp2_fpath)
    shutil.copy(tp2_temp_fpath, tp2_fpath)
    # 6.4: Copy additional .tp2 files
    for temp_fpath, fpath in zip(
        additional_tp2_temp_fpaths, additional_tp2_fpaths
    ):
        if os.path.exists(fpath):
            os.remove(fpath)
        shutil.copy(temp_fpath, fpath)

    # Step 7: Clean up temporary directory
    shutil.rmtree(temp_dir)

    return ExtractionResult(
        extraction_type=mod_structure_type,
        mod_folder_path=primary_mod_dpath,
        tp2_file_path=tp2_fpath,
        additional_mod_folder_paths=additional_mod_dpaths,
        additional_tp2_file_paths=additional_tp2_fpaths,
    )


def safe_copy_dir_to_game_dir(mod_dir: str, target_mod_dir: str) -> None:
    """Copy the mod directory to the game directory.

    Parameters
    ----------
    mod_dir : str
        The path to the mod directory.
    target_mod_dir : str
        The path to the target mod directory.

    """
    oper_print(f"Copying {mod_dir} to {target_mod_dir}...")
    if os.path.exists(target_mod_dir):
        make_all_files_in_dir_writable(target_mod_dir)
        shutil.rmtree(target_mod_dir)
        oper_print(f"Deleted existing mod directory '{target_mod_dir}'.")
    shutil.copytree(mod_dir, target_mod_dir)
    make_all_files_in_dir_writable(target_mod_dir)
    oper_print(f"Mod copied to '{target_mod_dir}'.")


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


def tp2_fpath_from_mod_dpath(mod_dpath: str, mod_name: str) -> str:
    """Get the path to the best matching .tp2 file from the mod directory path.

    Parameters
    ----------
    mod_dpath : str
        The path to the mod directory.
    mod_name : str
        The name of the mod.

    Returns
    -------
    str
        The path to the best matching .tp2 file.

    """
    return fuzzy_find(mod_dpath, mod_name, [".tp2"], setup_file_search=True)
