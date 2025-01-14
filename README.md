# slycache

[![PyPi version](https://img.shields.io/pypi/v/slycache.svg)](https://pypi.python.org/pypi/slycache)

[![Python versions](https://img.shields.io/pypi/pyversions/slycache)](https://pypi.python.org/pypi/slycache)

[![Build status](https://github.com/snopoke/slycache/actions/workflows/ci.yml/badge.svg)](https://github.com/snopoke/slycache/actions/workflows/ci.yml)

A caching API for python loosely modeled after the Java Caching API
([JSR107](https://docs.google.com/document/d/1YZ-lrH6nW871Vd9Z34Og_EqbX_kxxJi55UrSn4yL2Ak/edit)).

-   Documentation: <https://snopoke.github.io/slycache/>.


## Basic Usage

Start by registering a cache backend:

``` python
slycache.register_backend("default", my_cache_backend)
```

Define a key namespace:

``` python
# define a key namespace
user_cache = slycache.with_defaults(namespace="user")
```

Use the cache on methods and functions:

``` python
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

For more advanced usage see the documentation:
<https://snopoke.github.io/slycache/>
