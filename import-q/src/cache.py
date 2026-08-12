import diskcache

from log import SCRIPT_DIR

CACHE = diskcache.Cache(SCRIPT_DIR.parent / "cache")

# dedicated cache for interactive review decisions, so we can iterate it safely
DECISIONS = diskcache.Cache(SCRIPT_DIR.parent / "cache-decisions")
