"""Jenga mod-specific fixes."""

# stdlib imports
from typing import Dict, List, Sequence

# 3rd party imports
from birch import Birch


class JengaFix:
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
        self.fix_name = "JengaFix"

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
        raise NotImplementedError("Fixes must implement the run method.")


class AnotherFineHellAfhvisFix(JengaFix):
    __doc__ = (
        JengaFix.__doc__
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
        import os

        afvis_path = os.path.join(mod_dir, self.SCR_DNAME, self.AFVIS_FNAME)
        rep_path = os.path.join(mod_dir, self.SCR_DNAME, self.REP_FNAME)
        # copy afvhvis.baf to afhjng.baf
        import shutil

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


# Mod Names
AFH = "AnotherFineHell"
AFH_NAMES = [
    AFH,
    "C#ANOTHERFINEHELL",
]


# Mod Alias Registry
MOD_ALIAS_REGISTRY: Dict[str, str] = {}
for n in AFH_NAMES:
    MOD_ALIAS_REGISTRY[n.lower()] = AFH.lower()


PRE_FIXES_REGISTRY: Dict[str, Sequence[JengaFix]] = {
    # AFH.lower(): [
    #     AnotherFineHellAfhvisFix(AFH),
    # ],
}


POST_FIXES_REGISTRY: Dict[str, Sequence[JengaFix]] = {}


def get_fixes_for_mod(mod_name: str, prefix: bool) -> Sequence[JengaFix]:
    """Get any fixes for the specified mod.

    Parameters
    ----------
    mod_name : str
        The name of the mod.
    prefix : bool
        Whether to get a prefix or postfix.

    Returns
    -------
    Sequece[JengaFix]
        A list of any fixes to apply before/after the specified mod.

    """
    uniform_name = MOD_ALIAS_REGISTRY.get(mod_name.lower(), mod_name.lower())
    registry = PRE_FIXES_REGISTRY if prefix else POST_FIXES_REGISTRY
    return registry.get(uniform_name, [])
