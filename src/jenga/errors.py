"""Custom exceptions for the package."""


class ConfigurationError(Exception):
    """Configuration error."""


class IllformedModArchiveError(Exception):
    """Ill-formed mod archive error."""


class IllformedExtractedModDirError(Exception):
    """Ill-formed extracted mod directory error."""
