import pytest

from slycache import caches


@pytest.fixture(scope="module")
def service(request):
    service = getattr(request.module, "service_under_test", None)
    if service is None:
        pytest.skip('no service defined, skipping module: {}'.format(request.module))
    return service


def test_get(service):
    assert caches["default"].get("user:jack") is None
    service.get("jack")
    assert caches["default"].get("user:jack") == "jack"
    assert "other" not in caches or caches["other"].get("user:jack") is None

    caches["default"].set("user:jack", "jack black")
    assert service.get("jack") == "jack black"


def test_get_from_other(service):
    if "other" not in caches:
        pytest.skip("'other' cache not registered")

    assert caches["other"].get("user:jill") is None
    service.get_from_other("jill")
    assert caches["other"].get("user:jill") == "jill"
    assert caches["default"].get("user:jill") is None


def test_delete(service):
    test_get(service)
    "other" in caches and test_get_from_other(service)
    assert caches["default"].get("user:jack") == "jack black"
    assert "other" not in caches or caches["other"].get("user:jill") == "jill"

    service.delete("jack")
    assert caches["default"].get("user:jack") is None

    service.delete("jill")
    assert "other" not in caches or caches["other"].get("user:jill") is None
