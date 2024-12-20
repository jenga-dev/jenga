"""Jenga mod-specific fixes."""

# stdlib imports
import os
import shutil
from typing import Dict, List, Sequence

# 3rd party imports
from birch import Birch

# local imports
from .config import (
    CfgKey,
)
from .fs_basics import merge_dirs
from .mod_data import (
    CRUCIBLE,
    EET,
    EET_END,
    ITEM_REV,
    SPELL_REV,
    get_mod_name_by_alias,
)
from .mod_index import get_mod_info

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
        """Initialize the JengaPrePostFix object."""
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
        raise NotImplementedError("Fixes must implement the apply method.")


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
        """Initialize the JengaCmdFix object."""
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
        raise NotImplementedError("Fixes must implement the apply method.")


# ===== EET Fixes =====


class EetCopyEetCommandFilePreFix(JengaPrePostFix):
    """Copy the EET command file to the game directory before installation.

    This fix is necessary for EET installations to work correctly.

    """

    def __init__(self, mod_name):
        """Initialize the EetCopyEetCommandFilePreFix object."""
        super().__init__(mod_name)
        self.fix_name = "EetCopyEetCommandFilePreFix"

    def apply(
        self,
        mod_dir: str,
        mod_tp2_path: str,
        jenga_config: Birch,
        run_config: dict,
    ) -> None:
        """Copy the EET command file to the game directory."""
        # find the setup-EET.command file
        eet_cmd_fname = None
        eet_cmd_fpath = None
        ex_mods_dir = jenga_config[CfgKey.EXTRACTED_MOD_CACHE_DIR_PATH]
        for fname in os.listdir(ex_mods_dir):
            if fname.lower() == "setup-eet.command":
                eet_cmd_fname = fname
                eet_cmd_fpath = os.path.join(ex_mods_dir, fname)
                break
        if eet_cmd_fpath is None or eet_cmd_fname is None:
            raise FileNotFoundError(
                "setup-EET.command file not found in the extracted mods "
                "directory. Unable to copy the setup-EET.command file to the "
                "game directory."
            )
        eet_cmd_target_fpath = os.path.join(
            run_config["game_install_dir"], eet_cmd_fname
        )
        # Delete any existing setup-EET.command file in the game directory
        if os.path.exists(eet_cmd_target_fpath):
            os.remove(eet_cmd_target_fpath)
        # Copy the EET command file to the mod directory
        shutil.copy(eet_cmd_fpath, eet_cmd_target_fpath)


class EetAddBg1PathCmdFix(JengaCmdFix):
    """Add the BG1 path to the EET install command.

    This fix is necessary for EET installations to work correctly.

    """

    # args format taken from auto-installation section in EET documentation:
    # https://rawgit.com/K4thos/EET/master/EET/readme-EET.html

    def __init__(self, mod_name):
        """Initialize the EetAddBg1PathCmdFix object."""
        super().__init__(mod_name)
        self.fix_name = "EetAddBg1PathCmdFix"

    def apply(
        self,
        cmd: List[str],
        jenga_config: Birch,
        run_config: dict,
    ) -> List[str]:
        """Add the BG1 path to the EET install command."""
        # Add the BG1 path to the command
        try:
            bg1_path = jenga_config[CfgKey.BGIIEE_DIR_PATHS][
                CfgKey.BGEE_SOURCE
            ]
        except KeyError as e:
            raise ValueError(
                "BGIIEE_DIR_PATHS.BGEE_SOURCE not found in the Jenga config."
                "It must be set to the path of the BG1 directory in order for"
                " the EET installation to work correctly."
            ) from e
        cmd.append("--args-list")
        cmd.append("sp")
        cmd.append(f'"{bg1_path}"')
        return cmd


# ===== Crucible Fixes =====


class CrucibleMihModConflictIgnore(JengaPrePostFix):
    """Bypass the Crucible mod conflict with MIH_EQ.

    Edits the Crucible tp2 file to remove line that raise mod conflict and
    terminate on an existing installation of MIH_EQ (Made in Heaven: Encounters
    & Quests).

    """

    def __init__(self, mod_name):
        """Initialize the CrucibleMihModConflictIgnore object."""
        super().__init__(mod_name)
        self.fix_name = "CrucibleMihModConflictIgnore"

    LINE_TO_DELETE = (
        "REQUIRE_PREDICATE !FILE_EXISTS ~mih_eq/setup-mih_eq.tp2~ @3002"
    )
    SEARCH_TERM = "setup-mih_eq.tp2"

    def apply(
        self,
        mod_dir: str,
        mod_tp2_path: str,
        jenga_config: Birch,
        run_config: dict,
    ) -> None:
        """Bypass the Crucible mod conflict with MIH_EQ."""
        # Read the tp2 file in mod_tp2_path and remove all lines containing
        # the SEARCH_TERM
        with open(mod_tp2_path, "r") as f:
            lines = f.readlines()
        with open(mod_tp2_path, "w") as f:
            for line in lines:
                if self.SEARCH_TERM not in line:
                    f.write(line)


# ===== item_rev Fixes =====


class ItemRevAugmentWithIrRevised(JengaPrePostFix):
    """Augments item_rev with ir_revised."""

    def __init__(self, mod_name):
        """Initialize the ItemRevAugmentWithIrRevised object."""
        super().__init__(mod_name)
        self.fix_name = "ItemRevAugmentWithIrRevised"

    def apply(
        self,
        mod_dir: str,
        mod_tp2_path: str,
        jenga_config: Birch,
        run_config: dict,
    ) -> None:
        """Augments item_rev with ir_revised."""
        irr_info = get_mod_info("ir_revised")
        if irr_info is None:
            return
        irr_dpath = irr_info.extracted_dpath
        # merge the content of irr_dpath into mod_dir, with irr_dpath files
        # taking precedence over mod_dir files in case of conflicts.
        merge_dirs(irr_dpath, mod_dir)


# ===== spell_rev Fixes =====


class SpellRevAugmentWithSrRevised(JengaPrePostFix):
    """Augments spell_rev with sr_revised."""

    def __init__(self, mod_name):
        """Initialize the SpellRevAugmentWithSrRevised object."""
        super().__init__(mod_name)
        self.fix_name = "SpellRevAugmentWithSrRevised"

    def apply(
        self,
        mod_dir: str,
        mod_tp2_path: str,
        jenga_config: Birch,
        run_config: dict,
    ) -> None:
        """Augments spell_rev with sr_revised."""
        srr_info = get_mod_info("sr_revised")
        if srr_info is None:
            return
        srr_dpath = srr_info.extracted_dpath
        # merge the content of srr_dpath into mod_dir, with srr_dpath files
        # taking precedence over mod_dir files in case of conflicts.
        merge_dirs(srr_dpath, mod_dir)


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
    """Prevent EET_end failure by deleting badly formatter pdialog.2da lines.

    Fixes an issue for EET_END where installation fails due to
    badly formatted lines in pdialog.2da, probably caused by Glam's NPC Pack.
    See here for more:
    https://www.gibberlings3.net/forums/topic/36138-install-issue-with-some-mods-glams-thalantyr/

    """

    def __init__(self, mod_name):
        """Initialize the EetEndPdialogPartialLinesFix object."""
        super().__init__(mod_name)
        self.fix_name = "EetEndPdialogPartialLinesFix"

    def apply(
        self,
        mod_dir: str,
        mod_tp2_path: str,
        jenga_config: Birch,
        run_config: dict,
    ) -> None:
        """Fix the EET_END mod."""
        fix_pdialog_files_in_directory(run_config["game_install_dir"])


PRE_FIXES_REGISTRY: Dict[str, Sequence[JengaPrePostFix]] = {
    EET.lower(): [
        EetCopyEetCommandFilePreFix(EET),
    ],
    CRUCIBLE.lower(): [
        CrucibleMihModConflictIgnore(CRUCIBLE),
    ],
    ITEM_REV.lower(): [
        ItemRevAugmentWithIrRevised(ITEM_REV),
    ],
    SPELL_REV.lower(): [
        SpellRevAugmentWithSrRevised(SPELL_REV),
    ],
    EET_END.lower(): [
        EetEndPdialogPartialLinesFix(EET_END),
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
    uniform_name = get_mod_name_by_alias(mod_name)
    if uniform_name is None:
        uniform_name = mod_name.lower()
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
    uniform_name = get_mod_name_by_alias(mod_name)
    if uniform_name is None:
        uniform_name = mod_name.lower()
    return CMD_FIXES_REGISTRY.get(uniform_name, [])
