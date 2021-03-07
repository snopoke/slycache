from slycache.ext.flask import FlaskCacheAdapter, register_cache
from tests.ext.services import UserServiceSingle

# import test cases
from ..test_cases import *

flask = pytest.importorskip("flask")
flask_caching = pytest.importorskip("flask_caching")


@pytest.fixture(autouse=True, scope="module")
def flask_cache():
    app = flask.Flask(__name__)
    app.config.from_mapping({"CACHE_TYPE": "SimpleCache"})
    cache = flask_caching.Cache(app)
    register_cache(cache)

    yield cache

    caches.deregister("default")


@pytest.fixture(autouse=True)
def clear_caches(flask_cache):  # pylint: disable=redefined-outer-name
    flask_cache.clear()


# see ..test_cases.service fixture
service_under_test = UserServiceSingle


def test_flask_caches():
    assert {"default"} == set(caches.registered_names())
    assert isinstance(caches["default"], FlaskCacheAdapter)
