import diskcache

from log import SCRIPT_DIR

CACHE = diskcache.Cache(SCRIPT_DIR.parent / "cache")
