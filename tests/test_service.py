"""Tests on a 'realistic' service class"""
import uuid
from dataclasses import dataclass
from typing import Dict, Tuple

import pytest

from slycache import CachePut, CacheRemove, CacheResult, slycache
from slycache.slycache import Slycache


def test_service_save_with_cache_value_param(default_cache):  # pylint: disable=unused-argument

    service = make_service(slycache)()
    user, data = _get_user_data()
    service.save_with_cache_value_param(user)
    assert service.data == data


def test_service_save_no_cache_value_param(default_cache):  # pylint: disable=unused-argument
    service = make_service(slycache)()
    user, data = _get_user_data()
    service.save_no_cache_value_param(user)
    assert service.data == data


def test_service_get_user_by_id_hit(default_cache):
    user, data = _get_user_data()
    default_cache.init(data)
    service = make_service(slycache)()

    assert service.data == {}  # will return None if data not in cache
    result = service.get_user_by_id(user.id)
    assert result == user


def test_service_get_user_by_id_miss(default_cache):
    user, data = _get_user_data()
    service = make_service(slycache)()

    result = service.get_user_by_username(user.id)
    assert result is None
    assert user.id not in default_cache

    service.data = data
    result = service.get_user_by_id(user.id)
    assert result == user
    assert user.id in default_cache


def test_service_delete(default_cache):
    user, data = _get_user_data()
    service = make_service(slycache)()

    service.save_with_cache_value_param(user)
    assert service.data == data
    assert user.id in default_cache

    service.delete(user)
    assert service.data == {}
    assert user.id not in default_cache


@pytest.mark.parametrize("func", ["update_user", "update_user_simple"])
def test_update_user(default_cache, func):
    user, data = _get_user_data()
    service = make_service(slycache)(data)

    old_username = user.username
    new_username = "new username"

    assert user.id not in default_cache
    assert old_username not in default_cache
    assert new_username not in default_cache

    getattr(service, func)(user.id, new_username)

    assert old_username not in default_cache
    assert user.id in default_cache
    assert new_username in default_cache


@pytest.mark.parametrize("func", ["save_with_multiple", "save_with_multiple_simple"])
def test_save_with_multiple(default_cache, func):
    user, _ = _get_user_data()
    service = make_service(slycache)()

    assert user.id not in default_cache
    assert user.username not in default_cache

    getattr(service, func)(user)

    assert user.id in default_cache
    assert user.username in default_cache


@pytest.mark.parametrize("func", ["delete_multiple", "delete_multiple_simple"])
def test_delete_multiple(default_cache, func):
    user, data = _get_user_data()
    service = make_service(slycache)(data)
    default_cache.init(data)

    assert user.id in default_cache
    assert user.username in default_cache

    getattr(service, func)(user)

    assert user.id not in default_cache
    assert user.username not in default_cache


def _get_user_data() -> Tuple["User", Dict]:
    user_id = uuid.uuid4().hex
    user = User(user_id, f"user_{user_id[:8]}")
    return user, {user_id: user, user.username: user}


@dataclass
class User:
    id: str
    username: str


def make_service(cache: Slycache):

    class Service:

        def __init__(self, data: Dict[str, User] = None):
            self.data = data or {}

        @cache.caching(
            result=[
                CacheResult(keys=["{user_id}"], skip_get=True),
                CacheResult(keys=["{username}"], skip_get=True),
            ]
        )
        def update_user(self, user_id: str, username: str):
            user = self.data[user_id]
            user.username = username
            self.data[user_id] = user
            return user

        @cache.cache_result(keys=["{user_id}", "{username}"], skip_get=True)
        def update_user_simple(self, user_id: str, username: str):
            user = self.data[user_id]
            user.username = username
            self.data[user_id] = user
            return user

        @cache.cache_result(keys="{user_id}")
        def get_user_by_id(self, user_id) -> User:
            try:
                return self.data[user_id]
            except KeyError:
                pass

        @cache.cache_result(keys="{username}")
        def get_user_by_username(self, username) -> User:
            try:
                return self.data[username]
            except KeyError:
                pass

        @cache.cache_put(keys="{user.id}", cache_value="user")
        def save_with_cache_value_param(self, user: User):
            self.data[user.id] = user
            self.data[user.username] = user

        @cache.caching(put=[
            CachePut(keys=["{user.id}"]),
            CachePut(keys=["{user.username}"]),
        ])
        def save_with_multiple(self, user: User):
            self.data[user.id] = user
            self.data[user.username] = user

        @cache.cache_put(keys=["{user.id}", "{user.username}"])
        def save_with_multiple_simple(self, user: User):
            self.data[user.id] = user
            self.data[user.username] = user

        @cache.cache_put(keys="{user.id}")
        def save_no_cache_value_param(self, user: User):
            self.data[user.id] = user
            self.data[user.username] = user

        @cache.cache_remove(keys="{user.id}")
        def delete(self, user: User):
            try:
                del self.data[user.id]
            except KeyError:
                pass

            try:
                del self.data[user.username]
            except KeyError:
                pass

        @cache.caching(remove=[
            CacheRemove(keys=["{user.id}"]),
            CacheRemove(keys=["{user.username}"]),
        ])
        def delete_multiple(self, user: User):
            try:
                del self.data[user.id]
            except KeyError:
                pass

            try:
                del self.data[user.username]
            except KeyError:
                pass

        @cache.cache_remove(keys=["{user.id}", "{user.username}"])
        def delete_multiple_simple(self, user: User):
            try:
                del self.data[user.id]
            except KeyError:
                pass

            try:
                del self.data[user.username]
            except KeyError:
                pass

    return Service
