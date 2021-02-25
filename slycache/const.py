import enum
import sys

_native_final = sys.version_info[:2] >= (3, 8)
if _native_final:
    from typing import Final
else:
    from typing import TypeVar
    Final = TypeVar("Final")


DEFAULT_CACHE_NAME = 'default'


class NotSet(enum.Enum):
    """Enum for use as default values for args, params that may also be None"""
    token = 0


NOTSET: Final = NotSet.token
