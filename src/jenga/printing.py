"""Printing utilities."""

from rich import print as rprint


JENG_CLR = "purple"
OPER_CLR = "deep_sky_blue1"
SCCS_CLR = "green"
NOTE_CLR = "yellow"
FAIL_CLR = "red"

JENGA_MARKER = f"[{JENG_CLR}]Jenga }}}}}} [/{JENG_CLR}]"
JENGA_FULL_LINE_MARKER = (
    f"[{JENG_CLR}] {{{{{{{{{{   Jenga   }}}}}}}}}} [/{JENG_CLR}]"
)
JENGA_GOODBYE_MARKER = (
    f"{JENGA_MARKER}[{JENG_CLR}] ---- Terminating. Goodbye! ---- {{{{"
)


def jprint(*args, **kwargs) -> None:
    """Print with Jenga marker."""
    rprint(JENGA_MARKER, *args, **kwargs)


def oper_print(*args, **kwargs) -> None:
    rprint(JENGA_MARKER, f"[{OPER_CLR}]", *args, **kwargs)


def sccs_print(*args, **kwargs) -> None:
    rprint(JENGA_MARKER, f"[{SCCS_CLR}]", *args, **kwargs)


def note_print(*args, **kwargs) -> None:
    rprint(JENGA_MARKER, f"[{NOTE_CLR}]", *args, **kwargs)


def fail_print(*args, **kwargs) -> None:
    rprint(JENGA_MARKER, f"[{FAIL_CLR}]", *args, **kwargs)


def full_line_marker() -> None:
    """Print full line Jenga marker."""
    rprint(JENGA_FULL_LINE_MARKER)

def print_goodbye() -> None:
    """Print goodbye message."""
    rprint(JENGA_GOODBYE_MARKER)
