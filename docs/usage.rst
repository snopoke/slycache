=====
Usage
=====

To use slycache in a project::

    @slycache.cache_result(keys="{username}")
    def get_user_by_username(username):
        ...

    @slycache.cache_result(keys="{user_id}")
    def get_user_by_id(user_id):
        ...

    @slycache.cache_put(keys=[
        "{user.username}", "{user.user_id}"
    ])
    def save_user(user):
        ...

    @slycache.cache_remove(keys=[
        "{user.username}", "{user.user_id}"
    ])
    def delete_user(user):
        ...

Adapting a backend
==================

The backend interface required by ``slycache`` is very simple and is
defined by the :class:`slycache.CacheInterface` class.

Slycache comes with build in support for the following backends:

* TODO

To use any other backend you must define a class the conforms to the
:class:`slycache.CacheInterface` interface and register it with ``slycache``::

    from slycache import caches
    caches.register("default", MyCacheBackend())


Multiple backends
-----------------

Multiple backends can be registered::

    caches.register("default", RedisBackend(), default_timeout=60)
    caches.register("locmem", InMemoryBackend(), default_timeout=10)

Unless overridden via the `cache_name` paramter ``slycache`` will
always use the ``default`` cache. Using another registered cache is as easy as::

    @slycache.cache_result(keys="{path}", cache_name="locmem")
    def process_data(path):
        ...

To avoid having to specify the `cache_name` paramter on each call you can
also create a new cache object with the defaults preset::

    locmem = slycache.with_defaults(cache_name="locmem")

    @locmem.cache_result(keys="{path}")
    def process_data(path):
        ...

Namespaces
==========

Changing the defaults
=====================
The default ``slycache`` object comes with certain presets:

* cache name: ``default``
* timeout: the cache backend default
* namespace: the cache backend default

These can be overridden whenever a function is decorated for caching::

    @slycache.cache_result(
        keys="{id}",
        cache_name="other", timeout=5 * 60, namespace="data"
    )
    def get_data(id):
        ...

Alternately you can also create a new cache object with the defaults preset which
is useful if you want to reuse the same defaults on multiple functions::

    cache_with_my_defaults = slycache.with_defaults(
        cache_name="other", timeout=5 * 60, namespace="analytics"
    )

    @cache_with_my_defaults.cache_result(keys="user_{from}-{to}")
    def get_user_analytics(from, to):
        ...

    @cache_with_my_defaults.cache_result(keys="project_{from}-{to}")
    def get_project_analytics(from, to):
        ...

Standalone Usage
================
Slycache can also be used on standalone functions::

    @slycache.cache_result(keys="{arg1}_{arg2}", timeout=60)
    def expensive_function(arg1, arg2):
        ...
        return result

    result = expensive_function("user1", False)

Repeated calls to ``expensive_function`` will return the cached value
until the cache expires (after 60s)

You may clear the cache if necessary::

    expensive_function.clear_cache("user1", False)

