========
slycache
========


.. image:: https://img.shields.io/pypi/v/slycache.svg
        :target: https://pypi.python.org/pypi/slycache

.. image:: https://github.com/snopoke/slycache/actions/workflows/ci.yml/badge.svg
        :target: https://github.com/snopoke/slycache/actions/workflows/ci.yml

.. image:: https://readthedocs.org/projects/slycache/badge/?version=latest
        :target: https://slycache.readthedocs.io/en/latest/?badge=latest
        :alt: Documentation Status


A caching API for python loosely modeled after the Java Caching API (JSR107_).

.. _JSR107: https://docs.google.com/document/d/1YZ-lrH6nW871Vd9Z34Og_EqbX_kxxJi55UrSn4yL2Ak/edit


* Documentation: https://slycache.readthedocs.io.


Features
--------

* Simple decorator based API
* Easily adapt any cache backend to work with slycache


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

For more advanced usage see the documentation: https://slycache.readthedocs.io
