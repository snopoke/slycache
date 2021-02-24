"""Main module"""
import enum
import inspect
import logging
from abc import ABCMeta, abstractmethod
from dataclasses import dataclass, replace
from functools import cached_property, wraps
from typing import Any, Callable, Final, List, Optional, Protocol, Union

log = logging.getLogger("slycache")


class SlycacheException(Exception):
    pass


class InvalidCacheError(SlycacheException):
    pass


class NotSet(enum.Enum):
    token = 0


NOTSET: Final = NotSet.token


class CacheInterface(Protocol):

    def get(self, key: str, default: Any = None) -> Any:
        raise NotImplementedError

    def set(self, key: str, value: Any, timeout: int = None):
        raise NotImplementedError

    def delete(self, key: str):
        raise NotImplementedError


DEFAULT_CACHE_NAME = 'default'


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


@dataclass(frozen=True)
class ProxyWithDefaults:
    """Proxy class that holds defaults for caching.
    This class keeps a reference to the cache provider
    via the cache name.
    """
    cache_name: str
    timeout: Union[int, NotSet] = NOTSET
    prefix: Union[str, NotSet] = NOTSET
    _merged: bool = False

    @property
    def key_prefix(self):
        return None if self.prefix is NOTSET else self.prefix

    def merge_with_global_defaults(self):
        if self._merged:
            return self

        defaults = caches.get_default_proxy(self.cache_name)
        updates = {"_merged": True}
        if self.timeout is NOTSET:
            updates["timeout"] = defaults.timeout
        if self.prefix is NOTSET:
            updates["prefix"] = defaults.prefix

        return replace(self, **updates)

    def validate(self):
        if not caches[self.cache_name]:
            raise InvalidCacheError(f"Slycache {self.cache_name} not configured")

    def get(self, key: str, default: Any = None) -> Any:
        return caches[self.cache_name].get(key, default)

    def set(self, key: str, value: Any):
        timeout = None if self.timeout is NOTSET else self.timeout
        caches[self.cache_name].set(key, value, timeout)

    def delete(self, key: str):
        caches[self.cache_name].delete(key)


class CacheHolder:
    """
    A container to manage access to cache instances.
    """

    def __init__(self):
        self._caches = {}
        self._proxies = {}

    def register(
        self,
        name: str,
        cache_provider: CacheInterface,
        default_timeout: int = None,
        default_prefix: Union[str, NotSet] = NOTSET
    ):
        if name in self._caches:
            raise InvalidCacheError(f"Cache '{name}' is already registered")
        self.replace(name, cache_provider, default_timeout, default_prefix)

    def replace(
        self,
        name: str,
        cache_provider: CacheInterface,
        default_timeout: int = None,
        default_prefix: Union[str, NotSet] = NOTSET
    ):
        self._caches[name] = cache_provider
        self._proxies[name] = ProxyWithDefaults(name, timeout=default_timeout, prefix=default_prefix, _merged=True)

    def deregister(self, name: str):
        try:
            del self._caches[name]
            del self._proxies[name]
        except KeyError:
            raise InvalidCacheError(f"Slycache {name} not configured")

    def registered_names(self):
        return list(self._caches)

    def get_default_proxy(self, name):
        try:
            return self._proxies[name]
        except KeyError:
            raise InvalidCacheError(f"Slycache {name} not configured")

    def __getitem__(self, name):
        try:
            return self._caches[name]
        except KeyError:
            raise InvalidCacheError(f"Slycache {name} not configured")


caches = CacheHolder()


@dataclass
class CacheInvocation:
    keys: List[str]
    cache_name: Optional[str] = None

    def get_updated_proxy(self, proxy: ProxyWithDefaults) -> ProxyWithDefaults:
        overrides = self._get_overrides()
        if overrides:
            return replace(proxy, **overrides)
        return proxy

    def _get_overrides(self) -> dict:
        overrides = {}
        if self.cache_name:
            overrides["cache_name"] = self.cache_name
        return overrides


@dataclass
class CacheResult(CacheInvocation):
    """
    Data class used to contain the parameters for a ``cache_result`` operation.

    See also:
        :meth:`slycache.Slycache.cache_result`
    """
    timeout: Union[int, NotSet] = NOTSET
    skip_get: bool = False

    def _get_overrides(self) -> dict:
        overrides = super()._get_overrides()
        if self.timeout is not NOTSET:
            overrides["timeout"] = self.timeout
        return overrides


@dataclass
class CachePut(CacheInvocation):
    """
    Data class used to contain the parameters for a ``cache_put`` operation.

    See also:
        :meth:`slycache.Slycache.cache_put`
    """
    cache_value: Optional[str] = None
    timeout: Union[int, NotSet] = NOTSET

    @property
    def skip_get(self):
        return True

    def _get_overrides(self) -> dict:
        overrides = super()._get_overrides()
        if self.timeout is not NOTSET:
            overrides["timeout"] = self.timeout
        return overrides


class CacheRemove(CacheInvocation):
    """
    Data class used to contain the parameters for a ``cache_remove`` operation.

    See also:
        :meth:`slycache.Slycache.cache_remove`
    """

    @property
    def skip_get(self):
        return True


class CacheAction(metaclass=ABCMeta):

    def __init__(self, invocation: CacheInvocation):
        self.invocation = invocation
        self._proxy = None
        self._formatted_keys = None

    @property
    def proxy(self):
        if not self._proxy:
            raise SlycacheException("proxy not set on action")
        return self._proxy

    def set_proxy(self, proxy):
        self._proxy = self.invocation.get_updated_proxy(proxy)

    @property
    def formatted_keys(self):
        return self._formatted_keys

    @formatted_keys.setter
    def formatted_keys(self, keys):
        self._formatted_keys = keys

    def call(self, cache_key, func, callargs, result):
        self._call(cache_key, func, callargs, result)

    @abstractmethod
    def _call(self, cache_key, func, callargs, result):
        raise NotImplementedError


class CacheResultAction(CacheAction):

    def _call(self, cache_key, func, callargs, result):
        value = self._get_value(func, callargs, result)
        if value is None:
            log.debug(
                "ignoring None value, cache=%s, function=%s, key=%s", self.proxy.cache_name, func.__name__,
                cache_key
            )
            return

        self.proxy.set(cache_key, value)
        log.debug("cache_set: cache=%s, function=%s, key=%s", self.proxy.cache_name, func.__name__, cache_key)

    def _get_value(self, func, callargs, result):  # pylint: disable=unused-argument,no-self-use
        return result


class CachePutAction(CacheResultAction):

    def _get_value(self, func, callargs, result):
        if self.invocation.cache_value is not None:
            return callargs[self.invocation.cache_value]

        args = list(callargs)
        if len(args) == 1:
            return callargs[args[0]]
        if len(args) == 2 and args[0] == "self":
            return callargs[args[1]]
        raise SlycacheException("'cache_value' must be provided for functions with multiple arguments")


class CacheRemoveAction(CacheAction):

    def _call(self, cache_key, func, callargs, result):
        log.debug("cache_remove: cache=%s, function=%s, key=%s", self.proxy.cache_name, func.__name__, cache_key)
        self.proxy.delete(cache_key)


class CombinedAction:

    def __init__(self, func: Callable, actions: List[CacheAction], key_formatter, proxy: ProxyWithDefaults):
        self._func = func
        self._actions = actions
        self._key_formatter = key_formatter

        for action in self._actions:
            action.set_proxy(proxy)

    def validate(self):
        self.skip_get  # noqa, pylint: disable=pointless-statement
        for action in self._actions:
            for key in action.invocation.keys:
                self._key_formatter.validate(key, self._func)

    @cached_property
    def skip_get(self):
        skip_get = {action.invocation.skip_get for action in self._actions}
        if len(skip_get) > 1:
            raise SlycacheException("All actions agree on 'skip_get'")
        return list(skip_get)[0]

    def get_cached(self, callargs, default=Ellipsis):
        if self.skip_get:
            return default

        for action in self._actions:
            for key in self.get_action_keys(action, callargs):
                result = action.proxy.get(key, default=default)
                if result is not default:
                    log.debug(
                        "cache hit: cache=%s key=%s function=%s", action.proxy.cache_name, key, self._func.__name__
                    )
                    return result
                log.debug(
                    "cache miss: cache=%s key=%s function=%s", action.proxy.cache_name, key, self._func.__name__
                )
        return default

    def get_action_keys(self, action: CacheAction, callargs):
        if not action.formatted_keys:
            keys = [
                self._key_formatter.format(action.proxy.key_prefix, key, self._func, callargs)
                for key in action.invocation.keys
            ]
            action.formatted_keys = keys
        return action.formatted_keys

    def call(self, result, callargs):
        for action in self._actions:
            for key in self.get_action_keys(action, callargs):
                action.call(key, self._func, callargs, result)


class Slycache:

    def __init__(self, proxy: ProxyWithDefaults = None, key_formatter=None):
        self._proxy = proxy
        self._key_formatter = key_formatter or StringKeyFormatter
        self._merged = not self._proxy

    def with_defaults(self, **defaults):
        cache_name = defaults.pop("cache_name", None)
        key_formatter = defaults.pop("key_formatter", self._key_formatter)
        if not cache_name and self._proxy:
            new_proxy = replace(self._proxy, **defaults)
        else:
            new_proxy = ProxyWithDefaults(cache_name or DEFAULT_CACHE_NAME, **defaults)

        return Slycache(new_proxy, key_formatter)

    @property
    def _cache_proxy(self):
        """Lazy initializer for proxy"""
        if not self._proxy:
            self._proxy = caches.get_default_proxy(DEFAULT_CACHE_NAME)

        return self._proxy.merge_with_global_defaults()

    def validate(self):
        self._cache_proxy.validate()

    def cache_result(
        self,
        func: Optional[Callable] = None,
        *,
        keys: Union[str, List[str]],
        cache_name: Optional[str] = None,
        timeout: Union[int, NotSet] = NOTSET,
        skip_get: bool = False
    ):
        """
        This is a function level decorator function used to mark methods whose returned value is cached,
        using a key generated from the method parameters, and returned from the cache on later calls
        with the same parameters.

        When a method decorated with ``cache_result`` is invoked a
        cache key will be generated and used to fetch the value from the cache before the decorated method
        executes. If a value is found in the cache it is returned and the
        decorated method is never executed. If no value is found the
        decorated method is invoked and the returned value is stored in the cache
        with the generated key.

        ``None`` return values are not cached

        The cache operation takes place after the invocation of the decorated function. Any exceptions
        raised will will prevent operation from being executed;

        To always invoke the annotated method and still cache the result set
        ``skip_get`` to ``True``. This will disable the pre-invocation cache check.

        Example of caching the User object with a key generated from the
        ``str`` and ``bool`` parameters.

        .. code::

            @slycache.cache_result(keys="{username}_{is_active}")
            def get_user(username: str, is_active: bool) -> User:
                ...

        Args:
            keys (Union[str, List[str]]): key template or list of key templates. These are converted
                to actual cache keys using the currently active key generator. See :ref:`key-generator`
            cache_name (str, optional): If set this overrides the currently configured cache for this specific
                operation.
            timeout (int, optional): If set this overrides the currently configured timeout for this specific
                operation.
            skip_get (bool, optional): If set to true the pre-invocation is
                skipped and the decorated method is always executed with the returned value
                being cached as normal. This is useful for create or update methods which
                should always be executed and have their returned value placed in the cache.

                Defaults to False.
        """
        if isinstance(keys, str):
            keys = [keys]
        invocation = CacheResult(keys, cache_name, timeout, skip_get)
        return self.caching(func, result=[invocation])

    def cache_put(
        self,
        func: Optional[Callable] = None,
        *,
        keys: Union[str, List[str]],
        cache_value: Optional[str] = None,
        cache_name: Optional[str] = None,
        timeout: Union[int, NotSet] = NOTSET
    ):
        """
        This is a function level decorator used to mark function where one of the function arguments
        should be stored in the cache. One parameter must be selected using the ``cache_value`` argument.

        If the function only has a single argument (excluding ``self``) then the ``cache_value`` argument
        may be omitted.

        When a function decorated with ``cache_put`` is invoked a
        cache key will be generated and used to store the value selected from the
        function arguments.

        ``None`` values are not cached

        The cache operation takes place after the invocation of the decorated function. Any exceptions
        raised will will prevent operation from being executed;

        Example of caching the User object:

        .. code::

            @slycache.cache_put(keys="{user.username}")
            def save_user(user: User):
                ...

        Args:
            keys (Union[str, List[str]]): key template or list of key templates. These are converted
                to actual cache keys using the currently active key generator. See :ref:`key-generator`
            cache_value (str, optional): The name of the function argument to cache. This may only be omitted
                if the function only has a single argument (excluding ``self``).
            cache_name (str, optional): If set this overrides the currently configured cache for this specific
                operation.
            timeout (int, optional): If set this overrides the currently configured timeout for this specific
                operation.
        """
        if isinstance(keys, str):
            keys = [keys]
        invocation = CachePut(keys, cache_name=cache_name, cache_value=cache_value, timeout=timeout)
        return self.caching(func, put=[invocation])

    def cache_remove(self, func=None, *, keys: Union[str, List[str]], cache_name: Optional[str] = None):
        """
        This is a function level decorator used to mark function where the invocation results
        in an entry (or entries) being removed from the specified cache.

        When a function decorated with ``cache_remove`` is invoked a
        cache key will be generated by the :ref:`key-generator` ``CacheInterface.delete`` will
        be invoked on the specified cache.

        The cache operation takes place after the invocation of the decorated function. Any exceptions
        raised will will prevent operation from being executed;

        Example of removing the User object from the cache:

        .. code::

            @slycache.cache_remove(keys=["{user.username}", "{user.id}"])
            def delete_user(user: User):
                ...

        Args:
            keys (Union[str, List[str]]): key template or list of key templates. These are converted
                to actual cache keys using the currently active key generator. See :ref:`key-generator`
            cache_name (str, optional): If set this overrides the currently configured cache for this specific
                operation.
        """
        if isinstance(keys, str):
            keys = [keys]
        invocation = CacheRemove(keys, cache_name=cache_name)
        return self.caching(func, remove=[invocation])

    def caching(
        self,
        func: Optional[Callable] = None,
        *,
        result: Optional[List[CacheResult]] = None,
        put: Optional[List[CachePut]] = None,
        remove: Optional[List[CacheRemove]] = None
    ):
        """
        A function level decorator used to execute multiple cache operations
        after the execution of the decorated function.

        When a function decorated with ``caching`` is invoked each of the supplied cache operations
        will be executed **in order**.

        The cache operations are executed after the invocation of the decorated function. Any exceptions
        raised will will prevent all of the operations from being executed;

        Example of caching the User object in multiple caches:

        .. code::

            @slycache.caching(result=[
                CacheResult(keys="{username}", cache_name="local_memory"),
                CacheResult(keys="{username}", cache_name="redis"),
            ])
            def get_user(username: str):
                ...

        Args:
            result (:obj:`list` of :class:`CacheResult`, optional): ``cache_result`` operations to execute.
                See :meth:`slycache.Slycache.cache_result`
            put (:obj:`list` of :class:`CachPut`, optional): ``cache_put`` operations to execute
                See :meth:`slycache.Slycache.cache_put`
            remove (:obj:`list` of :class:`CachRemove`, optional): ``cache_remove`` operations to execute
                See :meth:`slycache.Slycache.cache_remove`
        """

        actions = [
            action_class(invocation) for invocations, action_class in (
                (result, CacheResultAction),
                (put, CachePutAction),
                (remove, CacheRemoveAction),
            ) if invocations for invocation in invocations
        ]
        return self._call(func, actions)

    def _call(self, func: Optional[Callable], actions: List[CacheAction]) -> Callable:
        self.validate()

        def _decorator(func):
            if not callable(func):
                raise SlycacheException(f"Decorator must be used on a function: {func!r}")

            action = CombinedAction(func, actions, self._key_formatter, self._cache_proxy)
            action.validate()

            @wraps(func)
            def _inner(*args, **kwargs):
                callargs = inspect.signature(func).bind(*args, **kwargs).arguments

                result = action.get_cached(callargs, default=Ellipsis)
                if result is not Ellipsis:
                    return result

                result = func(*args, **kwargs)
                action.call(result, callargs)
                return result

            return _inner

        return _decorator if func is None else _decorator(func)


slycache = Slycache()
