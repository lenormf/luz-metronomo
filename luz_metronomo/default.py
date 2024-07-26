import os
from dataclasses import dataclass
from pathlib import Path


@dataclass
class Default:
    PROGRAM_NAME = "luz-metronomo"
    PROGRAM_DESCRIPTION = "Track the rate for electricity in Spain"

    XDG_DATA_HOME = Path(os.getenv("XDG_DATA_HOME") or Path.home() / ".local" / "share")
    PATH_DIR_USER_DATA = XDG_DATA_HOME / PROGRAM_NAME

    PATH_DIR_SYSTEM_CONFIG = Path("/etc") / PROGRAM_NAME

    XDG_CONFIG_HOME = Path(os.getenv("XDG_CONFIG_HOME") or Path.home() / ".config")
    PATH_DIR_USER_CONFIG = XDG_CONFIG_HOME / PROGRAM_NAME

    XDG_CACHE_HOME = Path(os.getenv("XDG_CACHE_HOME") or Path.home() / ".cache")
    PATH_DIR_USER_CACHE = XDG_CACHE_HOME / PROGRAM_NAME

    URL_API = "https://apidatos.ree.es/es/datos/mercados/precios-mercados-tiempo-real"
