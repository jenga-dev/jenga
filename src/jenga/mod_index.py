"""A simple mod infex inferred from extracted mods."""

# stdlib imports
import os
import re
from dataclasses import dataclass
from typing import Dict, Optional

from .config import EXTRACTED_MOD_CACHE_DIR_PATH

# local imports
from .util import get_tp2_names_and_paths


@dataclass
class ModInfo:
    """A simple mod info inferred from extracted mods."""

    name: str
    version: str
    author: str
    description: str
    extracted_dpath: str
    tp2_fpath: str


MOD_INDEX: Dict[str, ModInfo] = {}


def get_mod_info(mod_name: str) -> Optional[ModInfo]:
    """Get mod info by mod name."""
    try:
        MOD_INDEX[mod_name]
    except KeyError:
        return None


def mod_info_from_dpath(
    extracted_mod_dpath: str,
) -> Optional[ModInfo]:
    # - extracted_dpath: the path to the folder
    # How mod attributes are determined:
    # - name: the name (without extension) of the shortest-named
    #         .tp2 file in the folder (including subfolders)
    # - tp2_fpath: the path to the shortest-named .tp2 file in the folder
    #              (including subfolders)
    tp2_fnames_to_fpaths = get_tp2_names_and_paths(extracted_mod_dpath)
    tp2_fname = min(tp2_fnames_to_fpaths.keys(), key=len)
    if ".tp2" in tp2_fname:
        name = tp2_fname.replace(".tp2", "")
    else:
        name = tp2_fname
    tp2_fpath = tp2_fnames_to_fpaths[tp2_fname]
    # get the version of the mod
    # - version: the version string in the .tp2 file
    #            it is a line of the form VERSION ~0.91.1~
    version = ""
    pattern = re.compile(r"VERSION\s*\~([a-zA-Z0-9\.\_\-]+)\~")
    with open(tp2_fpath, "r", encoding="utf-8") as tp2_f:
        tp2_lines = tp2_f.readlines()
    for line in tp2_lines:
        match = pattern.match(line)
        if match:
            version = match.group(1)
            break
    # get the author of the mod
    # - author: the author string in the .tp2 file
    #           format: AUTHOR ~SubtleD and Grammarsalad~
    author = ""
    pattern = re.compile(r"AUTHOR\s*\~([a-zA-Z0-9\.\_\-\s]+)\~")
    for line in tp2_lines:
        match = pattern.match(line)
        if match:
            author = match.group(1)
            break
    # get the description of the mod
    # - description: if the root of the folder contains an .ini file,
    #                the value of the Description key in the [Metadata] section
    #                of the .ini file. Otherwise, the empty string.
    description = ""
    # search for an .ini file in the root of the folder
    ini_fpaths = []
    for entry in os.scandir(extracted_mod_dpath):
        if entry.is_file() and entry.name.endswith(".ini"):
            ini_fpaths.append(entry.path)
    if len(ini_fpaths) > 0:
        for ini_fpath in ini_fpaths:
            # read the first .ini file found
            with open(ini_fpath, "r", encoding="utf-8") as ini_f:
                ini_lines = ini_f.readlines()
            # search for the [Metadata] section
            metadata_section = False
            for line in ini_lines:
                if metadata_section:
                    if line.startswith("Description"):
                        description = line.split("=")[1].strip()
                if "[Metadata]" in line:
                    metadata_section = True
    # return a ModInfo object
    return ModInfo(
        name=name,
        version=version,
        author=author,
        description=description,
        extracted_dpath=extracted_mod_dpath,
        tp2_fpath=tp2_fpath,
    )


def populate_mod_index_by_dpath(
    extracted_mods_dpath: str,
) -> None:
    """Populate mod index from extracted mods."""
    # iterate over all folders in extracted_mods_dpath,
    # and for each folder, determine mod attributes like so:
    for fof in os.scandir(extracted_mods_dpath):
        if fof.is_dir():
            mod_info = mod_info_from_dpath(fof.path)
            if mod_info:
                MOD_INDEX[mod_info.name] = mod_info


def populate_mod_index_from_extracted_mods_dir() -> None:
    """Populate mod index from the extracted mods directory."""
    if EXTRACTED_MOD_CACHE_DIR_PATH is None:
        raise ValueError("EXTRACTED_MOD_CACHE_DIR_PATH is not set.")
    if not os.path.exists(EXTRACTED_MOD_CACHE_DIR_PATH):
        raise FileNotFoundError(
            "EXTRACTED_MOD_CACHE_DIR_PATH does not exist: "
            f"{EXTRACTED_MOD_CACHE_DIR_PATH}"
        )
    if os.path.isfile(EXTRACTED_MOD_CACHE_DIR_PATH):
        raise NotADirectoryError(
            "EXTRACTED_MOD_CACHE_DIR_PATH is not a directory: "
            f"{EXTRACTED_MOD_CACHE_DIR_PATH}"
        )
    populate_mod_index_by_dpath(EXTRACTED_MOD_CACHE_DIR_PATH)
