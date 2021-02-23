"""Test the slycache api"""
import uuid

import pytest

from slycache import slycache, caches
from slycache.slycache import DEFAULT_CACHE_ALIAS


def result_func(arg):
    return getattr(result_func, "_return")


@pytest.mark.parametrize("cache, timeout, prefix", [
    (Ellipsis, Ellipsis, Ellipsis),
    ("default", Ellipsis, Ellipsis),
    ("other", Ellipsis, Ellipsis),
    (Ellipsis, 5, Ellipsis),
    (Ellipsis, Ellipsis, "all_your_base"),
])
def test_cache_result_with_config(default_cache, other_cache, cache, timeout, prefix):
    result = uuid.uuid4().hex
    result_func._return = result

    cache_alias = cache if cache is not Ellipsis else DEFAULT_CACHE_ALIAS

    config = {}
    for k, v in {"cache": cache, "timeout": timeout, "prefix": prefix}.items():
        if v is not Ellipsis:
            config[k] = v

    custom_cache = slycache.with_config(**config)
    cached_func = custom_cache.cache_result(key="{arg}")(result_func)

    arg = uuid.uuid4().hex
    assert cached_func(arg) == result
    if cache is Ellipsis or cache == DEFAULT_CACHE_ALIAS:
        cache_fixture = default_cache
    else:
        cache_fixture = other_cache

    expected_key = f"{prefix}{arg}" if prefix is not Ellipsis else arg
    entry = cache_fixture.get_entry(expected_key)
    assert cache_fixture.get(expected_key) == result, entry

    cache_config = caches.get_config(cache_alias)
    expected_timeout = timeout if timeout is not Ellipsis else cache_config.timeout
    assert entry.timeout == expected_timeout
