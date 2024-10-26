"""Jenga mod-specific fixes."""

# stdlib imports
import os
import shutil
from typing import Dict, List, Sequence

# 3rd party imports
from birch import Birch


# ===== Base Fix Classes =====

class JengaPrePostFix:
    """A runnable object that fixes a specific mod issue during a Jenga build.

    Parameters
    ----------
    mod_name : str
        The name of the mod that the fix is for.

    Attributes
    ----------
    fix_name : str
        The name of the fix.

    """

    def __init__(self, mod_name):
        self.mod_name = mod_name
        self.fix_name = "JengaPrePostFix"

    def apply(
        self,
        mod_dir: str,
        mod_tp2_path: str,
        jenga_config: Birch,
        run_config: dict,
    ) -> None:
        """Run the fix.

        Parameters
        ----------
        mod_dir : str
            The path to the mod directory.
        mod_tp2_path : str
            The path to the mod's TP2 file.
        jenga_config : Birch
            The Jenga configuration.
        run_config : dict
            The run configuration.

        """
        raise NotImplementeodError("Fixes must implement the apply method.")


class JengaCmdFix:
    """A runnable object that alters a mod install command to fix an issue.

    Parameters
    ----------
    mod_name : str
        The name of the mod that the fix is for.

    Attributes
    ----------
    fix_name : str
        The name of the fix.
    """

    def __init__(self, mod_name):
        self.mod_name = mod_name
        self.fix_name = "JengaPrePostFix"

    def apply(
        self,
        cmd: List[str],
        jenga_config: Birch,
        run_config: dict,
    ) -> List[str]:
        """Run the fix.

        Parameters
        ----------
        cmd : List[str]
            The command to alter.
        jenga_config : Birch
            The Jenga configuration.
        run_config : dict
            The run configuration.

        Returns
        -------
        List[str]
            The altered command.
        """
        raise NotImplementeodError("Fixes must implement the apply method.")


# ===== EET Fixes =====

class EetAddBg1PathCmdFix(JengaCmdFix):
    """Add the BG1 path to the EET install command.

    This fix is necessary for EET installations to work correctly.
    """

    def __init__(self, mod_name):
        super().__init__(mod_name)
        self.fix_name = "EetAddBg1PathCmdFix"

    def apply(
        self,
        cmd: List[str],
        jenga_config: Birch,
        run_config: dict,
    ) -> List[str]:
        # Add the BG1 path to the command
        try:
            bg1_path = jenga_config["BGEE_DIR_PATH"]
        except KeyError:
            raise ValueError(
                "BGEE_DIR_PATH not found in the Jenga config."
                "It must be set to the path of the BG1 directory in order for"
                " the EET installation to work correctly."
            )
        cmd.append("--args-list")
        cmd.append("sp")
        cmd.append(f"{bg1_path}")
        return cmd

# ===== AnotherFineHell Fixes =====

class AnotherFineHellAfhvisFix(JengaPrePostFix):
    __doc__ = (
        JengaPrePostFix.__doc__
        + """
    Fixes an issue for AnotherFineHell on MacOS where installation fails du to
    ERROR: error loading [c#anotherfinehell/scripts/c#afhvis.baf]
    ERROR: compiling [c#anotherfinehell/scripts/c#afhvis.baf]!
    """
    )

    def __init__(self, mod_name):
        super().__init__(mod_name)
        self.fix_name = "AnotherFineHellAfhvisFix"

    AFVIS_FNAME = "c#afhvis.baf"
    REP_FNAME = "c#afhjng.baf"
    SCR_DNAME = "scripts"

    def apply(
        self,
        mod_dir: str,
        mod_tp2_path: str,
        jenga_config: Birch,
        run_config: dict,
    ) -> None:
        afvis_path = os.path.join(mod_dir, self.SCR_DNAME, self.AFVIS_FNAME)
        rep_path = os.path.join(mod_dir, self.SCR_DNAME, self.REP_FNAME)
        # copy afvhvis.baf to afhjng.baf
        shutil.copy(afvis_path, rep_path)
        # update tp2 file to use afhjng.baf for the the MOVE command
        with open(mod_tp2_path, "r") as f:
            lines = f.readlines()
        with open(mod_tp2_path, "w") as f:
            for line in lines:
                if self.AFVIS_FNAME in line and line.startswith("MOVE"):
                    f.write(line.replace(self.AFVIS_FNAME, self.REP_FNAME))
                else:
                    f.write(line)


# ===== Crucible Fixes =====

class CrucibleMihModConflictIgnore(JengaPrePostFix):
    """Bypass the Crucible mod conflict with MIH_EQ.

    Edits the Crucible tp2 file to remove line that raise mod conflict and
    terminate on an existing installation of MIH_EQ (Made in Heaven: Encounters
    & Quests).

    """

    def __init__(self, mod_name):
        super().__init__(mod_name)
        self.fix_name = "CrucibleMihModConflictIgnore"

    LINE_TO_DELETE = (
        "REQUIRE_PREDICATE !FILE_EXISTS ~mih_eq/setup-mih_eq.tp2~ @3002"
    )
    SEARCH_TOKEN = "setup-mih_eq.tp2"

    def apply(
        self,
        mod_dir: str,
        mod_tp2_path: str,
        jenga_config: Birch,
        run_config: dict,
    ) -> None:
        # Read the tp2 file in mod_tp2_path and remove all lines containing
        # the SEARCH_TOKEN
        with open(mod_tp2_path, "r") as f:
            lines = f.readlines()
        with open(mod_tp2_path, "w") as f:
            for line in lines:
                if self.SEARCH_TOKEN not in line:
                    f.write(line)


# ===== EET_END Fixes =====

def fix_pdialog_files_in_directory(directory_path: str) -> None:
    """Fix pdialog.2da files by removing lines with only a single word.

    Parameters
    ----------
    directory_path : str
        The path to the directory to search for pdialog.2da files.

    """
    for root, _, files in os.walk(directory_path):
        for file_name in files:
            if file_name.lower() == "pdialog.2da":
                file_path = os.path.join(root, file_name)
                fix_pdialog_file(file_path)


def fix_pdialog_file(file_path: str) -> None:
    """Remove lines containing only a single word from given pdialog.2da file.

    Parameters
    ----------
    file_path : str
        The path to the pdialog.2da

    Examples
    --------
    fix_pdialog_files_in_directory("/path/to/directory")

    """
    with open(file_path, "rt", encoding="utf-8") as file:
        lines = file.readlines()
    # Filter out lines with only a single word
    fixed_lines = [line for line in lines if len(line.split()) > 1]
    with open(file_path, "wt", encoding="utf-8") as file:
        file.writelines(fixed_lines)


class EetEndPdialogPartialLinesFix(JengaPrePostFix):
    __doc__ = (
        JengaPrePostFix.__doc__
        + """
    Fixes an issue for EET_END where installation fails due to
    badly formatted lines in pdialog.2da, probably caused by Glam's NPC Pack.
    See here for more:
    https://www.gibberlings3.net/forums/topic/36138-install-issue-with-some-mods-glams-thalantyr/
    """
    )

    def __init__(self, mod_name):
        super().__init__(mod_name)
        self.fix_name = "EetEndPdialogPartialLinesFix"

    def apply(
        self,
        mod_dir: str,
        mod_tp2_path: str,
        jenga_config: Birch,
        run_config: dict,
    ) -> None:
        fix_pdialog_files_in_directory(run_config["game_dir"])


# ===== Mod Aliases Registry =====

# Mod Names
EET = "EET"
AFH = "AnotherFineHell"
EET_END = "EET_END"
LUCY = "LUCY"
DC = "DC"
CRUCIBLE = "CRUCIBLE"


# Mod Alias Registry
ALIAS_TO_MOD_REGISTRY: Dict[str, str] = {
    # EET ALIASES
    EET.lower(): EET.lower(),
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


PRE_FIXES_REGISTRY: Dict[str, Sequence[JengaPrePostFix]] = {
    # AFH.lower(): [
    #     AnotherFineHellAfhvisFix(AFH),
    # ],
    EET_END.lower(): [
        EetEndPdialogPartialLinesFix(EET_END),
    ],
    CRUCIBLE.lower(): [
        CrucibleMihModConflictIgnore(CRUCIBLE),
    ],
}


CMD_FIXES_REGISTRY: Dict[str, Sequence[JengaCmdFix]] = {
    EET.lower(): [
        EetAddBg1PathCmdFix(EET),
    ],
}


POST_FIXES_REGISTRY: Dict[str, Sequence[JengaPrePostFix]] = {}


def get_prepost_fixes_for_mod(
    mod_name: str,
    prefix: bool,
) -> Sequence[JengaPrePostFix]:
    """Get any fixes for the specified mod.

    Parameters
    ----------
    mod_name : str
        The name of the mod.
    prefix : bool
        Whether to get a prefix or postfix.

    Returns
    -------
    Sequence[JengaPrePostFix]
        A list of any fixes to apply before/after the specified mod.

    """
    uniform_name = ALIAS_TO_MOD_REGISTRY.get(
        mod_name.lower(), mod_name.lower()
    )
    registry = PRE_FIXES_REGISTRY if prefix else POST_FIXES_REGISTRY
    return registry.get(uniform_name, [])


def get_cmd_fixes_for_mod(mod_name: str) -> Sequence[JengaCmdFix]:
    """Get any command fixes for the specified mod.

    Parameters
    ----------
    mod_name : str
        The name of the mod.

    Returns
    -------
    Sequence[JengaCmdFix]
        A list of any command fixes to apply for the specified mod.

    """
    uniform_name = ALIAS_TO_MOD_REGISTRY.get(
        mod_name.lower(), mod_name.lower())
    return CMD_FIXES_REGISTRY.get(uniform_name, [])
