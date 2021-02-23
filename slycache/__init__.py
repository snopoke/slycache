"""Top-level package for slycache."""

__author__ = """snopoke"""
__version__ = '0.1.0'

from .slycache import caches, slycache, CacheInterface,InvalidCacheError, SlycacheException

__all__ = [
    "caches",
    "slycache",
    "CacheInterface",
    "SlycacheException",
    "InvalidCacheError",
]
