import enum
from typing import Final

DEFAULT_CACHE_NAME = 'default'


class NotSet(enum.Enum):
    token = 0


NOTSET: Final = NotSet.token
