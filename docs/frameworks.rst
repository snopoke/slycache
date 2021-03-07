==========
Frameworks
==========

.. _django:

Django
======

Automatically register all available Django caches with Slycache:

**settings.py**

.. code:: python

    INSTALLED_APPS = [
        "slycache.ext.django"
    ]

    CACHES = {
        "default": {...},
        "other": {...}
    }

.. _flask-cache:

Flask-Caching
=============

To use Slycache with `Flask-Caching <https://flask-caching.readthedocs.io/en/latest/>`_
simply register the configured cache as follows:

.. code:: python

    from flask import Flask
    from flask_caching import Cache
    from slycache.ext.flask import register_cache

    app = Flask(__name__)
    ...
    cache = Cache(app)
    register_cache(cache)
