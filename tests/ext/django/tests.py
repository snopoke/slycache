import os

from slycache.ext.django.app import DjangoCacheAdapter
from tests.ext.services import UserServiceMultiple

# import test cases
from ..test_cases import *

django = pytest.importorskip("django")


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


# see ..test_cases.service fixture
service_under_test = UserServiceMultiple


def test_django_caches():
    assert {"default", "other"} == set(caches.registered_names())
    assert isinstance(caches["default"], DjangoCacheAdapter)
    assert isinstance(caches["other"], DjangoCacheAdapter)
