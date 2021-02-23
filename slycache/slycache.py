"""Main module."""
import inspect
import logging
from abc import ABCMeta, abstractmethod
from dataclasses import dataclass, replace
from functools import wraps
from typing import Any, Protocol

log = logging.getLogger("slycache")


class SlycacheException(Exception):
    pass


class InvalidCacheError(SlycacheException):
    pass


class CacheInterface(Protocol):
    def get(self, key: str, default: Any = None) -> Any:
        raise NotImplementedError

    def set(self, key: str, value: Any, timeout: int = None):
        raise NotImplementedError

    def delete(self, key: str):
        raise NotImplementedError


DEFAULT_CACHE_ALIAS = 'default'


class StringKeyFormatter:
    @staticmethod
    def validate(template, fn):  # pylint: disable=unused-argument
        # TODO: parse key to check params  # pylint: disable=fixme
        # arg_names = inspect.getfullargspec(func).args
        # vary_on = [part.split('.') for part in vary_on]
        # vary_on = [(part[0], tuple(part[1:])) for part in vary_on]
        # for arg, attrs in vary_on:
        #     if arg not in arg_names:
        #         raise ValueError(
        #             'We cannot vary on "{}" because the function {} has '
        #             'no such argument'.format(arg, self.fn.__name__)
        #         )

        if template and not isinstance(template, str):
            raise ValueError(f"'key' must be None or a string: {template}")

    @staticmethod
    def format(prefix, key_template, fn, callargs) -> str:
        arg_names = inspect.getfullargspec(fn).args
        valid_args = {name: callargs[name] for name in arg_names}
        template_format = key_template.format(**valid_args)
        return template_format if prefix is None else f"{prefix}{template_format}"


@dataclass
class SlycacheConfig:
    cache: str = DEFAULT_CACHE_ALIAS
    timeout: int = 60
    prefix: str = None

    def validate(self):
        if not caches[self.cache]:
            raise InvalidCacheError(f"Slycache {self.cache} not configured")

    def get(self, key: str, default: Any = None) -> Any:
        return caches[self.cache].get(key, default)

    def set(self, key: str, value: Any):
        caches[self.cache].set(key, value, self.timeout)

    def delete(self, key: str):
        caches[self.cache].delete(key)


class CacheHolder:
    """
    A container to manage access to cache instances.
    """
    def __init__(self):
        self._caches = {}
        self._configs = {}

    def register(self,
                 alias: str,
                 cache_provider: CacheInterface,
                 default_timeout: int = None):
        if alias in self._caches:
            raise InvalidCacheError(f"Cache '{alias}' is already registered")
        self.replace(alias, cache_provider, default_timeout)

    def replace(self,
                alias: str,
                cache_provider: CacheInterface,
                default_timeout: int = None):
        self._caches[alias] = cache_provider
        self._configs[alias] = SlycacheConfig(alias, timeout=default_timeout)

    def get_config(self, alias):
        try:
            return self._configs[alias]
        except KeyError:
            raise InvalidCacheError(f"Slycache {alias} not configured")

    def __getitem__(self, alias):
        try:
            return self._caches[alias]
        except KeyError:
            raise InvalidCacheError(f"Slycache {alias} not configured")


caches = CacheHolder()


class CacheAction(metaclass=ABCMeta):
    @abstractmethod
    def __call__(self, cache_config, cache_key, func, callargs, result):
        pass


class PutAction(CacheAction):
    def __call__(self, cache_config, cache_key, func, callargs, result):
        value = self._get_value(func, callargs, result)
        if value is None:
            log.debug("ignoring None value, cache=%s, function=%s, key=%s",
                      cache_config.cache, func.__name__, cache_key)
            return

        cache_config.set(cache_key, value)
        log.debug("cache_set: cache=%s, function=%s, key=%s",
                  cache_config.cache, func.__name__, cache_key)

    def _get_value(self, func, callargs, result):
        raise NotImplementedError


class Slycache:
    def __init__(self,
                 cache_alias: str = DEFAULT_CACHE_ALIAS,
                 config: SlycacheConfig = None,
                 key_formatter=None):
        self.alias = cache_alias
        self._config = config
        self._key_formatter = key_formatter or StringKeyFormatter

    def with_config(self, **defaults):
        alias = defaults.pop("cache", self.alias)
        config = caches.get_config(alias)
        return Slycache(alias, replace(config, **defaults))

    def validate(self):
        if not self._config:
            self._config = caches.get_config(self.alias)
        self._config.validate()

    def cache_result(self, func=None, *, key):
        class Action(PutAction):
            def _get_value(self, func, callargs, result):
                return result

        return self._call(func, key, Action(), return_cached=True)

    def cache_put(self, func=None, *, key, cache_value=None):
        class Action(PutAction):
            def _get_value(self, func, callargs, result):
                if cache_value is not None:
                    return callargs[cache_value]

                callargs.pop('self', None)
                if len(callargs) == 1:
                    return list(callargs.values())[0]
                raise SlycacheException(
                    "'cache_value' must be provided for functions with multiple arguments"
                )

        return self._call(func, key, Action(), return_cached=False)

    def cache_remove(self, func=None, *, key):
        class Action(CacheAction):
            def __call__(self, cache_config, cache_key, func, callargs,
                         result):
                log.debug("cache_remove: cache=%s, function=%s, key=%s",
                          cache_config.cache, func.__name__, cache_key)
                cache_config.delete(cache_key)

        return self._call(func, key, Action(), return_cached=False)

    def _call(self, func, key, action: CacheAction, return_cached: bool):
        self.validate()

        def _decorator(func):
            if not callable(func):
                raise SlycacheException(
                    f"Decorator must be used on a function: {func!r}")

            self._key_formatter.validate(key, func)

            @wraps(func)
            def _inner(*args, **kwargs):
                bound_args = inspect.signature(func).bind(*args, **kwargs)
                cache_key = self._key_formatter.format(self._config.prefix,
                                                       key, func,
                                                       bound_args.arguments)
                if return_cached:
                    result = self._config.get(cache_key, default=Ellipsis)
                    if result is not Ellipsis:
                        return result
                    log.debug("cache miss: key=%s function=%s", cache_key,
                              func.__name__)
                result = func(*args, **kwargs)
                action(self._config, cache_key, func, bound_args.arguments,
                       result)
                return result

            return _inner

        return _decorator if func is None else _decorator(func)


slycache = Slycache()
