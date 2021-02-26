import logging
import sys
from abc import ABCMeta, abstractmethod
from typing import (TYPE_CHECKING, Any, Callable, Dict, List, Optional,
                    TypeVar, Union)

from .const import NOTSET, NotSet
from .exceptions import SlycacheException
from .invocations import CacheInvocation


if TYPE_CHECKING:
    # pylint: disable=unused-import
    from .slycache import ProxyWithDefaults

log = logging.getLogger("slycache")

Invocation = TypeVar("Invocation", bound=CacheInvocation)


class CacheAction(metaclass=ABCMeta):
    """Base class for actions"""

    def __init__(self, invocation: Invocation):
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

    @abstractmethod
    def call(self, cache_key: str, func: Callable, call_args: Dict, result: Any):
        """Override in subclasses to perform the appropriate action"""
        raise NotImplementedError


class CacheResultAction(CacheAction):
    """Action for ``CacheResult``

    See also:
        :meth:`slycache.cache_result`
    """

    def call(self, cache_key: str, func: Callable, call_args: Dict, result: Any):
        value = self._get_value(call_args, result)
        if value is None:
            log.debug(
                "ignoring None value, cache=%s, function=%s, key=%s", self.proxy.cache_name, func.__name__,
                cache_key
            )
            return

        self.proxy.set(cache_key, value)
        log.debug("cache_set: cache=%s, function=%s, key=%s", self.proxy.cache_name, func.__name__, cache_key)

    def _get_value(  # pylint: disable=no-self-use
        self, call_args: Dict, result: Any  # pylint: disable=unused-argument
    ) -> Any:
        return result


class CachePutAction(CacheResultAction):
    """Action for ``CachePut``

        See also:
            :meth:`slycache.cache_put`
        """

    def _get_value(self, call_args: Dict, result: Any) -> Any:
        if self.invocation.cache_value is not None:
            return call_args[self.invocation.cache_value]

        args = list(call_args)
        if len(args) == 1:
            return call_args[args[0]]
        if len(args) == 2 and args[0] == "self":
            return call_args[args[1]]
        raise SlycacheException("'cache_value' must be provided for functions with multiple arguments")


class CacheRemoveAction(CacheAction):
    """Action for ``CacheRemove``

        See also:
            :meth:`slycache.cache_remove`
        """

    def call(self, cache_key: str, func: Callable, call_args: Dict, result: Any):
        log.debug("cache_remove: cache=%s, function=%s, key=%s", self.proxy.cache_name, func.__name__, cache_key)
        self.proxy.delete(cache_key)


class ActionExecutor:
    """Class responsible for executing cache actions based on the function
    and call arguments they have been decorated on.
    """

    def __init__(self, func: Callable, actions: List[CacheAction], key_generator, proxy: "ProxyWithDefaults"):
        self._func = func
        self._actions = actions
        self._key_generator = key_generator
        self._skip_get_ = None

        for action in self._actions:
            action.set_proxy(proxy)

    def validate(self):
        """Validate actions and key templates"""
        self._skip_get  # noqa, pylint: disable=pointless-statement
        for action in self._actions:
            for key in action.invocation.keys:
                self._key_generator.validate(key, self._func)

    @property
    def _skip_get(self):
        if self._skip_get_ is None:
            skip_get = {action.invocation.skip_get for action in self._actions}
            if len(skip_get) > 1:
                raise SlycacheException("All actions agree on 'skip_get'")
            self._skip_get_ = list(skip_get)[0]
        return self._skip_get_

    def get_cached(self, call_args) -> Union[Any, NotSet]:
        """Iteratively check the action caches with each key
        until a cached entry is found or all actions & keys are exhausted.

        If all actions have ``skip_get=True``, ``NOTSET`` is always returned and the caches
        are not checked.

        Returns:
            [Any, NotSet]: cached value if found or ``NOTSET`` if no value is found
                           or all actions have ``skip_get=True``
        """
        if self._skip_get:
            return NOTSET

        for action in self._actions:
            for key in self._get_action_keys(action, call_args):
                result = action.proxy.get(key, default=NOTSET)
                if result is not NOTSET:
                    log.debug(
                        "cache hit: cache=%s key=%s function=%s", action.proxy.cache_name, key, self._func.__name__
                    )
                    return result
                log.debug(
                    "cache miss: cache=%s key=%s function=%s", action.proxy.cache_name, key, self._func.__name__
                )
        return NOTSET

    def _get_action_keys(self, action: CacheAction, call_args):
        if not action.formatted_keys:
            keys = [
                self._key_generator.generate(action.proxy.key_namespace, key, self._func, call_args)
                for key in action.invocation.keys
            ]
            action.formatted_keys = keys
        return action.formatted_keys

    def call(self, result: Optional[Any], call_args: Dict):
        """Execute the actions

        Arguments:
            result: The result returned from the invocation of the decorated function
            call_args: Dict of arguments from the invocation of the decorated function
        """
        for action in self._actions:
            for key in self._get_action_keys(action, call_args):
                action.call(key, self._func, call_args, result)

    def clear_cache(self, call_args: Dict):
        """Helper to clear the cache for a decorated function"""
        for action in self._actions:
            remove_action = CacheRemoveAction(action.invocation)
            remove_action.set_proxy(action.proxy)
            for key in self._get_action_keys(remove_action, call_args):
                remove_action.call(key, self._func, call_args, None)
