import slycache
from slycache import CacheRemove

user_cache = slycache.with_defaults(namespace="user")


class UserServiceSingle:

    @staticmethod
    @user_cache.cache_result("{username}")
    def get(username):
        return username

    @staticmethod
    @user_cache.cache_remove("{username}")
    def delete(username):
        pass


class UserServiceMultiple:

    @staticmethod
    @user_cache.cache_result("{username}")
    def get(username):
        return username

    @staticmethod
    @user_cache.cache_result("{username}", cache_name="other")
    def get_from_other(username):
        return username

    @staticmethod
    @user_cache.caching(CacheRemove(["{username}"]), CacheRemove(["{username}"], cache_name="other"))
    def delete(username):
        pass
