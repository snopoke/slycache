==========
Frameworks
==========

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
