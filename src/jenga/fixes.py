"""Jenga mod-specific fixes."""

# 3rd party imports
from birch import Birch


class JengaFix:
    """A runnable object that fixes a specific mod issue during a Jenga build.

    Parameters
    ----------
    mod_name : str
        The name of the mod that the fix is for.

    """

    def __init__(self, mod_name):
        self.mod_name = mod_name

    def run(
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

    def run(
        self,
        mod_dir: str,
        mod_tp2_path: str,
        jenga_config: Birch,
        run_config: dict,
    ) -> None:
        pass
