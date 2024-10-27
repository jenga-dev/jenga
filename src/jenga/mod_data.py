"""The mod alias registry."""

from typing import Dict, List

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


# build the reverse alias registry
MOD_TO_ALIAS_LIST_REGISTRY: Dict[str, List[str]] = {}
for alias, mod in ALIAS_TO_MOD_REGISTRY.items():
    if mod not in MOD_TO_ALIAS_LIST_REGISTRY:
        MOD_TO_ALIAS_LIST_REGISTRY[mod] = [alias]
    else:
        MOD_TO_ALIAS_LIST_REGISTRY[mod].append(alias)


# ===== Mod Hints =====

JENGA_HINT_FNAME = ".jenga_hint.json"


class JengaHintKey:
    """Keys for the Jenga hint file."""
    MOD_NAME = "mod_name"
    ARCHIVE_FNAME = "archive_fname"
    EXTRACTION_TYPE = "extraction_type"
    MAIN_TP2_FPATH = "main_tp2_fpath"
