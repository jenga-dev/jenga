"""Utility functions for jenga."""

# Standard library imports
import json
import os
import shutil
import tempfile
from dataclasses import dataclass
from enum import Enum
from typing import Callable, Dict, List, Optional, Tuple

# Third-party imports
import patoolib
from thefuzz import fuzz, process

# local imports
from .config import (
    CfgKey,
    demand_extracted_mod_cache_dir_path,
    demand_game_dir_path,
    demand_zipped_mod_cache_dir_path,
    get_game_dir,
)
from .errors import (
    IllformedModArchiveError,
)
from .fs_basics import (
    fuzzy_find,
    make_all_files_in_dir_writable,
)
from .mod_data import (
    JENGA_HINT_FNAME,
    MOD_TO_ALIAS_LIST_REGISTRY,
    JengaHintKey,
)
from .printing import (
    note_print,
    oper_print,
    sccs_print,
)


def fuzzy_find_file_or_dir(
    directory: str,
    name: str,
    setup_file_search: Optional[bool] = False,
    archive_search: Optional[bool] = False,
    dir_search: Optional[bool] = False,
) -> str:
    """Fuzzy find the file matching the given name in directory.

    Parameters
    ----------
    directory : str
        The directory to search for the file.
    name : str
        The name of the file to search for.
    setup_file_search : bool, optional
        Whether to search for possibly setup- prefixed files. Default is False.
    archive_search : bool, optional
        Whether to search for archives. Default is False.
    dir_search : bool, optional
        Whether to search for directories. Default is False.

    Returns
    -------
    str
        The path to the file found in the directory.

    """
    if len(name) > 5:
        fnfs = os.listdir(directory)
        candidates = []
        for fof in fnfs:
            if name.lower() in fof.lower():
                candidates.append(fof)
        if len(candidates) == 1:
            if setup_file_search:
                if candidates[0].endswith(".tp2"):
                    return os.path.join(directory, candidates[0])
            if archive_search:
                if candidates[0].endswith((".zip", ".tar.gz", ".rar")):
                    return os.path.join(directory, candidates[0])
        low_candidates = [cand.lower() for cand in candidates]
        if setup_file_search:
            low_candidates = [
                cand for cand in low_candidates if cand.endswith(".tp2")
            ]
        elif archive_search:
            low_candidates = [
                cand
                for cand in low_candidates
                if cand.endswith((".zip", ".tar.gz", ".rar"))
            ]
        result = process.extractOne(
            name.lower(), low_candidates, scorer=fuzz.ratio
        )
        if result is not None:
            best_match = candidates[low_candidates.index(result[0])]
            best_score = result[1]
            if best_score > 30:
                return os.path.join(directory, best_match)

    search_aliases = [name]
    if name.lower() in MOD_TO_ALIAS_LIST_REGISTRY:
        search_aliases = MOD_TO_ALIAS_LIST_REGISTRY[name.lower()]
    if archive_search:
        file_types = [".zip", ".tar.gz", ".rar"]
        saliases = search_aliases.copy()
        search_aliases.clear()
        for alias in saliases:
            search_aliases.append(alias)
            search_aliases.append(f"osx-{alias}")
            search_aliases.append(f"mac-{alias}")
    elif setup_file_search:
        file_types = [".tp2"]
        saliases = search_aliases.copy()
        search_aliases.clear()
        for alias in saliases:
            search_aliases.append(alias)
            search_aliases.append(f"setup-{alias}")
    else:
        file_types = None
    if archive_search or dir_search:
        # sort so longest names are searched first
        search_aliases.sort(key=len, reverse=True)
    else:
        # sort so shortest names are searched first
        search_aliases.sort(key=len)
    results_and_scores = []
    for alias in search_aliases:
        best_match, score = fuzzy_find(directory, alias, file_types)
        results_and_scores.append((best_match, score))
    results_and_scores.sort(key=lambda x: x[1], reverse=True)
    if setup_file_search:
        results_and_scores = [
            res for res in results_and_scores if res[0].endswith(".tp2")
        ]
    elif archive_search:
        results_and_scores = [
            res
            for res in results_and_scores
            if res[0].endswith((".zip", ".tar.gz", ".rar"))
        ]
    print(results_and_scores)
    best_match = results_and_scores[0][0]
    best_score = results_and_scores[0][1]
    if best_match is not None and best_score > 30:
        return os.path.join(directory, best_match)
    raise FileNotFoundError(f"Unable to locate {name}.* in {directory}.")


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
    return fuzzy_find_file_or_dir(mod_dpath, mod_name, setup_file_search=True)


class ExtractionType(Enum):
    def __str__(self):
        if self == ExtractionType.TYPE_A:
            return (
                "<ExtractionType.TYPE_A: Single mod folder with .tp2 file "
                "inside>"
            )
        if self == ExtractionType.TYPE_B:
            return (
                "<ExtractionType.TYPE_B: One or more .tp2 file, no folders in"
                " the archive>"
            )
        if self == ExtractionType.TYPE_C:
            return (
                "<ExtractionType.TYPE_C: One mod folder, no .tp2 file inside;"
                " tp2 file/s next to it>"
            )
        if self == ExtractionType.TYPE_D:
            return (
                "<ExtractionType.TYPE_D: Multiple mod folders, each "
                "containing a .tp2 file>"
            )
        if self == ExtractionType.TYPE_E:
            return (
                "<ExtractionType.TYPE_E: Multiple mod folders; tp2 file/s "
                "next to them>"
            )
        return self.name

    def __repr__(self):
        return str(self)

    TYPE_A = 1  # Single mod folder with .tp2 file inside
    TYPE_B = 2  # One or more .tp2 file, no folders in the archive
    TYPE_C = 3  # One mod folder, no .tp2 file inside; tp2 file/s next to it
    TYPE_D = 4  # Multiple mod folders, each containing a .tp2 file
    TYPE_E = 5  # Multiple mod folders; tp2 file/s next to them


@dataclass
class ExtractionResult:
    """Dataclass for the result of an extraction operation."""

    extraction_type: ExtractionType
    mod_folder_path: str
    tp2_file_path: str
    additional_mod_folder_paths: List[str]
    additional_tp2_file_paths: List[str]
    additional_file_paths: List[str]


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


def get_tp2_names_and_paths(
    dir_path: str,
    verbose: Optional[bool] = False,
) -> Dict[str, str]:
    """Get names and paths of all .tp2 files in a directory and subdirectories.

    Parameters
    ----------
    dir_path : str
        The path to the directory.
    verbose : bool, optional
        Whether to print verbose output. Default is False.

    Returns
    -------
    Dict[str, str]
        A dictionary containing the names and paths of all .tp2 files.

    """
    _print = lambda x: print(x) if verbose else None
    _print(f"Traversal starting at '{dir_path}'...")
    mod_tp2_fnames = {}
    for root, _, files in os.walk(dir_path):
        for f in files:
            _print(f)
            if f.lower().endswith(".tp2"):
                fname = os.path.splitext(f)[0]
                mod_tp2_fnames[fname] = os.path.join(root, f)
    return mod_tp2_fnames


_ARCHIVE_MOD_DIR_MAPPERS = {
    "sr_revised": {
        "spell_rev": "sr_revised",
    },
    "ir_revised": {
        "item_rev": "ir_revised",
    },
}


def _get_archive_mod_dir_name_mappers(
    archive_fname_no_ext: str,
) -> Optional[Dict[str, str]]:
    """Get the archive mod directory name mappers."""
    for key in _ARCHIVE_MOD_DIR_MAPPERS:
        if key in archive_fname_no_ext.lower():
            return _ARCHIVE_MOD_DIR_MAPPERS[key]


def _map_mod_dir_path(
    mod_dpath: str,
    dname_mappers: Dict[str, str],
) -> str:
    """Map the mod directory path to the target game directory path."""
    mod_parent_dpath = os.path.dirname(mod_dpath)
    mod_dname = os.path.basename(mod_dpath)
    if mod_dname in dname_mappers:
        mod_dname = dname_mappers[mod_dname]
    return os.path.join(mod_parent_dpath, mod_dname)


def extract_archive_to_extracted_mods_dir(
    archive_fpath: str,
    extracted_mods_dir_path: str,
    mod_name: Optional[str] = None,
    verbose: Optional[bool] = False,
) -> ExtractionResult:
    """Extract an archive to the extracted mods directory.

    Parameters
    ----------
    archive_fpath : str
        The path to the archive.
    extracted_mods_dir_path : str
        The path to the directory containing the extracted mods.
    mod_name : str, optional
        The name of the mod to extract. If not provided, the name will be
        guessed from the archive contents.
    verbose : bool, optional
        Whether to print verbose output. Default is False.

    Returns
    -------
    ExtractionResult
        A dataclass containing the extraction result.

    """
    # remove extention from the archive name
    archive_fname = os.path.basename(archive_fpath)
    archive_fname_no_ext = os.path.splitext(archive_fname)[0]

    # Step 4: Extract the archive
    temp_dir = tempfile.mkdtemp()
    patoolib.extract_archive(archive_fpath, outdir=temp_dir)

    # Step 4.5: Guess the mod name if not provided
    # recursively find all .tp2 files in the extracted archive
    if mod_name is None:
        mod_tp2_fnames = list(get_tp2_names_and_paths(temp_dir).keys())
        if len(mod_tp2_fnames) == 0:
            raise IllformedModArchiveError(
                "Unable to locate .tp2 file in unarchived mod archive "
                f"'{temp_dir}'"
            )
        if len(mod_tp2_fnames) == 1:
            mod_name = os.path.splitext(mod_tp2_fnames[0])[0]
        else:
            # infer mod name from the shortest .tp2 file name
            min_name = min(mod_tp2_fnames, key=len)
            if min_name is None:
                raise IllformedModArchiveError(
                    "Unable to infer mod name from .tp2 files in unarchived "
                    f"mod archive '{temp_dir}'"
                )
            mod_name = os.path.splitext(min_name)[0]
    if mod_name is None:
        raise IllformedModArchiveError(
            "Unable to infer mod name from .tp2 file in unarchived "
            f"mod archive '{temp_dir}'"
        )

    # Step 5: Identify mod structure and handle accordingly
    files_and_folders_in_temp = os.listdir(temp_dir)
    files_and_folders_in_temp = [
        f for f in files_and_folders_in_temp if f != "__MACOSX"
    ]
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
    archive_command_fnames = [
        f for f in archive_file_and_dir_names if f.endswith(".command")
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
    additional_temp_fpaths = []
    additional_fpaths = []

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
                    f for f in mod_folder_candidates if f != primary_mod_dname
                ]
            else:
                primary_mod_dname = res[0]
                additional_mod_dnames = [
                    f for f in mod_folder_candidates if f != primary_mod_dname
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
            if len(archive_command_fnames) > 0:
                additional_temp_fpaths = [
                    os.path.join(unarchived_dpath, f)
                    for f in archive_command_fnames
                ]
                additional_fpaths = [
                    os.path.join(extracted_mods_dir_path, f)
                    for f in archive_command_fnames
                ]

    # Step 6: Move to extracted_mods_dir_path
    # 6.0: Handle cases like IR_Revised and SR_Revised, where the path for
    # the targter extracted mod folder should be altered (as it is spell_rev
    # for SR_Revised, for example) or it will overwrite another mod.
    mod_dname_mappers = _get_archive_mod_dir_name_mappers(archive_fname_no_ext)
    if mod_dname_mappers is not None:
        primary_mod_dpath = _map_mod_dir_path(
            primary_mod_dpath, mod_dname_mappers
        )
        for i, dpath in enumerate(additional_mod_dpaths):
            additional_mod_dpaths[i] = _map_mod_dir_path(
                dpath, mod_dname_mappers
            )
        for k, v in mod_dname_mappers.items():
            if k in tp2_fpath:
                tp2_fpath = tp2_fpath.replace(k, v, 1)
            for i, fpath in enumerate(additional_tp2_fpaths):
                if k in fpath:
                    additional_tp2_fpaths[i] = fpath.replace(k, v, 1)
    # 6.1: Copy the primary mod folder
    if os.path.exists(primary_mod_dpath):
        make_all_files_in_dir_writable(primary_mod_dpath)
        shutil.rmtree(primary_mod_dpath)
    shutil.copytree(primary_mod_temp_dpath, primary_mod_dpath)
    if verbose:
        sccs_print(
            f"Primary mod folder '{primary_mod_dpath}' copied to "
            f"'{extracted_mods_dir_path}'."
        )
    # 6.2: Copy additional mod folders
    for temp_dpath, dpath in zip(
        additional_mod_temp_dpaths, additional_mod_dpaths
    ):
        if os.path.exists(dpath):
            make_all_files_in_dir_writable(dpath)
            shutil.rmtree(dpath)
        shutil.copytree(temp_dpath, dpath)
        if verbose:
            sccs_print(
                f"Additional mod folder '{dpath}' copied to "
                f"'{extracted_mods_dir_path}'."
            )
    # 6.3: Copy the main .tp2 file
    if os.path.exists(tp2_fpath):
        os.remove(tp2_fpath)
    shutil.copy(tp2_temp_fpath, tp2_fpath)
    if verbose:
        sccs_print(
            f"Main .tp2 file '{tp2_fpath}' copied to "
            f"'{extracted_mods_dir_path}'."
        )
    # 6.4: Copy additional .tp2 files
    for temp_fpath, fpath in zip(
        additional_tp2_temp_fpaths, additional_tp2_fpaths
    ):
        if os.path.exists(fpath):
            os.remove(fpath)
        shutil.copy(temp_fpath, fpath)
        if verbose:
            sccs_print(
                f"Additional .tp2 file '{fpath}' copied to "
                f"'{extracted_mods_dir_path}'."
            )
    # 6.5: Copy additional files
    for temp_fpath, fpath in zip(additional_temp_fpaths, additional_fpaths):
        if os.path.exists(fpath):
            os.remove(fpath)
        shutil.copy(temp_fpath, fpath)
        if verbose:
            sccs_print(
                f"Additional file '{fpath}' copied to "
                f"'{extracted_mods_dir_path}'."
            )

    # Step 7: Write a Jenga hint file into the mod folder
    hint_fpath = os.path.join(primary_mod_dpath, JENGA_HINT_FNAME)
    hint_data = {
        JengaHintKey.MOD_NAME: mod_name,
        JengaHintKey.ARCHIVE_FNAME: archive_fname,
        JengaHintKey.EXTRACTION_TYPE: mod_structure_type.name,
        JengaHintKey.MAIN_TP2_FPATH: tp2_fpath,
    }
    json.dump(hint_data, open(hint_fpath, "w"), indent=4)

    # Step 8: Clean up temporary directory
    shutil.rmtree(temp_dir)

    return ExtractionResult(
        extraction_type=mod_structure_type,
        mod_folder_path=primary_mod_dpath,
        tp2_file_path=tp2_fpath,
        additional_mod_folder_paths=additional_mod_dpaths,
        additional_tp2_file_paths=additional_tp2_fpaths,
        additional_file_paths=additional_fpaths,
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
    archive_fpath = fuzzy_find_file_or_dir(
        zipped_mods_dpath,
        mod_name,
        archive_search=True,
    )
    archive_fname = os.path.basename(archive_fpath)
    oper_print(f"Best match for archive of mod '{mod_name}': {archive_fname}")
    # prompt for user confirmation
    note_print(
        f"Found archive '{archive_fname}' for mod '{mod_name}' in "
        f"'{zipped_mods_dpath}'. Is this correct? (y/n)"
    )
    response = input()
    if response.lower() not in ["y", "yes"]:
        raise FileNotFoundError(
            f"Unable to locate archive for mod '{mod_name}'."
            "Please extract the mod manually into the extracted mods directory"
            " and add `prefer_extracted: true` to the mod's entry in your"
            " Jenga build file."
        )

    # Step 2: Search for an existing mod folder in extracted_mods_dir_path
    extracted_mods = os.listdir(extracted_mods_dir_path)
    res = process.extractOne(mod_name, extracted_mods)
    if res is not None:
        best_folder_match = res[0]
        existing_mod_folder_path = os.path.join(
            extracted_mods_dir_path, best_folder_match
        )
        # Step 3: Prompt user for deletion
        if os.path.exists(existing_mod_folder_path):
            note_print(
                f"Delete existing mod folder '{best_folder_match}'? (y/n): "
            )
            response = input()
            if response.lower() in ["y", "yes"]:
                shutil.rmtree(existing_mod_folder_path)

    # Step 4-7: Extract the archive and handle the mod structure
    return extract_archive_to_extracted_mods_dir(
        archive_fpath, extracted_mods_dir_path, mod_name
    )


def extract_zipped_mods_in_dir_to_dir(
    zip_mods_dpath: str,
    extracted_mods_dpath: str,
    archive_name_inclusion_criteria: Optional[Callable[[str], bool]] = None,
) -> None:
    """Extract all zipped mods to the extracted mods directory.

    Parameters
    ----------
    zip_mods_dpath : str
        The path to the directory containing the zipped mods.
    extracted_mods_dpath : str
        The path to the directory containing the extracted mods.

    """
    SUPPORTED_EXT = [".zip", ".tar.gz", ".rar"]
    dir_items = os.listdir(zip_mods_dpath)
    archives = [
        item
        for item in dir_items
        if any(item.endswith(ext) for ext in SUPPORTED_EXT)
    ]
    if archive_name_inclusion_criteria is not None:
        archives = [
            archive
            for archive in archives
            if archive_name_inclusion_criteria(archive)
        ]
    n = len(archives)
    done = 0
    for archive in archives:
        res = None
        archive_file_path = os.path.join(zip_mods_dpath, archive)
        oper_print(f"Extracting {archive}...")
        try:
            res = extract_archive_to_extracted_mods_dir(
                archive_file_path, extracted_mods_dpath, mod_name=None
            )
        except IllformedModArchiveError as e:
            note_print(f"Error extracting {archive}: {e}")
        done += 1
        pct = (done / n) * 100
        oper_print(f"[{pct:.2f}%] Finished extracting {archive}:\n {res}")


def extract_all_archives_in_zipped_mods_dir_to_extracted_mods_dir() -> None:
    """Extract all archives in the zipped mods dir to the extracted dir."""
    zipped_dpath = demand_zipped_mod_cache_dir_path()
    extracted_dpath = demand_extracted_mod_cache_dir_path()
    extract_zipped_mods_in_dir_to_dir(zipped_dpath, extracted_dpath)


def extract_some_archives_in_zipped_mods_dir_to_extracted_mods_dir(
    mod_name_part: str,
) -> None:
    """Extract all archives in the zipped mods dir to the extracted dir."""
    zipped_dpath = demand_zipped_mod_cache_dir_path()
    extracted_dpath = demand_extracted_mod_cache_dir_path()
    criteria = lambda name: mod_name_part.lower() in name.lower()
    extract_zipped_mods_in_dir_to_dir(
        zipped_dpath,
        extracted_dpath,
        archive_name_inclusion_criteria=criteria,
    )


def overwrite_dir_with_another_dir(
    another_dir: str, dir_to_overwrite: str
) -> None:
    """Overwrite the game directory with the source directory.

    Parameters
    ----------
    another_dir : str
        The path to the source directory.
    dir_to_overwrite : str
        The path to the game directory.

    """
    oper_print(f"Overwriting '{dir_to_overwrite}' with '{another_dir}'...")
    if os.path.exists(dir_to_overwrite):
        make_all_files_in_dir_writable(dir_to_overwrite)
        try:
            shutil.rmtree(dir_to_overwrite)
        except PermissionError:
            # run as sudo
            os.system(f'sudo rm -rf "{dir_to_overwrite}"')
        oper_print(f"Deleted existing game directory '{dir_to_overwrite}'.")
    try:
        shutil.copytree(another_dir, dir_to_overwrite)
    except PermissionError:
        # run as sudo
        os.system(f'sudo cp -r "{another_dir}" "{dir_to_overwrite}"')
    make_all_files_in_dir_writable(dir_to_overwrite)
    oper_print(f"Game directory overwritten with '{another_dir}'.")


def overwrite_game_dir_with_source_dir(
    game_alias: str,
    source_dir_type: str,
) -> None:
    """Overwrite the game directory with the source directory.

    Parameters
    ----------
    game_alias : str
        The game alias.
    source_dir_type : str
        The source directory type. Currently supports 'CLEAN_SOURCE' and
        'EET_SOURCE'.

    """
    game_dir = get_game_dir(game_alias, CfgKey.TARGET)
    if game_dir is None:
        raise FileNotFoundError(
            f"Game directory for '{game_alias}' not found."
        )
    source_dir = demand_game_dir_path(game_alias, dir_type=source_dir_type)
    note_print(
        f"Preparing to OVERWRITE the game directory at '{game_dir}' with a "
        f"source directory at '{source_dir}'! \n"
        "To confirm, type 'I confirm' and press Enter."
    )
    response = input()
    if response.lower() != "i confirm":
        raise ValueError("User did not confirm overwrite.")
    overwrite_dir_with_another_dir(source_dir, game_dir)
    sccs_print(
        f"Game directory at '{game_dir}' overwritten with '{source_dir_type}' "
        f"directory at '{source_dir}'."
    )
