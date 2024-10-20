"""Configuration control for jenga."""

import birch


class CfgKey:
    """Configuration keys for jenga."""
    BGIIEE_DIR_PATH = "BGIIEE_DIR_PATH"
    MOD_CACHE_DIR_PATH = "MOD_CACHE_DIR_PATH"
    DEFAULT_LANGUAGE = "DEFAULT_LANGUAGE"
    NUM_RETRIES = "NUM_RETRIES"
    STOP_ON_WARNING = "STOP_ON_WARNING"
    STOP_ON_ERROR = "STOP_ON_ERROR"


CFG = birch.Birch(
    namespace="jenga",
    defaults={
        CfgKey.DEFAULT_LANGUAGE: "en",
        CfgKey.NUM_RETRIES: 0,
        CfgKey.STOP_ON_WARNING: False,
        CfgKey.STOP_ON_ERROR: True,
    },
    default_casters={
        CfgKey.NUM_RETRIES: int,
        CfgKey.STOP_ON_WARNING: bool,
        CfgKey.STOP_ON_ERROR: bool,
    },
)


BGIIEE_DIR_PATH = CFG[CfgKey.BGIIEE_DIR_PATH]
MOD_CACHE_DIR_PATH = CFG[CfgKey.MOD_CACHE_DIR_PATH]
DEFAULT_LANGUAGE = CFG[CfgKey.DEFAULT_LANGUAGE]
NUM_RETRIES = CFG[CfgKey.NUM_RETRIES]
STOP_ON_WARNING = CFG[CfgKey.STOP_ON_WARNING]
STOP_ON_ERROR = CFG[CfgKey.STOP_ON_ERROR]
