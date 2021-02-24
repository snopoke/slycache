"""Test the slycache api"""
import uuid

import pytest

from slycache import caches, slycache
from slycache.slycache import DEFAULT_CACHE_ALIAS


def result_func(arg):  # pylint: disable=unused-argument
    return getattr(result_func, "return_value")


@pytest.mark.parametrize("cache, timeout, prefix", [
    (Ellipsis, Ellipsis, Ellipsis),
    ("default", Ellipsis, Ellipsis),
    ("other", Ellipsis, Ellipsis),
    (Ellipsis, 5, Ellipsis),
    (Ellipsis, Ellipsis, "all_your_base"),
])  # pylint: disable=too-many-locals
def test_cache_result_with_defaults(default_cache, other_cache, cache, timeout,
                                  prefix):
    _test_cache(default_cache, other_cache, cache, timeout, prefix, True)


@pytest.mark.parametrize("cache, timeout", [
    (Ellipsis, Ellipsis),
    ("default", Ellipsis),
    ("other", Ellipsis),
    (Ellipsis, 5),
    (Ellipsis, Ellipsis),
])  # pylint: disable=too-many-locals
def test_cache_result_overwrite_defaults(default_cache, other_cache, cache,
                                       timeout):
    _test_cache(default_cache, other_cache, cache, timeout, Ellipsis, False)


# pylint: disable=too-many-locals
def _test_cache(default_cache, other_cache, cache, timeout, prefix,
                override_at_class_level):
    result = uuid.uuid4().hex
    result_func.return_value = result

    cache_alias = cache if cache is not Ellipsis else DEFAULT_CACHE_ALIAS

    overrides = {}
    for k, v in {
            "cache_name": cache,
            "timeout": timeout,
            "prefix": prefix
    }.items():
        if v is not Ellipsis:
            overrides[k] = v

    custom_cache = slycache
    if override_at_class_level:
        custom_cache = slycache.with_defaults(**overrides)
        overrides = {}

    cached_func = custom_cache.cache_result(key="{arg}",
                                            **overrides)(result_func)

    arg = uuid.uuid4().hex
    assert cached_func(arg) == result
    if cache is Ellipsis or cache == DEFAULT_CACHE_ALIAS:
        cache_fixture = default_cache
    else:
        cache_fixture = other_cache

    expected_key = f"{prefix}{arg}" if prefix is not Ellipsis else arg
    entry = cache_fixture.get_entry(expected_key)
    assert cache_fixture.get(expected_key) == result, entry

    proxy = caches.get_proxy(cache_alias)
    expected_timeout = timeout if timeout is not Ellipsis else proxy.timeout
    assert entry.timeout == expected_timeout
