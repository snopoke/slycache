import logging
from abc import ABCMeta, abstractmethod
from functools import cached_property
from typing import TYPE_CHECKING, Any, Callable, Dict, List, Optional

from .exceptions import SlycacheException
from .invocations import CacheInvocation

if TYPE_CHECKING:
    # pylint: disable=unused-import
    from .slycache import ProxyWithDefaults

log = logging.getLogger("slycache")


class CacheAction(metaclass=ABCMeta):

    def __init__(self, invocation: CacheInvocation):
        self.invocation = invocation
        self._proxy = None
        self._formatted_keys = None

    @property
    def proxy(self) -> "ProxyWithDefaults":
        if not self._proxy:
            raise SlycacheException("proxy not set on action")
        return self._proxy

    def set_proxy(self, proxy: "ProxyWithDefaults"):
        self._proxy = self.invocation.get_updated_proxy(proxy)

    @property
    def formatted_keys(self) -> Optional[List[str]]:
        return self._formatted_keys

    @formatted_keys.setter
    def formatted_keys(self, keys: List[str]):
        self._formatted_keys = keys

    def call(self, cache_key: str, func: Callable, callargs: Dict, result: Any):
        self._call(cache_key, func, callargs, result)

    @abstractmethod
    def _call(self, cache_key: str, func: Callable, callargs: Dict, result: Any):
        raise NotImplementedError


class CacheResultAction(CacheAction):

    def _call(self, cache_key: str, func: Callable, callargs: Dict, result: Any):
        value = self._get_value(func, callargs, result)
        if value is None:
            log.debug(
                "ignoring None value, cache=%s, function=%s, key=%s", self.proxy.cache_name, func.__name__,
                cache_key
            )
            return

        self.proxy.set(cache_key, value)
        log.debug("cache_set: cache=%s, function=%s, key=%s", self.proxy.cache_name, func.__name__, cache_key)

    def _get_value(  # pylint: disable=no-self-use
        self, func: Callable, callargs: Dict, result: Any  # pylint: disable=unused-argument
    ) -> Any:
        return result


class CachePutAction(CacheResultAction):

    def _get_value(self, func: Callable, callargs: Dict, result: Any) -> Any:
        if self.invocation.cache_value is not None:
            return callargs[self.invocation.cache_value]

        args = list(callargs)
        if len(args) == 1:
            return callargs[args[0]]
        if len(args) == 2 and args[0] == "self":
            return callargs[args[1]]
        raise SlycacheException("'cache_value' must be provided for functions with multiple arguments")


class CacheRemoveAction(CacheAction):

    def _call(self, cache_key: str, func: Callable, callargs: Dict, result: Any):
        log.debug("cache_remove: cache=%s, function=%s, key=%s", self.proxy.cache_name, func.__name__, cache_key)
        self.proxy.delete(cache_key)


class CombinedAction:

    def __init__(self, func: Callable, actions: List[CacheAction], key_formatter, proxy: "ProxyWithDefaults"):
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
                self._key_formatter.generate(action.proxy.key_prefix, key, self._func, callargs)
                for key in action.invocation.keys
            ]
            action.formatted_keys = keys
        return action.formatted_keys

    def call(self, result, callargs):
        for action in self._actions:
            for key in self.get_action_keys(action, callargs):
                action.call(key, self._func, callargs, result)
