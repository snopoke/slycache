import os

import pytest

from slycache import caches
from slycache.ext.django.app import DjangoCacheAdapter
from tests.ext.services import UserServiceMultiple

try:
    import django
except ImportError:
    pytestmark = pytest.mark.skip


@pytest.fixture(scope="module", autouse=True)
def with_django():
    if 'DJANGO_SETTINGS_MODULE' not in os.environ:
        os.environ.setdefault('DJANGO_SETTINGS_MODULE', "tests.ext.django.settings")

    django.setup()

    yield

    caches.deregister("default")
    caches.deregister("other")


@pytest.fixture(autouse=True)
def clear_caches():
    from django.core.cache import caches as django_caches  # pylint: disable=import-outside-toplevel
    for cache in django_caches.all():
        cache.clear()


def test_django_caches():
    assert {"default", "other"} == set(caches.registered_names())
    assert isinstance(caches["default"], DjangoCacheAdapter)
    assert isinstance(caches["other"], DjangoCacheAdapter)


def test_get_from_default():
    assert caches["default"].get("user:jack") is None
    UserServiceMultiple.get_from_default("jack")
    assert caches["default"].get("user:jack") == "jack"
    assert caches["other"].get("user:jack") is None

    caches["default"].set("user:jack", "jack black")
    assert UserServiceMultiple.get_from_default("jack") == "jack black"


def test_get_from_other():
    assert caches["other"].get("user:jill") is None
    UserServiceMultiple.get_from_other("jill")
    assert caches["other"].get("user:jill") == "jill"
    assert caches["default"].get("user:jill") is None


def test_delete():
    test_get_from_default()
    test_get_from_other()
    assert caches["default"].get("user:jack") == "jack black"
    assert caches["other"].get("user:jill") == "jill"

    UserServiceMultiple.delete_from_all("jack")
    assert caches["default"].get("user:jack") is None

    UserServiceMultiple.delete_from_all("jill")
    assert caches["other"].get("user:jill") is None
