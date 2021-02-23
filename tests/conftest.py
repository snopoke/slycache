import pytest

from slycache.slycache import DEFAULT_CACHE_ALIAS, caches
from tests.mock_cache import DictCache


@pytest.fixture
def default_cache():
    cache = DictCache(DEFAULT_CACHE_ALIAS)
    caches.replace(DEFAULT_CACHE_ALIAS, cache)
    return cache


@pytest.fixture
def other_cache():
    cache = DictCache("other")
    caches.replace("other", cache)
    return cache
