from typing import Any, Optional

from flask_caching import BaseCache

import slycache
from slycache import CacheInterface


def register_cache(cache, name="default"):
    slycache.register_backend(name, FlaskCacheAdapter(cache))


class FlaskCacheAdapter(CacheInterface):

    def __init__(self, delegate: BaseCache):  # pylint: disable=super-init-not-called
        self._delegate = delegate

    def get(self, key: str, default: Optional[Any] = None) -> Any:
        value = self._delegate.get(key)
        return default if value is None else value

    def set(self, key: str, value: Any, timeout: Optional[int] = None):
        self._delegate.set(key, value, timeout=timeout)

    def delete(self, key: str):
        self._delegate.delete(key)
