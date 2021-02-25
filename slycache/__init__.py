__author__ = """snopoke"""
__version__ = '0.1.0'

from .exceptions import InvalidCacheError, SlycacheException
from .interface import CacheInterface, KeyGenerator
from .invocations import CachePut, CacheRemove, CacheResult
from .slycache import Slycache, caches, slycache

register_backend = slycache.register_backend
with_defaults = slycache.with_defaults
cache_result = slycache.cache_result
cache_put = slycache.cache_put
cache_remove = slycache.cache_remove
caching = slycache.caching

__all__ = [
    "caches",
    "slycache",
    "Slycache",
    "CacheResult",
    "CachePut",
    "CacheRemove",
    "CacheInterface",
    "SlycacheException",
    "InvalidCacheError",
    "KeyGenerator",
    "register_backend",
]
