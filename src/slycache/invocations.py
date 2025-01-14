from dataclasses import dataclass, replace
from typing import TYPE_CHECKING, List, Optional, Union

from slycache.const import NOTSET, NotSet

if TYPE_CHECKING:
    # pylint: disable=unused-import
    from .slycache import ProxyWithDefaults


@dataclass(frozen=True)
class CacheInvocation:
    """Base invocation class.

    Invocations classes are used to store the parameters for
    cache actions. Each invocation type has a corresponding action type.

    See also:
        :meth:slycache.cations.CacheAction
    """
    keys: List[str]
    cache_name: Optional[str] = None
    namespace: Union[int, NotSet] = NOTSET

    def get_updated_proxy(self, proxy: "ProxyWithDefaults") -> "ProxyWithDefaults":
        overrides = self._get_overrides()
        if overrides:
            return replace(proxy, **overrides)
        return proxy

    def _get_overrides(self) -> dict:
        overrides = {}
        if self.cache_name:
            overrides["cache_name"] = self.cache_name
        if self.namespace is not NOTSET:
            overrides["namespace"] = self.namespace
        return overrides


@dataclass(frozen=True)
class CacheResult(CacheInvocation):
    """
    Data class used to contain the parameters for a ``cache_result`` operation.

    See also:
        :meth:`slycache.cache_result`
    """
    timeout: Union[int, NotSet] = NOTSET
    skip_get: bool = False

    def _get_overrides(self) -> dict:
        overrides = super()._get_overrides()
        if self.timeout is not NOTSET:
            overrides["timeout"] = self.timeout
        return overrides


@dataclass(frozen=True)
class CachePut(CacheInvocation):
    """
    Data class used to contain the parameters for a ``cache_put`` operation.

    See also:
        :meth:`slycache.cache_put`
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
        :meth:`slycache.cache_remove`
    """

    @property
    def skip_get(self):
        return True
