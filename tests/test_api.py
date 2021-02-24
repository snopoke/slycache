"""Test the slycache api"""
import uuid

import pytest

from slycache import caches, slycache
from slycache.slycache import DEFAULT_CACHE_NAME, NOTSET, ProxyWithDefaults


def result_func(arg):  # pylint: disable=unused-argument
    return getattr(result_func, "return_value")


@pytest.mark.parametrize(
    "cache, timeout, prefix", [
        (Ellipsis, Ellipsis, Ellipsis),
        ("default", Ellipsis, Ellipsis),
        ("other", Ellipsis, Ellipsis),
        (Ellipsis, 5, Ellipsis),
        (Ellipsis, Ellipsis, "all_your_base"),
    ]
)  # pylint: disable=too-many-locals
def test_cache_result_with_defaults(default_cache, other_cache, cache, timeout, prefix):
    _test_cache(default_cache, other_cache, cache, timeout, prefix, True)


@pytest.mark.parametrize(
    "cache, timeout", [
        (Ellipsis, Ellipsis),
        ("default", Ellipsis),
        ("other", Ellipsis),
        (Ellipsis, 5),
        (Ellipsis, Ellipsis),
    ]
)  # pylint: disable=too-many-locals
def test_cache_result_overwrite_defaults(default_cache, other_cache, cache, timeout):
    _test_cache(default_cache, other_cache, cache, timeout, Ellipsis, False)


# pylint: disable=too-many-locals
def _test_cache(default_cache, other_cache, cache, timeout, prefix, override_at_class_level):
    result = uuid.uuid4().hex
    result_func.return_value = result

    cache_alias = cache if cache is not Ellipsis else DEFAULT_CACHE_NAME

    overrides = {}
    for k, v in {"cache_name": cache, "timeout": timeout, "prefix": prefix}.items():
        if v is not Ellipsis:
            overrides[k] = v

    custom_cache = slycache
    if override_at_class_level:
        custom_cache = slycache.with_defaults(**overrides)
        overrides = {}

    cached_func = custom_cache.cache_result(keys="{arg}", **overrides)(result_func)

    arg = uuid.uuid4().hex
    assert cached_func(arg) == result
    if cache is Ellipsis or cache == DEFAULT_CACHE_NAME:
        cache_fixture = default_cache
    else:
        cache_fixture = other_cache

    expected_key = f"{prefix}{arg}" if prefix is not Ellipsis else arg
    entry = cache_fixture.get_entry(expected_key)
    assert cache_fixture.get(expected_key) == result, entry

    proxy = caches.get_default_proxy(cache_alias)
    expected_timeout = timeout if timeout is not Ellipsis else proxy.timeout
    assert entry.timeout == expected_timeout


def test_with_defaults_prefix(clean_slate):
    prefix = clean_slate.with_defaults(prefix="v1_")
    assert prefix._proxy == ProxyWithDefaults(  # pylint: disable=protected-access
        DEFAULT_CACHE_NAME,
        NOTSET,
        "v1_",
        False
    )


def test_with_defaults_name(clean_slate):
    other = clean_slate.with_defaults(cache_name="other")
    assert other._proxy == ProxyWithDefaults("other", NOTSET, NOTSET, False)  # pylint: disable=protected-access


def test_with_defaults_timeout(clean_slate):
    timeout = clean_slate.with_defaults(timeout=10)
    assert timeout._proxy == ProxyWithDefaults(  # pylint: disable=protected-access
        DEFAULT_CACHE_NAME,
        10,
        NOTSET,
        False
    )


def test_with_defaults_key_formatter(clean_slate):
    new_key_formatter = lambda x: x  # noqa
    fourth = clean_slate.with_defaults(key_formatter=new_key_formatter)
    assert fourth._key_formatter == new_key_formatter  # pylint: disable=protected-access


def test_with_defaults_carry_forward(clean_slate):
    key_formatter = lambda x: x  # noqa
    other = clean_slate.with_defaults(cache_name="other", timeout=2, prefix="v1_", key_formatter=key_formatter)
    assert other._proxy == ProxyWithDefaults("other", 2, "v1_", False)  # pylint: disable=protected-access
    assert other._key_formatter == key_formatter  # pylint: disable=protected-access

    new_key_formatter = lambda x: x + "1"  # noqa
    other1 = other.with_defaults(timeout=10, prefix="v2_", key_formatter=new_key_formatter)
    assert other1._proxy == ProxyWithDefaults("other", 10, "v2_", False)  # pylint: disable=protected-access
    assert other1._key_formatter == new_key_formatter  # pylint: disable=protected-access

    new_key_formatter = lambda x: x + "2"  # noqa
    default1 = other.with_defaults(
        cache_name=DEFAULT_CACHE_NAME, timeout=5, prefix="v3_", key_formatter=new_key_formatter
    )
    assert default1._proxy == ProxyWithDefaults(  # pylint: disable=protected-access
        DEFAULT_CACHE_NAME,
        5,
        "v3_",
        False
    )
    assert default1._key_formatter == new_key_formatter  # pylint: disable=protected-access
