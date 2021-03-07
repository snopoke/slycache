import pytest

from slycache import caches
from slycache.ext.flask import FlaskCacheAdapter, register_cache
from tests.ext.services import UserServiceSingle

try:
    from flask import Flask
    from flask_caching import Cache
except ImportError:
    pytestmark = pytest.mark.skip


@pytest.fixture(autouse=True, scope="module")
def flask_cache():
    app = Flask(__name__)
    app.config.from_mapping({"CACHE_TYPE": "SimpleCache"})
    cache = Cache(app)
    register_cache(cache)

    yield cache

    caches.deregister("default")


@pytest.fixture(autouse=True)
def clear_caches(flask_cache):  # pylint: disable=redefined-outer-name
    flask_cache.clear()


def test_flask_caches():
    assert {"default"} == set(caches.registered_names())
    assert isinstance(caches["default"], FlaskCacheAdapter)


def test_get():
    assert caches["default"].get("user:jack") is None
    UserServiceSingle.get("jack")
    assert caches["default"].get("user:jack") == "jack"

    caches["default"].set("user:jack", "jack black")
    assert UserServiceSingle.get("jack") == "jack black"


def test_delete():
    test_get()
    assert caches["default"].get("user:jack") == "jack black"

    UserServiceSingle.delete("jack")
    assert caches["default"].get("user:jack") is None
