# slycache

A caching API for Python services that is loosely modeled after the Java
Caching API
([JSR107](https://docs.spring.io/spring-framework/reference/integration/cache/jsr-107.html)).

## Installation

Install Slycache using your favourite Python dependency management tool:

``` console
$ pip install slycache
```

## Set Up

Before you can use `slycache` you must register a cache backend.

Slycache comes with build in support for the following backends:

### Django

Automatically register all available Django caches with Slycache:

**settings.py**

```python
INSTALLED_APPS = [
    "slycache.ext.django"
]

CACHES = {
    "default": {...},
    "other": {...}
}
```

### Flask

To use Slycache with
[Flask-Caching](https://flask-caching.readthedocs.io/en/latest/) simply
register the configured cache as follows:

``` python
from flask import Flask
from flask_caching import Cache
from slycache.ext.flask import register_cache

app = Flask(__name__)
...
cache = Cache(app)
register_cache(cache)
```

### Custom Backends

To use any other backend you must define a class the conforms to the
`slycache.CacheInterface`{.interpreted-text role="class"} interface and
register it with `slycache`:

```python
import slycache
slycache.register_backend("default", MyCacheBackend())
```

### Multiple backends

Multiple backends can be registered:

```python
slycache.register_backend("default", RedisBackend(), default_timeout=60)
slycache.register_backend("locmem", InMemoryBackend(), default_timeout=10)
```

Unless overridden via the [cache_name]{.title-ref} parameter `slycache`
will always use the `default` cache. Using another registered cache is
as easy as:

```python
@slycache.cache_result("{path}", cache_name="locmem")
def process_data(path):
    ...
```

To avoid having to specify the [cache_name]{.title-ref} parameter on
each call you can also create a new cache object with the defaults
preset:

```python
locmem = slycache.with_defaults(cache_name="locmem")

@locmem.cache_result("{path}")
def process_data(path):
    ...
```

## Basic Usage

To use slycache in a project start by creating a namespaced cache:

```python
user_cache = slycache.with_defaults(namespace="user")
```

Then you can use the cache to decorate functions:

```python
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
```

## Namespaces

By default `slycache` will generate a namespace for keys based on the
function name and arguments. This ensures that there are no key overlaps
in the global namespace:

```python
@slycache.cache_result("{user.id},{game.id}")
def compute_score(user, game):
    ...

> compute_score(user1, game1)
DEBUG   cache_miss: key=compute_score:user,game:user1,game1
DEBUG   cache_set:  key=compute_score:user,game:user1,game1
```

Using the global namespace means that each decorated function will
result in unique keys. In order to make use of the power of `slycache`
you must define a custom namespace:

```python
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
```

In the example above you can see that even though we are decorating
different functions they are operating on the same set of cache keys
because they share a common namespace.

By default the maximum length of namespaces is 60 characters.

## Changing the defaults

The default `slycache` object comes with certain presets:

-   cache name: `default`
-   timeout: the cache backend default
-   namespace: the cache backend default

These can be overridden whenever a function is decorated for caching:

```python
@slycache.cache_result(
    keys="{id}",
    cache_name="other", timeout=5 * 60, namespace="data"
)
def get_data(id):
    ...
```

Alternately you can also create a new cache object with the defaults
preset which is useful if you want to reuse the same defaults on
multiple functions:

```python
analytics_cache = slycache.with_defaults(
    cache_name="other", timeout=5 * 60, namespace="analytics"
)

@analytics_cache.cache_result("user_{from}-{to}")
def get_user_analytics(from, to):
    ...

@analytics_cache.cache_result("project_{from}-{to}")
def get_project_analytics(from, to):
    ...
```

## Clearing the cache

For standalone functions the cache may be cleared by calling
`clear_cache` on the decorated function:

```python
@slycache.cache_result("{user}_{role}", timeout=60)
def expensive_function(user, role):
    ...
    return result

> result = expensive_function("user1", "admin")
DEBUG   cache_miss: key=...
DEBUG   cache_set: key=...

> expensive_function.clear_cache("user1", "admin")
DEBUG   cache_remove: key=...
```

When using custom namespaces you can also decorate functions with the
`cache_remove` decorator:

```python
user_cache = slycache.with_defaults(namespace="user")

@user_cache.cache_remove("{user.username"})
def delete_user(user):
    ...

> delete_user(user1)
DEBUG cache_remove: key=user:wile.e.coyote
```

## Cache Keys

Keys are passed in to Slycache as string templates which are formatted
as [Python format
strings](https://docs.python.org/3/library/string.html#format-string-syntax).

The template may reference any arguments passed to the decorated
function:

``` python
class Project:
    @slycache.cache_result("{self.id}.{user.username}")
    def calculate_expenses(self, user: User):
        ...
```

The above example would generate keys as follows:

    [namespace]:1234.user1

Keys longer than 250 characters (excluding the namespace) will be
converted into a base64 encoded SHA1 hash.

### Type handling

Accepted types for keys are:

-   str, int, float, Decimal, bytes, bool
-   list, dict, set, frozenset
-   date, time (converted to ISO format)
-   timezone naive datetime (converted to ISO format)
-   timezone aware datetime (translated to UTC and then converted to ISO
    format)
-   timedelta (converted to total seconds)

## Advanced Usage

### Multiple Cache Operations

In certain circumstances it may be desirable to use multiple decorators
on a single function, for example, caching the same value in multiple
caches.

This can be accomplished by using the `caching` decorator:

``` python
slycache.register_backend("locmem", InMemoryBackend(), default_timeout=10)
slycache.register_backend("redis", RedisBackend(), default_timeout=60)

user_cache = slycache.with_defaults(namespace="user")

class User:
    @user_cache.caching(
        CacheResult("{username}", cache_name="locmem"),
        CacheResult("{username}", cache_name="redis")
    )
    @staticmethod
    def get_by_username(username):
        ...
        return user

    @user_cache.caching(
        CacheResult("{id}", cache_name="locmem"),
        CacheResult("{id}", cache_name="redis")
    )
    @staticmethod
    def get_by_id(id):
        ...
        return user

    @user_cache.caching(
        CachePut(["{self.username}", "{self.id}"], cache_value="self", cache_name="locmem"),
        CachePut(["{self.username}", "{self.id}"], cache_value="self", cache_name="redis")
    )
    def save(self):
        ...
```

### Skip get

Result caching can also be done on functions where the cache check
should be skipped and the decorated function should always be executed,
for example update functions:

``` python
@user_cache.cache_result("{username}", skip_get=True)
def activate_user(username):
    user = get_user(username)
    user.is_active = True
    user.save()
    return user
```
