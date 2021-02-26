"""Main module"""
import inspect
import logging
from dataclasses import dataclass, replace
from functools import wraps
from typing import Any, Callable, List, Optional, Union

from .actions import (ActionExecutor, CacheAction, CachePutAction,
                      CacheRemoveAction, CacheResultAction)
from .const import DEFAULT_CACHE_NAME, NOTSET, NotSet
from .exceptions import InvalidCacheError, SlycacheException
from .interface import CacheInterface
from .invocations import CachePut, CacheRemove, CacheResult
from .key_generator import StringFormatKeyGenerator

log = logging.getLogger("slycache")


@dataclass(frozen=True)
class ProxyWithDefaults:
    """Proxy class that holds defaults for caching.
    This class keeps a reference to the cache provider
    via the cache name.
    """
    cache_name: str
    timeout: Union[int, NotSet] = NOTSET
    namespace: Union[str, NotSet] = NOTSET
    _merged: bool = False

    @property
    def key_namespace(self):
        return None if self.namespace is NOTSET else self.namespace

    def merge_with_global_defaults(self):
        if self._merged:
            return self

        defaults = caches.get_default_proxy(self.cache_name)
        updates = {"_merged": True}
        if self.timeout is NOTSET:
            updates["timeout"] = defaults.timeout
        if self.namespace is NOTSET:
            updates["namespace"] = defaults.namespace

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
        backend: CacheInterface,
        default_timeout: int = None,
        default_namespace: Union[str, NotSet] = NOTSET
    ):
        if name in self._caches:
            raise InvalidCacheError(f"Cache '{name}' is already registered")
        self.replace(name, backend, default_timeout, default_namespace)

    def replace(
        self,
        name: str,
        backend: CacheInterface,
        default_timeout: int = None,
        default_namespace: Union[str, NotSet] = NOTSET
    ):
        self._caches[name] = backend
        self._proxies[name] = ProxyWithDefaults(
            name, timeout=default_timeout, namespace=default_namespace, _merged=True
        )

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


KeysType = Union[str, List[str]]


class Slycache:

    def __init__(self, proxy: ProxyWithDefaults = None, key_generator=None):
        self._proxy = proxy
        self._key_generator = key_generator or StringFormatKeyGenerator
        self._merged = not self._proxy

    @staticmethod
    def register_backend(
        name: str,
        backend: CacheInterface,
        default_timeout: Optional[int] = None,
        default_namespace: Optional[Union[str, NotSet]] = NOTSET
    ):
        """Register a cache backend.

        Arguments:
            name: (str): the name of the cache
            backend: (:obj:`slycache.interface.CacheInterface`): An instance of the backend class.
                This must conform to the interface defined by :class:`slycache.interface.CacheInterface`
            default_timeout: (int, optional): the default timeout for this backend (seconds). Defaults to no timeout.
            default_namespace: (str, optional): the default namespace for this backend. Defaults to None.
                See :ref:`namespaces`
        """
        caches.register(name, backend, default_timeout, default_namespace)

    def with_defaults(self, **defaults):
        """Return a new Slycache object with updated defaults.

        Arguments:
            cache_name: (str, optional): name of the cache to use
            key_generator: (KeyGenerator, optional): :class:`slycache.KeyGenerator` object to use for generating
                and validating keys.
            timeout: (int, optional): default timeout to use for keys
            namespace: (str, optional): key namespace to use
        """
        cache_name = defaults.pop("cache_name", None)
        key_generator = defaults.pop("key_generator", self._key_generator)
        if not cache_name and self._proxy:
            new_proxy = replace(self._proxy, **defaults)
        else:
            new_proxy = ProxyWithDefaults(cache_name or DEFAULT_CACHE_NAME, **defaults)

        return Slycache(new_proxy, key_generator)

    def cache_result(
        self,
        keys: KeysType,
        *,
        cache_name: Optional[str] = None,
        timeout: Union[int, NotSet] = NOTSET,
        namespace: Union[str, NotSet] = NOTSET,
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

            @slycache.cache_result("{username}_{is_active}")
            def get_user(username: str, is_active: bool) -> User:
                ...

        Args:
            keys (str or List[str]): key template or list of key templates. These are converted
                to actual cache keys using the currently active key generator. See :ref:`key-generator`
            cache_name (str, optional): If set this overrides the currently configured cache for this specific
                operation.
            timeout (int, optional): If set this overrides the currently configured timeout for this specific
                operation.
            namespace (str, optional): If set this overrides the currently configured namespace for this specific
                operation.
            skip_get (bool, optional): If set to true the pre-invocation is
                skipped and the decorated method is always executed with the returned value
                being cached as normal. This is useful for create or update methods which
                should always be executed and have their returned value placed in the cache.

                Defaults to False.
        """
        if isinstance(keys, str):
            keys = [keys]
        invocation = CacheResult(keys, cache_name, namespace, timeout, skip_get)
        return self.caching(result=[invocation])

    def cache_put(
        self,
        keys: KeysType,
        *,
        cache_value: Optional[str] = None,
        cache_name: Optional[str] = None,
        timeout: Union[int, NotSet] = NOTSET,
        namespace: Union[str, NotSet] = NOTSET
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

            @slycache.cache_put("{user.username}")
            def save_user(user: User):
                ...

        Args:
            keys (str or List[str]): key template or list of key templates. These are converted
                to actual cache keys using the currently active key generator. See :ref:`key-generator`
            cache_value (str, optional): The name of the function argument to cache. This may only be omitted
                if the function only has a single argument (excluding ``self``).
            cache_name (str, optional): If set this overrides the currently configured cache for this specific
                operation.
            timeout (int, optional): If set this overrides the currently configured timeout for this specific
                operation.
            namespace (str, optional): If set this overrides the currently configured namespace for this specific
                operation.
        """
        if isinstance(keys, str):
            keys = [keys]
        invocation = CachePut(keys, cache_name, namespace, cache_value, timeout)
        return self.caching(put=[invocation])

    def cache_remove(
        self,
        keys: KeysType,
        *,
        cache_name: Optional[str] = None,
        namespace: Union[str, NotSet] = NOTSET,
    ):
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

            @slycache.cache_remove(["{user.username}", "{user.id}"])
            def delete_user(user: User):
                ...

        Args:
            keys (str or List[str]): key template or list of key templates. These are converted
                to actual cache keys using the currently active key generator. See :ref:`key-generator`
            cache_name (str, optional): If set this overrides the currently configured cache for this specific
                operation.
            namespace (str, optional): If set this overrides the currently configured namespace for this specific
                operation.
        """
        if isinstance(keys, str):
            keys = [keys]
        invocation = CacheRemove(keys, cache_name, namespace)
        return self.caching(remove=[invocation])

    def caching(
        self,
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
                CacheResult("{username}", cache_name="local_memory"),
                CacheResult("{username}", cache_name="redis"),
            ])
            def get_user(username: str):
                ...

        Args:
            result (:obj:`list` of :class:`slycache.CacheResult`, optional): ``cache_result`` operations to execute.
            put (:obj:`list` of :class:`slycache.CachePut`, optional): ``cache_put`` operations to execute
            remove (:obj:`list` of :class:`slycache.CacheRemove`, optional): ``cache_remove`` operations to execute
        """

        actions = [
            action_class(invocation) for invocations, action_class in (
                (result, CacheResultAction),
                (put, CachePutAction),
                (remove, CacheRemoveAction),
            ) if invocations for invocation in invocations
        ]
        return self._call(actions)

    def _call(self, actions: List[CacheAction]) -> Callable:
        self.validate()

        def _decorator(func):
            if not callable(func):
                raise SlycacheException(f"Decorator must be used on a function: {func!r}")

            action = ActionExecutor(func, actions, self._key_generator, self._cache_proxy)
            action.validate()

            @wraps(func)
            def _inner(*args, **kwargs):
                call_args = inspect.signature(func).bind(*args, **kwargs).arguments

                result = action.get_cached(call_args)
                if result is not NOTSET:
                    return result

                result = func(*args, **kwargs)
                action.call(result, call_args)
                return result

            def _clear(*args, **kwargs):
                call_args = inspect.signature(func).bind(*args, **kwargs).arguments
                action.clear_cache(call_args)

            _inner.clear_cache = _clear
            return _inner

        return _decorator

    def validate(self):
        self._cache_proxy.validate()

    @property
    def _cache_proxy(self):
        """Lazy initializer for proxy"""
        if not self._proxy:
            self._proxy = caches.get_default_proxy(DEFAULT_CACHE_NAME)

        return self._proxy.merge_with_global_defaults()


caches = CacheHolder()
slycache = Slycache()
