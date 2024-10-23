"""Printing utilities."""
from rich import print as rprint

JENGA_MARKER = "[purple]Jenga }}} [/purple]"
JENGA_FULL_LINE_MARKER = "[purple] {{{{{{{{{{{   Jenga   }}}}}}}}}}} [/purple]"


def jprint(*args, **kwargs) -> None:
    """Print with Jenga marker."""
    rprint(JENGA_MARKER, *args, **kwargs)


def full_line_marker() -> None:
    """Print full line Jenga marker."""
    rprint(JENGA_FULL_LINE_MARKER)

