========
slycache
========


.. image:: https://img.shields.io/pypi/v/slycache.svg
        :target: https://pypi.python.org/pypi/slycache
        :alt: PyPi version

.. image:: https://img.shields.io/pypi/pyversions/slycache
        :target: https://pypi.python.org/pypi/slycache
        :alt: Python versions

.. image:: https://github.com/snopoke/slycache/actions/workflows/ci.yml/badge.svg
        :target: https://github.com/snopoke/slycache/actions/workflows/ci.yml
        :alt: Build status

.. image:: https://readthedocs.org/projects/slycache/badge/?version=latest
        :target: https://slycache.readthedocs.io/en/latest/?badge=latest
        :alt: Documentation Status


A caching API for python loosely modeled after the Java Caching API (JSR107_).

.. _JSR107: https://docs.google.com/document/d/1YZ-lrH6nW871Vd9Z34Og_EqbX_kxxJi55UrSn4yL2Ak/edit


* Documentation: https://slycache.readthedocs.io.

.. note::
    This library is in Alpha stage and not ready for production use.

Basic Usage
-----------

Start by registering a cache backend:

.. code:: python

    slycache.register_backend("default", my_cache_backend)

Define a key namespace:

.. code:: python

    # define a key namespace
    user_cache = slycache.with_defaults(namespace="user")

Use the cache on methods and functions:

.. code:: python

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
