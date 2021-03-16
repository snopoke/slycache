from testil import assert_raises

from slycache import InvalidCacheError, caches
from tests.mock_cache import DictCache


def test_get_mising():
    with assert_raises(InvalidCacheError):
        caches["anything"]


def test_get_mising_proxy():
    with assert_raises(InvalidCacheError):
        caches.get_proxy("anything")


def test_deregister_missing():
    with assert_raises(InvalidCacheError):
        caches.deregister("anything")


def test_regiter_duplicate(clean_caches):
    clean_caches.register("default", DictCache("d"))
    with assert_raises(InvalidCacheError):
        clean_caches.register("default", DictCache("d"))
