=====
Usage
=====

To use slycache in a project start by creating a namespaced cache::

    user_cache = slycache.with_defaults(namespace="user")

Then you can use the cache to decorate functions::

    @user_cache.cache_result("{username}")
    def get_user_by_username(username):
        ...

    @user_cache.cache_result("{user_id}")
    def get_user_by_id(user_id):
        ...

    @user_cache.cache_put([
        "{user.username}", "{user.user_id}"
    ])
    def save_user(user):
        ...

    @user_cache.cache_remove([
        "{user.username}", "{user.user_id}"
    ])
    def delete_user(user):
        ...

Adapting a backend
------------------

The backend interface required by ``slycache`` is very simple and is
defined by the :class:`slycache.CacheInterface` class.

Slycache comes with build in support for the following backends:

* TODO

To use any other backend you must define a class the conforms to the
:class:`slycache.CacheInterface` interface and register it with ``slycache``::

    import slycache
    slycache.register_backend("default", MyCacheBackend())


Multiple backends
~~~~~~~~~~~~~~~~~

Multiple backends can be registered::

    slycache.register_backend("default", RedisBackend(), default_timeout=60)
    slycache.register_backend("locmem", InMemoryBackend(), default_timeout=10)

Unless overridden via the `cache_name` paramter ``slycache`` will
always use the ``default`` cache. Using another registered cache is as easy as::

    @slycache.cache_result("{path}", cache_name="locmem")
    def process_data(path):
        ...

To avoid having to specify the `cache_name` paramter on each call you can
also create a new cache object with the defaults preset::

    locmem = slycache.with_defaults(cache_name="locmem")

    @locmem.cache_result("{path}")
    def process_data(path):
        ...

.. _namespaces:

Namespaces
----------
By default ``slycache`` will generate a namespace for keys based on the
function name and arguments. This ensures that there are no key
overlaps in the global namespace::

    @slycache.cache_result("{user.id},{game.id}")
    def compute_score(user, game):
        ...

    > compute_score(user1, game1)
    DEBUG   cache_miss: key=compute_score:user,game:user1,game1
    DEBUG   cache_set:  key=compute_score:user,game:user1,game1

Using the global namespace means that each decorated function will result
in unique keys. In order to make use of the power of ``slycache`` you must
define a custom namespace::

    game_cache = slycache.with_defaults(namespace="mario")

    @game_cache.cache_result("{user.id},{game.id}")
    def get_score(user, game):
        ...

    @game_cache.cache_put("{user.id},{game.id}", cache_value="score")
    def update_score(user, game, score):
        ...

    > update_score(user1, game1, 5)
    DEBUG   cache_set: key=mario:user1,game1

    > get_score(user1, game1)
    DEBUG   cache_hit: key=mario:user1,game1

In the example above you can see that even though we are decorating different
functions they are operating on the same set of cache keys because they
share a common namespace.

Changing the defaults
---------------------
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

    analytics_cache = slycache.with_defaults(
        cache_name="other", timeout=5 * 60, namespace="analytics"
    )

    @analytics_cache.cache_result("user_{from}-{to}")
    def get_user_analytics(from, to):
        ...

    @analytics_cache.cache_result("project_{from}-{to}")
    def get_project_analytics(from, to):
        ...

Clearing the cache
------------------
For standalone functions the cache may be cleared by calling ``clear_cache`` on
the decorated function::

    @slycache.cache_result("{user}_{role}", timeout=60)
    def expensive_function(user, role):
        ...
        return result

    > result = expensive_function("user1", "admin")
    DEBUG   cache_miss: key=...
    DEBUG   cache_set: key=...

    > expensive_function.clear_cache("user1", "admin")
    DEBUG   cache_remove: key=...

When using custom namespaces you can also decorate functions
with the ``cache_remove`` decorator::

    user_cache = slycache.with_defaults(namespace="user")

    @user_cache.cache_remove("{user.username"})
    def delete_user(user):
        ...

    > delete_user(user1)
    DEBUG cache_remove: key=user:wile.e.coyote

Cache Keys
----------

Keys are passed in to Slycache as string templates which are formatted as
[Python format strings](https://docs.python.org/3/library/string.html#format-string-syntax).

The template may reference any arguments passed to the decorated function:

.. code:: python

    class Project:
        @slycache.cache_result("{self.id}.{user.username}")
        def calculate_expenses(self, user: User):
            ...

The above example would generate keys as follows::

    [namespace]:1234.user1


Special type handling
~~~~~~~~~~~~~~~~~~~~~

``datetime`` values receive special treatment when they appear in keys.

Any timezone aware ``datetime`` object will be converted to UTC. This means that ``datetime`` objects
with different timezones but representing the same point in time will be serialized the same way.

Naive ``datetimes`` will be serialized without adjustment.

Advanced Usage
--------------

Multiple Cache Operations
~~~~~~~~~~~~~~~~~~~~~~~~~

TODO

Skip get
~~~~~~~~

TODO

