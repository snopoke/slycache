import os
import pytest

from slycache import CacheRemove, caches, slycache


try:
    import django
except ImportError:
    pytestmark = pytest.mark.skip


@pytest.fixture(scope="module", autouse=True)
def with_django():
    if 'DJANGO_SETTINGS_MODULE' not in os.environ:
        os.environ.setdefault('DJANGO_SETTINGS_MODULE', "tests.ext.django.settings")

    django.setup()


@pytest.fixture(autouse=True)
def clear_caches():
    from django.core.cache import caches as django_caches  # pylint: disable=import-outside-toplevel
    for cache in django_caches.all():
        cache.clear()


def test_django_caches():
    assert {"default", "other"} == set(caches.registered_names())


def test_get_from_default():
    UserService.get_from_default("jack")
    assert caches["default"].get("user:jack") == "jack"
    assert caches["other"].get("user:jack") is None

    caches["default"].set("user:jack", "jack black")
    assert UserService.get_from_default("jack") == "jack black"


def test_get_from_other():
    UserService.get_from_other("jill")
    assert caches["other"].get("user:jill") == "jill"
    assert caches["default"].get("user:jill") is None


def test_delete():
    test_get_from_default()
    test_get_from_other()
    assert caches["default"].get("user:jack") == "jack black"
    assert caches["other"].get("user:jill") == "jill"

    UserService.delete_from_all("jack")
    assert caches["default"].get("user:jack") is None

    UserService.delete_from_all("jill")
    assert caches["other"].get("user:jill") is None


user_cache = slycache.with_defaults(namespace="user")


class UserService:

    @staticmethod
    @user_cache.cache_result("{username}")
    def get_from_default(username):
        return username

    @staticmethod
    @user_cache.cache_result("{username}", cache_name="other")
    def get_from_other(username):
        return username

    @staticmethod
    @user_cache.caching(remove=[CacheRemove(["{username}"]), CacheRemove(["{username}"], cache_name="other")])
    def delete_from_all(username):
        pass
