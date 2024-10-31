"""A simple mod infex inferred from extracted mods."""

# stdlib imports
import json
import os
import re
from dataclasses import dataclass
from typing import Dict, List, Optional

# 3rd party imports
from rich.progress import track

# local imports
from .config import (
    demand_extracted_mod_cache_dir_path,
    get_xdg_config_dpath,
)
from .fs_basics import (
    robust_read_lines_from_text_file,
)
from .fs_util import (
    _get_name_mapper_func_by_archive_fname,
    get_tp2_names_and_paths,
)
from .mod_data import (
    JENGA_HINT_FNAME,
    JengaHintKey,
    add_alias_to_mod,
    clear_alias_registries_from_config_dir,
    dump_aliases_registry_to_config_dir,
    get_mod_name_by_alias,
    load_aliases_registry_from_config_dir,
    reset_inmemory_alias_to_mod_registry,
    reset_inmemory_mod_to_alias_list_registry,
)
from .printing import (
    note_print,
    oper_print,
    sccs_print,
)


@dataclass
class ModInfo:
    """A simple mod info inferred from extracted mods."""

    name: str
    full_name: str
    version: str
    author: str
    description: str
    extracted_dpath: str
    tp2_fpath: str
    aliases: List[str]
    download: Optional[str] = None
    label_type: Optional[str] = None
    mod_type: Optional[str] = None
    before: Optional[str] = None
    after: Optional[str] = None
    archive_fname: Optional[str] = None


MOD_INDEX: Dict[str, ModInfo] = {}


def get_mod_info(mod_name: str) -> Optional[ModInfo]:
    """Get mod info by mod name."""
    try:
        return MOD_INDEX[mod_name.lower()]
    except KeyError:
        try:
            resolved_mod_name = get_mod_name_by_alias(mod_name)
            if resolved_mod_name is None:
                note_print(f"Mod {mod_name} not found in the mod index.")
                return None
            return MOD_INDEX[resolved_mod_name.lower()]
        except KeyError:
            note_print(f"Mod {mod_name} not found in the mod index.")
            return None


def read_mod_ini_file(ini_fpath: str) -> Dict[str, str]:
    """Read the mod .ini file.

    Parameters
    ----------
    ini_fpath : str
        The path to the mod .ini file.

    Returns
    -------
    Dict[str, str]
        The key-value pairs in the .ini file.

    """
    ini_lines = robust_read_lines_from_text_file(ini_fpath)
    metadata_section = False
    key_value_pairs = {}
    for line in ini_lines:
        if metadata_section:
            if "=" in line:
                # split on the firt occurence of "="
                key, value = line.split("=", 1)
                key_value_pairs[key.strip().lower()] = value.strip()
        if "[Metadata]" in line:
            metadata_section = True
    return key_value_pairs


def read_mod_tp2_file(tp2_fpath: str) -> Dict[str, Optional[str]]:
    """Read the mod .tp2 file.

    Parameters
    ----------
    tp2_fpath : str
        The path to the mod .tp2 file.

    Returns
    -------
    Dict[str, str]
        The key-value pairs in the .tp2 file.

    """
    # - version: the version string in the .tp2 file
    #            it is a line of the form VERSION ~0.91.1~
    # - author: the author string in the .tp2 file
    #           format: AUTHOR ~SubtleD and Grammarsalad~
    tp2_lines = robust_read_lines_from_text_file(tp2_fpath)
    version = None
    author = None
    ver_pat = re.compile(r"VERSION\s*\~([a-zA-Z0-9\.\_\-]+)\~")
    author_pat = re.compile(r"AUTHOR\s*\~([a-zA-Z0-9\.\_\-\s]+)\~")
    for line in tp2_lines:
        ver_match = ver_pat.match(line)
        if ver_match:
            version = ver_match.group(1)
        author_match = author_pat.match(line)
        if author_match:
            author = author_match.group(1)
    return {"version": version, "author": author}


def mod_info_from_dpath(
    extracted_mod_dpath: str,
) -> Optional[ModInfo]:
    """Get mod info from extracted mod directory path.

    Parameters
    ----------
    extracted_mod_dpath : str
        The path to the extracted mod directory.

    Returns
    -------
    Optional[ModInfo]
        The mod info object if successful, otherwise None.

    """
    # read the hint file if it exists
    hint_fpath = os.path.join(extracted_mod_dpath, JENGA_HINT_FNAME)
    hint = {}
    if os.path.exists(hint_fpath):
        hint = json.load(open(hint_fpath, "r"))
    aliases: List[str] = []
    if hint.get(JengaHintKey.ALIASES):
        aliases = hint[JengaHintKey.ALIASES]
    # How mod attributes are determined:
    # - name: the name (without extension) of the shortest-named
    #         .tp2 file in the folder (including subfolders)
    # - tp2_fpath: the path to the shortest-named .tp2 file in the folder
    #              (including subfolders)
    name = None
    tp2_fpath = None
    archive_fname = None
    archive_inferred_version = None
    # better to get the name and tp2_fpath from the hint file
    if JengaHintKey.MOD_NAME in hint:
        name = hint[JengaHintKey.MOD_NAME]
    if JengaHintKey.MAIN_TP2_FPATH in hint:
        tp2_fpath = hint[JengaHintKey.MAIN_TP2_FPATH]
    if JengaHintKey.ARCHIVE_FNAME in hint:
        archive_fname = hint[JengaHintKey.ARCHIVE_FNAME]
    if JengaHintKey.ARCHIVE_INFERRED_VERSION in hint:
        archive_inferred_version = hint[JengaHintKey.ARCHIVE_INFERRED_VERSION]
    # if one or both are missing from the hint file, infer them from the folder
    if name is None or tp2_fpath is None:
        tp2_fnames_to_fpaths = get_tp2_names_and_paths(extracted_mod_dpath)
        try:
            tp2_fname = min(tp2_fnames_to_fpaths.keys(), key=len)
        except ValueError:
            tp2_fnames_to_fpaths = get_tp2_names_and_paths(
                extracted_mod_dpath, verbose=True
            )
            tp2_fname = min(tp2_fnames_to_fpaths.keys(), key=len)
        if name is None:
            if ".tp2" in tp2_fname:
                name = tp2_fname.replace(".tp2", "")
            else:
                name = tp2_fname
        if tp2_fpath is None:
            tp2_fpath = tp2_fnames_to_fpaths[tp2_fname]
    data_from_tp2 = read_mod_tp2_file(tp2_fpath)
    author = data_from_tp2["author"]
    version = data_from_tp2["version"]
    # search for an .ini file in the root of the folder
    ini_fpaths = []
    data_from_ini = {}
    for entry in os.scandir(extracted_mod_dpath):
        if entry.is_file() and entry.name.endswith(".ini"):
            ini_fpaths.append(entry.path)
    if len(ini_fpaths) > 0:
        for ini_fpath in ini_fpaths:
            res = read_mod_ini_file(ini_fpath)
            data_from_ini.update(res)
    if "author" in data_from_ini:
        author = data_from_ini.get("author")
    full_name = data_from_ini.get("name", name)
    description = data_from_ini.get("description", "")
    download = data_from_ini.get("download")
    label_type = data_from_ini.get("labeltype")
    mod_type = data_from_ini.get("type")
    before = data_from_ini.get("before")
    after = data_from_ini.get("after")
    if version is None:
        if archive_inferred_version is not None:
            version = archive_inferred_version
        else:
            version = ""
    if author is None:
        author = ""
    # return a ModInfo object
    return ModInfo(
        name=name,
        full_name=full_name,
        version=version,
        author=author,
        description=description,
        extracted_dpath=extracted_mod_dpath,
        tp2_fpath=tp2_fpath,
        aliases=aliases,
        download=download,
        label_type=label_type,
        mod_type=mod_type,
        before=before,
        after=after,
        archive_fname=archive_fname,
    )


MOD_INDEX_FNAME = "mod_index.json"
MOD_INDEX_FPATH = os.path.join(
    get_xdg_config_dpath(),
    MOD_INDEX_FNAME,
)


def _is_likely_mod_dir_name(dir_name: str) -> bool:
    """Check if a directory name is like a mod directory name."""
    lname = dir_name.lower()
    if lname.startswith("__"):
        return False
    if lname.startswith("."):
        return False
    if lname == "docs":
        return False
    if lname.endswith(".app"):
        return False
    return True


def populate_mod_index_by_dpath(
    extracted_mods_dpath: str,
    verbose: Optional[bool] = False,
) -> None:
    """Populate mod index from extracted mods."""
    global MOD_INDEX
    MOD_INDEX = {}
    reset_inmemory_alias_to_mod_registry()
    reset_inmemory_mod_to_alias_list_registry()
    # iterate over all folders in extracted_mods_dpath,
    # and for each folder, determine mod attributes like so:
    oper_print("Populating mod index from the extracted mods folder...")
    entries = list(os.scandir(extracted_mods_dpath))
    for fof in track(
        entries,
        description="Processing mods...",
    ):
        mod_info = None
        if fof.is_dir():
            if _is_likely_mod_dir_name(fof.name):
                # try:
                mod_info = mod_info_from_dpath(fof.path)
                # except Exception as e:
                #     note_print(
                #         f"Error while processing mod dir at {fof.path}: {e}"
                #         "\nSkipping this mod."
                #     )
            if mod_info is not None:
                mod_key = mod_info.name.lower()
                MOD_INDEX[mod_key] = mod_info
                # handle the unqiue case of name mappers, for mods like
                # ir_revised and sr_revised, which confuse with aliases they
                # shouldn't have, like "item_rev" and "spell_rev", respectively
                archive_fname = mod_info.archive_fname
                alias_fix = lambda alias: alias
                if archive_fname is not None:
                    name_mapper_func = _get_name_mapper_func_by_archive_fname(
                        archive_fname
                    )
                    if name_mapper_func is not None:
                        alias_fix = name_mapper_func
                        mod_info.aliases = [
                            name_mapper_func(alias)
                            for alias in mod_info.aliases
                        ]
                full_name = mod_info.full_name
                if full_name is not None and len(full_name) > 0:
                    alias = alias_fix(full_name)
                    add_alias_to_mod(alias, mod_info.name)
                    mod_info.aliases.append(alias)
                tp2_fpath = mod_info.tp2_fpath
                if tp2_fpath is not None:
                    tp2_fname = os.path.basename(tp2_fpath)
                    alias = alias_fix(os.path.splitext(tp2_fname)[0])
                    add_alias_to_mod(alias, mod_info.name)
                    mod_info.aliases.append(alias)
                for alias in mod_info.aliases:
                    add_alias_to_mod(alias, mod_info.name)
                mod_info.aliases = list(set(mod_info.aliases))
                if verbose:
                    sccs_print(
                        f"Added to the mod index: {mod_key}, {mod_info}"
                    )
    sccs_print("Mod index populated from the extracted mods folder.")
    # write the mod alias registries to files
    clear_alias_registries_from_config_dir()
    dump_aliases_registry_to_config_dir()
    # write the mod index to a file
    dump_dict = {
        name.lower(): info.__dict__ for name, info in MOD_INDEX.items()
    }
    # delete the file if it exists
    if os.path.exists(MOD_INDEX_FPATH):
        os.remove(MOD_INDEX_FPATH)
    # print("\n\n======= MOD INDEX DUMP DEBUG ===============")
    # print(dump_dict)
    # print("============================================\n\n")
    with open(MOD_INDEX_FPATH, "w") as f:
        json.dump(dump_dict, f, indent=4)
    sccs_print(f"Mod index written to {MOD_INDEX_FPATH}")


def load_mod_index_from_config() -> None:
    """Load mod index from config."""
    global MOD_INDEX
    if not os.path.exists(MOD_INDEX_FPATH) or (
        not os.path.isfile(MOD_INDEX_FPATH)
    ):
        return
    oper_print("Attempting to load mod index from config directory...")
    with open(MOD_INDEX_FPATH, "r") as f:
        mod_index = json.load(f)
    if len(mod_index) == 0:
        note_print("Mod index file is empty. Skipping loading into memory.")
        return
    MOD_INDEX = {}
    for name, info in mod_index.items():
        MOD_INDEX[name] = ModInfo(**info)
    sccs_print("Mod index loaded from config directory.")


def populate_mod_index_from_extracted_mods_dir(
    verbose: Optional[bool] = False,
) -> None:
    """Populate mod index from the extracted mods directory."""
    populate_mod_index_by_dpath(
        extracted_mods_dpath=demand_extracted_mod_cache_dir_path(),
        verbose=verbose,
    )
