import pytest

from slycache import Slycache, caches
from slycache.const import DEFAULT_CACHE_NAME, NOTSET
from slycache.slycache import ProxyWithDefaults
from tests.mock_cache import DictCache


@pytest.fixture
def default_cache():
    cache = DictCache(DEFAULT_CACHE_NAME)
    caches.replace(DEFAULT_CACHE_NAME, cache)
    yield cache
    caches.deregister(DEFAULT_CACHE_NAME)


@pytest.fixture
def other_cache():
    cache = DictCache("other")
    caches.replace("other", cache)
    yield cache
    caches.deregister("other")


@pytest.fixture
def clean_caches():
    for name in caches.registered_names():
        caches.deregister(name)

    assert caches._caches == {}  # pylint: disable=protected-access

    yield caches

    for name in caches.registered_names():
        caches.deregister(name)


@pytest.fixture
def clean_slate(clean_caches):
    default = Slycache()
    assert default._proxy == ProxyWithDefaults(DEFAULT_CACHE_NAME, NOTSET, NOTSET, False)  # pylint: disable=protected-access
    return default
