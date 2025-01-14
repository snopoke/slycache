import enum
from typing import Final

DEFAULT_CACHE_NAME = "default"


class NotSet(enum.Enum):
    """Enum for use as default values for args, params that may also be None"""

    token = 0


NOTSET: Final = NotSet.token
