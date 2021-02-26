Welcome to slycache's documentation!
======================================

A caching API for Python that is loosely modeled after the Java Caching API (JSR107_).

.. _JSR107: https://docs.google.com/document/d/1YZ-lrH6nW871Vd9Z34Og_EqbX_kxxJi55UrSn4yL2Ak/edit

Basic Usage
-----------

Start by registering a cache backend::

    slycache.register_backend("default", my_cache_backend)

Define a key namespace::

    # define a key namespace
    user_cache = slycache.with_defaults(namespace="user")

Use the cache on methods and functions::

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

.. toctree::
   :maxdepth: 2
   :hidden:

   installation
   usage
   modules
   contributing
   authors
   history
