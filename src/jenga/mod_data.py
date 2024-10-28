"""The mod alias registry."""

# stdlib imports
import os
import json
from typing import Dict, List, Optional

# local imports
from .config import get_xdg_config_dpath
from .printing import note_print, sccs_print

# ===== Mod Aliases Registry =====

# Mod Names
EET = "EET"
LEUI_BG1EE = "LEUI-BG1EE"
AFH = "AnotherFineHell"
EET_END = "EET_END"
LUCY = "LUCY"
DC = "DC"
CRUCIBLE = "CRUCIBLE"
ITEM_REV = "item_rev"
SPELL_REV = "spell_rev"


# Mod Alias Registry
ALIAS_TO_MOD_REGISTRY: Dict[str, str] = {
    # EET ALIASES
    EET.lower(): EET.lower(),
    # LEUI_BG1EE ALIASES
    LEUI_BG1EE.lower(): LEUI_BG1EE.lower(),
    "lefreuts-enhanced-ui-bg1ee-skin".lower(): LEUI_BG1EE.lower(),
    # AFH ALIASES
    AFH.lower(): AFH.lower(),
    "C#ANOTHERFINEHELL".lower(): AFH.lower(),
    # LUCY ALIASES
    LUCY.lower(): LUCY.lower(),
    "lucy-the-wyvern".lower(): LUCY.lower(),
    # DC ALIASES
    DC.lower(): DC.lower(),
    "DungeonCrawl".lower(): DC.lower(),
    # CRUCIBLE ALIASES
    CRUCIBLE.lower(): CRUCIBLE.lower(),
    # ITEM_REV ALIASES
    ITEM_REV.lower(): ITEM_REV.lower(),
    "itemrev": ITEM_REV.lower(),
    "item revisions": ITEM_REV.lower(),
    "item_revisions": ITEM_REV.lower(),
    # SPELL_REV ALIASES
    SPELL_REV.lower(): SPELL_REV.lower(),
    "spellrev": SPELL_REV.lower(),
    "spell revisions": SPELL_REV.lower(),
    "spell_revisions": SPELL_REV.lower(),
    # EET_END ALIASES
    EET_END.lower(): EET_END.lower(),
    "EETEND".lower(): EET_END.lower(),
}

def get_mod_name_by_alias(alias: str) -> Optional[str]:
    """Get the mod name by alias.

    Parameters
    ----------
    alias : str
        The alias of the mod.

    Returns
    -------
    Optional[str]
        The name of the mod if the alias exists, otherwise None.
    """
    return ALIAS_TO_MOD_REGISTRY.get(alias.lower(), None)

# build the reverse alias registry
MOD_TO_ALIAS_LIST_REGISTRY: Dict[str, List[str]] = {}
for alias, mod in ALIAS_TO_MOD_REGISTRY.items():
    if mod not in MOD_TO_ALIAS_LIST_REGISTRY:
        MOD_TO_ALIAS_LIST_REGISTRY[mod] = [alias]
    else:
        MOD_TO_ALIAS_LIST_REGISTRY[mod].append(alias)


def get_aliases_by_mod(mod: str) -> List[str]:
    """Get the aliases by mod.

    Parameters
    ----------
    mod : str
        The name of the mod.

    Returns
    -------
    List[str]
        The list of aliases for the mod.
    """
    return MOD_TO_ALIAS_LIST_REGISTRY.get(mod.lower(), [])


def add_alias_to_mod(alias: str, mod: str) -> None:
    """Add an alias to the mod.

    Parameters
    ----------
    alias : str
        The alias of the mod.
    """
    alias = alias.lower()
    mod = mod.lower()
    ALIAS_TO_MOD_REGISTRY[alias] = mod
    if mod not in MOD_TO_ALIAS_LIST_REGISTRY:
        MOD_TO_ALIAS_LIST_REGISTRY[mod] = [alias]
    else:
        MOD_TO_ALIAS_LIST_REGISTRY[mod].append(alias)


_ALIAS_REG_FNAME = "mod_alias_registry.json"
_REV_ALIAS_REG_FNAME = "mod_alias_registry_reversed.json"


def dump_aliases_registry_to_config_dir() -> None:
    """Writes the mod alias registry to the config directory as a json file.
    """
    ALIAS_REGISTRY_FPATH = os.path.join(
        get_xdg_config_dpath(), _ALIAS_REG_FNAME)
    with open(ALIAS_REGISTRY_FPATH, "w") as f:
        json.dump(ALIAS_TO_MOD_REGISTRY, f)
    REV_ALIAS_REGISTRY_FPATH = os.path.join(
        get_xdg_config_dpath(), _REV_ALIAS_REG_FNAME)
    with open(REV_ALIAS_REGISTRY_FPATH, "w") as f:
        json.dump(MOD_TO_ALIAS_LIST_REGISTRY, f)
    sccs_print("Dumped mod alias registry to the config directory.")


def load_aliases_registry_from_config_dir() -> None:
    """Loads the mod alias registry from the config directory."""
    ALIAS_REGISTRY_FPATH = os.path.join(
        get_xdg_config_dpath(), _ALIAS_REG_FNAME)
    if os.path.exists(ALIAS_REGISTRY_FPATH):
        with open(ALIAS_REGISTRY_FPATH, "r") as f:
            ALIAS_TO_MOD_REGISTRY.update(json.load(f))
        sccs_print("Loaded mod alias registry from the config directory.")
    else:
        note_print(
            "Mod alias registry file not found in the config directory.")
    REV_ALIAS_REGISTRY_FPATH = os.path.join(
        get_xdg_config_dpath(), _REV_ALIAS_REG_FNAME)
    if os.path.exists(REV_ALIAS_REGISTRY_FPATH):
        with open(REV_ALIAS_REGISTRY_FPATH, "r") as f:
            MOD_TO_ALIAS_LIST_REGISTRY.update(json.load(f))
        sccs_print("Loaded reversed mod alias registry from the config "
                   "directory.")
    else:
        note_print(
            "Reversed mod alias registry file not found in the config "
            "directory.")



# ===== Mod Hints =====

JENGA_HINT_FNAME = ".jenga_hint.json"


class JengaHintKey:
    """Keys for the Jenga hint file."""

    MOD_NAME = "mod_name"
    ARCHIVE_FNAME = "archive_fname"
    EXTRACTION_TYPE = "extraction_type"
    MAIN_TP2_FPATH = "main_tp2_fpath"
    ALIASES = "aliases"
