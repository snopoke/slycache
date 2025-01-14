from typing import Any, Optional

from django.apps import AppConfig
from django.core.cache import BaseCache

from slycache import CacheInterface, slycache


class SlycacheConfig(AppConfig):
    name = "slycache"
    verbose_name = "Slycache"

    def ready(self):
        from django.conf import settings
        from django.core.cache import caches

        for name in settings.CACHES:
            cache = caches[name]
            print("Registering cache", name)
            slycache.register_backend(name, DjangoCacheAdapter(cache))


class DjangoCacheAdapter(CacheInterface):
    def __init__(self, delegate: BaseCache):
        self._delegate = delegate

    def get(self, key: str, default: Optional[Any] = None) -> Any:
        return self._delegate.get(key, default=default)

    def set(self, key: str, value: Any, timeout: Optional[int] = None):
        self._delegate.set(key, value, timeout=timeout)

    def delete(self, key: str):
        self._delegate.delete(key)
