"""Top-level package for slycache.

.. autofunction::  slycache.Slycache.cache_result

|

.. autofunction::  slycache.Slycache.cache_put

|

.. autofunction::  slycache.Slycache.cache_remove

|

.. autofunction::  slycache.Slycache.caching

.. _with_defaults:

Creating caches with custom defaults
====================================

.. autofunction::  slycache.Slycache.with_defaults


.. _invocations:

Invocation Parameters
=====================

.. autoclass::  slycache.CacheResult

|

.. autoclass::  slycache.CachePut

|

.. autoclass::  slycache.CacheRemove


.. _cache_interface:

Cache Interface
===============

.. autoclass::  slycache.CacheInterface
    :members:

.. _key-generator:

Key Generators
==============
.. autoclass::  slycache.KeyGenerator
    :members:

|

"""

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
]
