"""Top-level package for slycache.

.. _key-generator:

Key Generators
==============
something

.. autofunction::  slycache.Slycache.cache_result

|

.. autofunction::  slycache.Slycache.cache_put

|

.. autofunction::  slycache.Slycache.cache_remove

|

.. autofunction::  slycache.Slycache.caching

|

.. autofunction::  slycache.Slycache.with_defaults

|

.. autoclass::  slycache.CacheResult

|

.. autoclass::  slycache.CachePut

|

.. autoclass::  slycache.CacheRemove

"""

__author__ = """snopoke"""
__version__ = '0.1.0'

from .exceptions import InvalidCacheError, SlycacheException
from .interface import CacheInterface
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
]
