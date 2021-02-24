__author__ = """snopoke"""
__version__ = '0.1.0'

from .exceptions import InvalidCacheError, SlycacheException
from .interface import CacheInterface, KeyGenerator
from .invocations import CachePut, CacheRemove, CacheResult
from .slycache import Slycache, caches, slycache

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
]
