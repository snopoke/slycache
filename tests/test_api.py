import uuid

import pytest

from slycache import CachePut, CacheResult
from slycache.const import DEFAULT_CACHE_NAME, NOTSET
from slycache.key_generator import StringFormatKeyGenerator
from slycache.slycache import ProxyWithDefaults, caches, slycache


def result_func(arg):  # pylint: disable=unused-argument
    return getattr(result_func, "return_value")


@pytest.mark.parametrize(
    "cache, timeout, namespace", [
        (Ellipsis, Ellipsis, Ellipsis),
        ("default", Ellipsis, Ellipsis),
        ("other", Ellipsis, Ellipsis),
        (Ellipsis, 5, Ellipsis),
        (Ellipsis, Ellipsis, "all_your_base"),
    ]
)  # pylint: disable=too-many-locals
def test_cache_result_with_defaults(default_cache, other_cache, cache, timeout, namespace):
    _test_cache(default_cache, other_cache, cache, timeout, namespace, True)


@pytest.mark.parametrize(
    "cache, timeout, namespace", [
        (Ellipsis, Ellipsis, Ellipsis),
        ("default", Ellipsis, Ellipsis),
        ("other", Ellipsis, Ellipsis),
        (Ellipsis, 5, Ellipsis),
        (Ellipsis, Ellipsis, "ns1"),
    ]
)  # pylint: disable=too-many-locals
def test_cache_result_overwrite_defaults(default_cache, other_cache, cache, timeout, namespace):
    _test_cache(default_cache, other_cache, cache, timeout, namespace, False)


# pylint: disable=too-many-locals
def _test_cache(default_cache, other_cache, cache, timeout, namespace, override_at_class_level):
    result = uuid.uuid4().hex
    result_func.return_value = result

    cache_alias = cache if cache is not Ellipsis else DEFAULT_CACHE_NAME

    overrides = {}
    for k, v in {"cache_name": cache, "timeout": timeout, "namespace": namespace}.items():
        if v is not Ellipsis:
            overrides[k] = v

    custom_cache = slycache
    if override_at_class_level:
        custom_cache = slycache.with_defaults(**overrides)
        overrides = {}

    cached_func = custom_cache.cache_result("{arg}", **overrides)(result_func)

    arg = uuid.uuid4().hex
    assert cached_func(arg) == result
    if cache is Ellipsis or cache == DEFAULT_CACHE_NAME:
        cache_fixture = default_cache
    else:
        cache_fixture = other_cache

    ns = namespace if namespace is not Ellipsis else None
    expected_key = StringFormatKeyGenerator.generate(ns, "{arg}", result_func, {"arg": arg})
    entry = cache_fixture.get_entry(expected_key)
    assert cache_fixture.get(expected_key) == result, entry

    proxy = caches.get_default_proxy(cache_alias)
    expected_timeout = timeout if timeout is not Ellipsis else proxy.timeout
    assert entry.timeout == expected_timeout


def test_with_defaults_namespace(clean_slate):
    namespace = clean_slate.with_defaults(namespace="v1_")
    assert namespace._proxy == ProxyWithDefaults(  # pylint: disable=protected-access
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


def test_with_defaults_key_generator(clean_slate):
    new_key_generator = lambda x: x  # noqa
    fourth = clean_slate.with_defaults(key_generator=new_key_generator)
    assert fourth._key_generator == new_key_generator  # pylint: disable=protected-access


def test_with_defaults_carry_forward(clean_slate):
    key_generator = lambda x: x  # noqa
    other = clean_slate.with_defaults(cache_name="other", timeout=2, namespace="v1_", key_generator=key_generator)
    assert other._proxy == ProxyWithDefaults("other", 2, "v1_", False)  # pylint: disable=protected-access
    assert other._key_generator == key_generator  # pylint: disable=protected-access

    new_key_generator = lambda x: x + "1"  # noqa
    other1 = other.with_defaults(timeout=10, namespace="v2_", key_generator=new_key_generator)
    assert other1._proxy == ProxyWithDefaults("other", 10, "v2_", False)  # pylint: disable=protected-access
    assert other1._key_generator == new_key_generator  # pylint: disable=protected-access

    new_key_generator = lambda x: x + "2"  # noqa
    default1 = other.with_defaults(
        cache_name=DEFAULT_CACHE_NAME, timeout=5, namespace="v3_", key_generator=new_key_generator
    )
    assert default1._proxy == ProxyWithDefaults(  # pylint: disable=protected-access
        DEFAULT_CACHE_NAME,
        5,
        "v3_",
        False
    )
    assert default1._key_generator == new_key_generator  # pylint: disable=protected-access


def test_clear_cache(default_cache):
    no_ns = slycache.with_defaults(namespace="")

    @no_ns.cache_result("{arg}")
    def expensive(arg):
        return arg

    assert expensive(1) == 1
    assert ":1" in default_cache

    expensive.clear_cache(1)
    assert ":1" not in default_cache


def test_clear_cache_multiple(default_cache, other_cache):
    no_ns = slycache.with_defaults(namespace="")

    @no_ns.caching(
        result=[
            CacheResult(["{arg}"], skip_get=True),
            CacheResult(["other_{arg}"], skip_get=True, cache_name="other"),
        ],
        put=[CachePut(["put_{arg}"]),
             CachePut(["other_put_{arg}"], cache_name="other")]
    )
    def expensive(arg):
        return arg

    assert expensive(1) == 1
    assert ":1" in default_cache
    assert ":other_1" in other_cache
    assert ":put_1" in default_cache
    assert ":other_put_1" in other_cache

    expensive.clear_cache(1)
    assert ":1" not in default_cache
    assert ":other_1" not in other_cache
    assert ":put_1" not in default_cache
    assert ":other_put_1" not in other_cache
