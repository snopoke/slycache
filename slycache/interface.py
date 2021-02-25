import sys
from typing import Any, Callable, Dict, Optional

_native_protocol = sys.version_info[:2] >= (3, 8)
if _native_protocol:
    from typing import Protocol
else:
    class Protocol:
        pass


class CacheInterface(Protocol):
    """Protocol class for the cache interface required by Slycache"""

    def get(self, key: str, default: Optional[Any] = None) -> Any:
        """Get a value from the cache and return it or else the default value.

        Arguments:
            key: the cache key
            default: value to return if no value found in the cache

        Returns:
            any: the cache value or ``default``
        """
        raise NotImplementedError

    def set(self, key: str, value: Any, timeout: Optional[int] = None):
        """Set a value in the cache with the given key and timeout.

        Arguments:
            key: the cache key
            value: the cache value
            timeout: cache item timeout in seconds or None
        """
        raise NotImplementedError

    def delete(self, key: str):
        """Delete value from cache.

        Arguments:
            key: the key to delete
        """
        raise NotImplementedError


class KeyGenerator(Protocol):
    """Protocol for a key generator class."""

    @staticmethod
    def validate(template: str, func: Callable):
        """Validate a key template.

        Arguments:
            template: key template
            func: the decorated function

        Raises:
            ValueError: if the template is not validated
        """
        raise NotImplementedError

    @staticmethod
    def generate(namespace: Optional[str], template: str, func: Callable, call_args: Dict) -> str:
        """Generate a key for use in a cache operation.

        Arguments:
            namespace: the namespace to suffix the key with
            template: the key template
            func: the decorated function
            call_args: dictionary of arguments that were used in the function invocation

        Returns:
            str: The generated key
        """
