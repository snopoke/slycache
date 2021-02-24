import pytest

from slycache import Slycache, caches
from slycache.const import DEFAULT_CACHE_NAME
from tests.mock_cache import DictCache


@pytest.fixture
def default_cache():
    cache = DictCache(DEFAULT_CACHE_NAME)
    caches.replace(DEFAULT_CACHE_NAME, cache)
    return cache


@pytest.fixture
def other_cache():
    cache = DictCache("other")
    caches.replace("other", cache)
    return cache


@pytest.fixture
def clean_slate():
    for name in caches.registered_names():
        caches.deregister(name)

    assert caches._caches == {}  # pylint: disable=protected-access

    default = Slycache()
    assert default._proxy is None  # pylint: disable=protected-access
    return default
